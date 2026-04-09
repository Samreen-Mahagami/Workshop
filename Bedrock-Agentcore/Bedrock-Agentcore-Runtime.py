import boto3

# Create client
client = boto3.client(
    "bedrock-agent-runtime",
    region_name="us-east-1"   # change if your agent is in another region
)

# Replace with your values
AGENT_ID = "LAMMK434UM"
AGENT_ALIAS_ID = "QAAILV9CXL"
SESSION_ID = "my-session-1"

# Call agent
response = client.invoke_agent(
    agentId=AGENT_ID,
    agentAliasId=AGENT_ALIAS_ID,
    sessionId=SESSION_ID,
    inputText="Explain Ec2 Server launching steps"
)

# Print output
for event in response["completion"]:
    if "chunk" in event:
        print(event["chunk"]["bytes"].decode(), end="")
