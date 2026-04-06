import boto3

# Create Polly client
polly = boto3.client('polly', region_name='us-east-1')

# Text to convert
text = "Hello Samreen, this is a aws polly service that converts text into natural-sounding speech using AI voices."

# Call Polly
response = polly.synthesize_speech(
    Text=text,
    OutputFormat='mp3',
    VoiceId='Joanna'   # Try different voices
)

# Save audio file
with open("output.mp3", "wb") as file:
    file.write(response['AudioStream'].read())

print("Audio file generated: output.mp3")
