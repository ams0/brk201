from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition, MCPTool, Tool
)
from dotenv import load_dotenv
import os
load_dotenv()

project_client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
mcp_tool = MCPTool(
    server_label="kb-zava-knowledge-base-94obi",
    server_url="https://fsunavala-srch-demos-prod.search.windows.net/knowledgebases/zava-knowledge-base/mcp?api-version=2025-11-01-Preview",
    require_approval="never",
    project_connection_id="kb-zava-knowledge-base-94obi"
)

instructions = """You are a support agent that answers custom questions about our products.

Always use the knowledge MCP tool to answer user questions about products.
Always speak in a professional tone. 
Always refer to the user by name if provided."""

# Create tools list with proper typing for the agent definition
tools: list[Tool] = [mcp_tool]

with project_client:
    # Create a prompt agent with MCP tool capabilities
    # The agent will be able to access external GitHub repositories through the MCP protocol
    agent = project_client.agents.create_version(
        agent_name="BasicSupportAgent",
        definition=PromptAgentDefinition(
            model="gpt-4.1",
            instructions=instructions,
            tools=tools,
        ),
    )
    print(f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})")
