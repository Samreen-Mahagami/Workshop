import boto3
import json

# Create Bedrock client
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

# Prompt
prompt = "generate python code for aws translate service"

# Request body (for Claude model)
body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 500,
    "messages": [
        {
            "role": "user",
            "content": prompt
        }
    ]
}

# Invoke model
response = bedrock.invoke_model(
    modelId="anthropic.claude-3-haiku-20240307-v1:0",
    body=json.dumps(body)
)

# Read response
result = json.loads(response["body"].read())

# Print output
print(result["content"][0]["text"])
