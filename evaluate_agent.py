import os
import json
import time
from pprint import pprint
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential
from openai.types.responses.response_input_param import FunctionCallOutput, ResponseInputParam
from openai.types.eval_create_params import DataSourceConfigCustom

load_dotenv()


credential = DefaultAzureCredential()

project_client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

agent_name = "BasicSupportAgent"

openai_client = project_client.get_openai_client()

conversation = openai_client.conversations.create()
response = openai_client.responses.create(
    conversation=conversation.id,
    input="Can you tell me about Zava's branding guidelines?",
    extra_body={"agent": {"name": agent_name, "type": "agent_reference"}},
)
print(f"Response output: {response.output_text} (id: {response.id})")

# Now create evaluation for the response
data_source_config = {"type": "azure_ai_source", "scenario": "responses"}
data_source_config = DataSourceConfigCustom(
    type="custom",
    item_schema={
        "type": "object", 
        "properties": {
            "query": {"type": "string"}
        }, 
        "required": ["query"]
    },
    include_sample_schema=True,
)

# Define data source for evaluation run
data_source = {
    "type": "azure_ai_target_completions",
    "source": {
        "type": "file_content",
        "content": [
            {"item": {"query": "Tell me about Zava's branding guidelines?"}},
            {"item": {"query": "What colors do Zava's shirts come in"}},
        ],
    },
    "input_messages": {
        "type": "template",
        "template": [
            {"type": "message", "role": "user", "content": {"type": "input_text", "text": "{{item.query}}"}}
        ],
    },
    "target": {
        "type": "azure_ai_agent",
        "name": agent_name,
        #"version": agent.version,  # Version is optional. Defaults to latest version if not specified
    },
}

model = "gpt-4.1"
# add your desired evaluators here
testing_criteria = [
    {
        "type": "azure_ai_evaluator", 
        "name": "task_adherence", 
        "evaluator_name": "builtin.task_adherence",
        "initialization_parameters": {"deployment_name": f"{model}"},
    },
    {
        "type": "azure_ai_evaluator", 
        "name": "groundedness", 
        "evaluator_name": "builtin.groundedness",
        "initialization_parameters": {"deployment_name": f"{model}"},
    }
]

eval_object = openai_client.evals.create(
    name="Agent Response Evaluation",
    data_source_config=data_source_config,
    testing_criteria=testing_criteria,
)
print(f"Evaluation created (id: {eval_object.id}, name: {eval_object.name})")

data_source = {
    "type": "azure_ai_responses",
    "item_generation_params": {
        "type": "response_retrieval",
        "data_mapping": {"response_id": "{{item.resp_id}}"},
        "source": {
            "type": "file_content",
            "content": [{
                "item": { "resp_id": response.id }
            }]
        },
    },
}

response_eval_run = openai_client.evals.runs.create(
    eval_id=eval_object.id, 
    name=f"Evaluation Run for Agent {agent_name}", 
    data_source=data_source
)
print(f"Evaluation run created (id: {response_eval_run.id})")

while response_eval_run.status not in ["completed", "failed"]:
    response_eval_run = openai_client.evals.runs.retrieve(
        run_id=response_eval_run.id, 
        eval_id=eval_object.id
    )
    print(f"Waiting for eval run to complete... current status: {response_eval_run.status}")
    time.sleep(5)

if response_eval_run.status == "completed":
    print("\n✓ Evaluation run completed successfully!")
    print(f"Result Counts: {response_eval_run.result_counts}")
    print(f"Eval Run Report URL: {response_eval_run.report_url}")
    output_items = list(
        openai_client.evals.runs.output_items.list(run_id=response_eval_run.id, eval_id=eval_object.id)
    )
    print(f"\nOUTPUT ITEMS (Total: {len(output_items)})")
    print(f"{'-'*60}")
    pprint(output_items)
    print(f"{'-'*60}")
else:
    print("\n✗ Evaluation run failed.")