from crewai import Agent, Task, Crew
from crewai.llm import LLM
import asyncio
import aiohttp
from typing import Dict, Any, List
from config import Config

class UpdatedCrewAIConnector:
    def __init__(self):
        if not Config.validate():
            raise ValueError("Missing required Azure OpenAI configuration")
        
        # Initialize Azure OpenAI LLM for CrewAI
        self.llm = LLM(
            model=f"azure/{Config.AZURE_OPENAI_DEPLOYMENT_NAME}",
            api_key=Config.AZURE_OPENAI_API_KEY,
            base_url=Config.AZURE_OPENAI_ENDPOINT,
            api_version=Config.AZURE_OPENAI_API_VERSION
        )
        
        # MCP server configuration
        self.mcp_base_url = f"http://{Config.MCP_SERVER_HOST}:{Config.MCP_SERVER_PORT}"
        
        # Initialize agents
        self.agents = self._create_agents()
    
    def _create_agents(self) -> Dict[str, Agent]:
        """Create CrewAI agents with Azure OpenAI LLM."""
        return {
            "researcher": Agent(
                role='Senior Research Analyst',
                goal='Uncover cutting-edge developments in AI and data science',
                backstory="You're a seasoned researcher with expertise in AI and data analysis.",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            ),
            "writer": Agent(
                role='Tech Content Strategist',
                goal='Craft compelling content on tech advancements',
                backstory="You're a skilled writer with a passion for technology and innovation.",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            ),
            "reviewer": Agent(
                role='Content Review Expert',
                goal='Review and improve content quality',
                backstory="You're an expert reviewer ensuring high-quality deliverables.",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
        }
    
    async def send_mcp_request(self, method: str, params: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Send request to MCP server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.mcp_base_url}/mcp",
                    json={"method": method, "params": params},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"MCP request failed: {response.status} - {error_text}")
        except Exception as e:
            raise Exception(f"Failed to send MCP request: {str(e)}")
    
    async def list_mcp_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools."""
        response = await self.send_mcp_request("list_tools")
        
        if response.get("success"):
            return response.get("data", [])
        else:
            raise Exception(f"Failed to list MCP tools: {response.get('error')}")
    
    async def execute_crew_with_mcp(self, task_description: str, agent_role: str = "researcher") -> Dict[str, Any]:
        """Execute a CrewAI task and report to MCP."""
        try:
            # Validate agent role
            if agent_role not in self.agents:
                raise ValueError(f"Unknown agent role: {agent_role}")
            
            # Create and execute CrewAI task
            task = Task(
                description=task_description,
                agent=self.agents[agent_role],
                expected_output="A comprehensive analysis with key findings"
            )
            
            crew = Crew(
                agents=[self.agents[agent_role]],
                tasks=[task],
                verbose=True
            )
            
            # Execute the crew task
            result = crew.kickoff()
            
            # Report to MCP server
            mcp_response = await self.send_mcp_request(
                "call_tool",
                {
                    "name": "execute_crew_task",
                    "arguments": {
                        "task_description": task_description,
                        "agent_role": agent_role
                    }
                }
            )
            
            return {
                "status": "success",
                "crew_result": str(result),
                "mcp_response": mcp_response
            }
        
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def get_crew_status_from_mcp(self, crew_id: str = "default") -> Dict[str, Any]:
        """Get crew status from MCP server."""
        response = await self.send_mcp_request(
            "call_tool",
            {
                "name": "get_crew_status",
                "arguments": {"crew_id": crew_id}
            }
        )
        return response