import boto3
import time
import uuid
import json
import urllib.request

transcribe = boto3.client('transcribe', region_name='us-east-1')

# Unique job name
job_name = "job-" + str(uuid.uuid4())

job_uri = "s3://transcribe-demo-v2/diabetes_converted.wav"

# Start transcription job
transcribe.start_transcription_job(
    TranscriptionJobName=job_name,
    Media={'MediaFileUri': job_uri},
    MediaFormat='mp3',
    LanguageCode='en-US'
)

print("Started job:", job_name)

# Wait for completion
while True:
    status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    job_status = status['TranscriptionJob']['TranscriptionJobStatus']

    if job_status in ['COMPLETED', 'FAILED']:
        print("Job Status:", job_status)
        break

    print("Waiting...")
    time.sleep(5)

# Save output in SAME DIRECTORY
if job_status == 'COMPLETED':
    transcript_url = status['TranscriptionJob']['Transcript']['TranscriptFileUri']

    # Fetch JSON result
    with urllib.request.urlopen(transcript_url) as response:
        data = json.loads(response.read())

    # Extract text
    text_output = data['results']['transcripts'][0]['transcript']

    # Save in current directory
    file_name = "transcription_output.txt"

    with open(file_name, "w") as f:
        f.write(text_output)

    print(f"✅ Output saved in current directory as: {file_name}")
