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
    input="What are HR policies?",
    extra_body={"agent": {
        "name": agent_name, 
        "version":"24", 
        "type": "agent_reference"
    }},
)
print(f"Response output: {response.output_text} (id: {response.id})")

# Configure evaluation parameters
model = "gpt-4.1"

data_source_config = {
    "type": "azure_ai_source", 
    "scenario": "responses"
}

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
    },
]

# Run evaluation
eval_object = openai_client.evals.create(
    name="BasicSupportAgent Evaluation",
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
                "item": { 
                    "resp_id": response.id,
                }
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
else:
    print("\n✗ Evaluation run failed.")