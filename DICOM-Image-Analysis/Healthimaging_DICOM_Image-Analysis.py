import boto3
import json
import time
import base64
import gzip
import numpy as np
from PIL import Image
import io
import pydicom

S3_BUCKET='medical-imaging-demo'
S3_INPUT_FOLDER='dicom-input/'
DATASTORE_ID='e7e6bc47d86744f69dbc25b8d0cc5b40'
AWS_REGION='us-east-1'

sts=boto3.client('sts')
s3 = boto3.client('s3')
AWS_ACCOUNT_ID = sts.get_caller_identity()['Account']
IAM_ROLE_ARN = f"arn:aws:iam::{AWS_ACCOUNT_ID}:role/HealthImagingS3Role"

healthimaging = boto3.client('medical-imaging', region_name=AWS_REGION)
bedrock = boto3.client('bedrock-runtime', region_name=AWS_REGION)

print("="*70)
print("HEALTHIMAGING CT SCAN ANALYSIS")
print("="*70)

# Check for image sets
print("\n[1/4] Checking datastore...")
image_sets = healthimaging.search_image_sets(datastoreId=DATASTORE_ID)

if not image_sets['imageSetsMetadataSummaries']:
    print("⚠ No image sets. Starting import...")
    import_response = healthimaging.start_dicom_import_job(
        datastoreId=DATASTORE_ID,
        inputS3Uri=f's3://{S3_BUCKET}/{S3_INPUT_FOLDER}',
        outputS3Uri=f's3://{S3_BUCKET}/healthimaging-output/',
        dataAccessRoleArn=IAM_ROLE_ARN
    )
    job_id = import_response['jobId']
    print(f"✓ Import started: {job_id}")

    while True:
        job = healthimaging.get_dicom_import_job(datastoreId=DATASTORE_ID, jobId=job_id)
        status = job['jobProperties']['jobStatus']
        print(f"  Status: {status}")
        if status == 'COMPLETED':
            break
        elif status == 'FAILED':
            print("✗ Failed:", job)
            exit(1)
        time.sleep(10)

    image_sets = healthimaging.search_image_sets(datastoreId=DATASTORE_ID)

image_set_id = image_sets['imageSetsMetadataSummaries'][0]['imageSetId']
print(f"✓ Image Set: {image_set_id}")

# Get metadata
print("\n[2/4] Retrieving metadata...")
metadata_response = healthimaging.get_image_set_metadata(
    datastoreId=DATASTORE_ID,
    imageSetId=image_set_id
)

compressed_data = metadata_response['imageSetMetadataBlob'].read()
decompressed_data = gzip.decompress(compressed_data)
metadata = json.loads(decompressed_data.decode('utf-8'))

study = metadata['Study']
series = study['Series'][list(study['Series'].keys())[0]]
instance = series['Instances'][list(series['Instances'].keys())[0]]
frame_id = instance['ImageFrames'][0]['ID']
print(f"✓ Frame ID: {frame_id}")

# Get original DICOM from S3 (more reliable than HealthImaging frame)
print("\n[3/4] Reading original DICOM from S3...")
objects = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_INPUT_FOLDER)
dcm_files = [obj['Key'] for obj in objects.get('Contents', []) if obj['Key'].endswith('.dcm')]

if not dcm_files:
    print("✗ No DICOM files found in S3")
    exit(1)

dcm_file = dcm_files[0]
print(f"✓ Reading: {dcm_file}")

s3_response = s3.get_object(Bucket=S3_BUCKET, Key=dcm_file)
dcm = pydicom.dcmread(io.BytesIO(s3_response['Body'].read()))

# Extract pixel data
pixel_array = dcm.pixel_array
print(f"✓ Image dimensions: {pixel_array.shape}")
print(f"✓ Pixel value range: {pixel_array.min()} to {pixel_array.max()}")

# Apply windowing for better visualization (important for CT scans)
print("\n[4/4] Converting and analyzing...")

# For CT scans, apply window/level
if hasattr(dcm, 'WindowCenter') and hasattr(dcm, 'WindowWidth'):
    window_center = float(dcm.WindowCenter[0] if isinstance(dcm.WindowCenter, list) else dcm.WindowCenter)
    window_width = float(dcm.WindowWidth[0] if isinstance(dcm.WindowWidth, list) else dcm.WindowWidth)
    print(f"  Applying window: Center={window_center}, Width={window_width}")
    
    lower = window_center - window_width / 2
    upper = window_center + window_width / 2
    pixel_array = np.clip(pixel_array, lower, upper)

# Normalize to 0-255
pixel_array = ((pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)

# Create image
img = Image.fromarray(pixel_array)

# Convert to JPEG
buffer = io.BytesIO()
img.convert('RGB').save(buffer, format='JPEG', quality=95)
image_jpeg = buffer.getvalue()
image_base64 = base64.b64encode(image_jpeg).decode('utf-8')

print("✓ Image converted to JPEG")

# Analyze with Bedrock
bedrock_response = bedrock.invoke_model(
    modelId='anthropic.claude-3-sonnet-20240229-v1:0',
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_base64}},
                {"type": "text", "text": "Analyze this CT scan. Identify: 1) Body part 2) Any abnormalities (stroke, hemorrhage, tumor) 3) Confidence level"}
            ]
        }]
    })
)

result = json.loads(bedrock_response['body'].read())

print("\n" + "="*70)
print("ANALYSIS RESULTS")
print("="*70)
print(result['content'][0]['text'])
print("="*70)
