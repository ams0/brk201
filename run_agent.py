from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

myEndpoint = "https://zava-demo.services.ai.azure.com/api/projects/zava-demo"

project_client = AIProjectClient(
    endpoint=myEndpoint,
    credential=DefaultAzureCredential(),
)

agent_name = "BasicSupportAgent"
openai_client = project_client.get_openai_client()

# ADDED: create a conversation
conversation = openai_client.conversations.create()

# Reference the agent to get a response
response = openai_client.responses.create(
    conversation=conversation.id, # ADDED: reference conversation id
    input=[{"role": "user", "content": "Tell me about HR policies"}],
    extra_body={"agent": {"name": agent_name, "type": "agent_reference"}},
    stream=True
)

# UPDATED: stream the response
for event in response:
    if event.type == "response.output_text.delta":
        print(event.delta, end='', flush=True)

print()  # Add a newline at the end


