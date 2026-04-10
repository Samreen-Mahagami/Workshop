import boto3

# Create Bedrock Agent Runtime client
client = boto3.client(
    "bedrock-agent-runtime",
    region_name="us-east-1"
)

# 🔹 Your Agent details
AGENT_ID = "IDPPQIHVKW"
ALIAS_ID = "7AN4LIIBT9"

# 🔹 SAME session → memory works
SESSION_ID = "memory-session-001"


def invoke_agent(user_input):
    response = client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=ALIAS_ID,
        sessionId=SESSION_ID,
        inputText=user_input
    )

    output_text = ""

    # Stream response
    for event in response.get("completion", []):
        if "chunk" in event:
            chunk = event["chunk"]["bytes"].decode()
            print(chunk, end="")
            output_text += chunk

    print("\n")
    return output_text


# -------------------------------
# 🧪 TEST MEMORY
# -------------------------------

print("---- Interaction 1 ----")
invoke_agent("Hi, my name is Samreen")

print("---- Interaction 2 ----")
invoke_agent("I live in Nashik")

print("---- Interaction 3 ----")
invoke_agent("What is my name and where do I live?")
