import boto3
import json
import time
import uuid

# --- CONFIGURATION ---
S3_INPUT_BUCKET = "healthscribe-input-testing" 
S3_OUTPUT_BUCKET = "healthscribe-output-testing"
IAM_ROLE_ARN = "arn:aws:iam::264268443465:role/HealthScribeServiceRole"
REGION = "us-east-1"

# Initialize Clients
transcribe = boto3.client('transcribe', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)

def get_latest_file_from_s3(bucket):
    """Automatically finds the newest file in your input bucket."""
    response = s3.list_objects_v2(Bucket=bucket)
    if 'Contents' not in response:
        return None
    
    # Sort files by the time they were uploaded
    sorted_files = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
    return sorted_files[0]['Key']

def run_healthscribe_test():
    # 1. AUTO-DETECT FILE
    file_key = get_latest_file_from_s3(S3_INPUT_BUCKET)
    
    if not file_key:
        print(f"[-] Error: No files found in {S3_INPUT_BUCKET}")
        return

    input_uri = f"s3://{S3_INPUT_BUCKET}/{file_key}"
    job_name = f"HealthScribe-{uuid.uuid4().hex[:6]}"
    
    print(f"[*] Found newest file: {file_key}")
    print(f"[*] Starting HealthScribe job: {job_name}")

    # 2. Start the Job
    transcribe.start_medical_scribe_job(
        MedicalScribeJobName=job_name,
        Media={'MediaFileUri': input_uri},
        OutputBucketName=S3_OUTPUT_BUCKET,
        DataAccessRoleArn=IAM_ROLE_ARN,
        Settings={'ShowSpeakerLabels': True, 'MaxSpeakerLabels': 2}
    )

    # 3. Poll for Completion
    print("[*] Waiting for AI to summarize...")
    clinical_doc_uri = None
    while True:
        response = transcribe.get_medical_scribe_job(MedicalScribeJobName=job_name)
        job = response.get('MedicalScribeJob', {})
        status = job.get('MedicalScribeJobStatus')
        
        if status == 'COMPLETED':
            print("[+] Job Completed!")
            clinical_doc_uri = job.get('MedicalScribeOutput', {}).get('ClinicalDocumentUri')
            break
        elif status == 'FAILED':
            print(f"[-] Job Failed: {job.get('FailureReason')}")
            return
        
        time.sleep(30)
        print("    ...processing audio...")

    # 4. Extract and Download
    path_parts = clinical_doc_uri.replace("https://", "").split("/")
    bucket_name = path_parts[1]
    key_name = "/".join(path_parts[2:])

    obj = s3.get_object(Bucket=bucket_name, Key=key_name)
    data = json.loads(obj['Body'].read().decode('utf-8'))

    # 5. Print the Report
    print("\n" + "="*60)
    print(f"       CLINICAL INSIGHTS FOR: {file_key}")
    print("="*60)

    sections = data.get('ClinicalDocumentation', {}).get('Sections', [])
    for section in sections:
        header = section.get('SectionName', '').replace('_', ' ').title()
        print(f"\n{header}")
        print("-" * len(header))
        
        for item in section.get('Summary', []):
            text = item.get('SummarizedSegment', '').strip()
            if text:
                print(f"• {text.replace('\n', '\n   ')}")

    print("\n" + "="*60)

if __name__ == "__main__":
    run_healthscribe_test()
