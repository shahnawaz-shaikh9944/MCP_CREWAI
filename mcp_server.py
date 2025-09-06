import asyncio
import json
from typing import Any, Dict, List, Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from config import Config

class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any] = {}

class MCPResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None

class SimpleMCPServer:
    def __init__(self):
        self.app = FastAPI(title="CrewAI MCP Server")
        self.tools = {
            "get_crew_status": {
                "name": "get_crew_status",
                "description": "Get the status of CrewAI agents and tasks",
                "schema": {
                    "type": "object",
                    "properties": {
                        "crew_id": {
                            "type": "string",
                            "description": "ID of the crew to check status for"
                        }
                    }
                }
            },
            "execute_crew_task": {
                "name": "execute_crew_task",
                "description": "Execute a task using CrewAI",
                "schema": {
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "Description of the task to execute"
                        },
                        "agent_role": {
                            "type": "string",
                            "description": "Role of the agent to use for the task"
                        }
                    },
                    "required": ["task_description", "agent_role"]
                }
            }
        }
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "server": "crewai-mcp-server"}
        
        @self.app.post("/mcp", response_model=MCPResponse)
        async def handle_mcp_request(request: MCPRequest):
            try:
                if request.method == "list_tools":
                    tools_list = [
                        {
                            "name": tool["name"],
                            "description": tool["description"]
                        }
                        for tool in self.tools.values()
                    ]
                    return MCPResponse(success=True, data=tools_list)
                
                elif request.method == "call_tool":
                    tool_name = request.params.get("name")
                    arguments = request.params.get("arguments", {})
                    
                    if tool_name not in self.tools:
                        return MCPResponse(
                            success=False, 
                            error=f"Unknown tool: {tool_name}"
                        )
                    
                    result = await self.execute_tool(tool_name, arguments)
                    return MCPResponse(success=True, data=result)
                
                else:
                    return MCPResponse(
                        success=False, 
                        error=f"Unknown method: {request.method}"
                    )
            
            except Exception as e:
                return MCPResponse(success=False, error=str(e))
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool with given arguments."""
        
        if tool_name == "get_crew_status":
            crew_id = arguments.get("crew_id", "default")
            return await self.get_crew_status(crew_id)
        
        elif tool_name == "execute_crew_task":
            task_description = arguments.get("task_description")
            agent_role = arguments.get("agent_role")
            
            if not task_description or not agent_role:
                raise ValueError("task_description and agent_role are required")
            
            return await self.execute_crew_task(task_description, agent_role)
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def get_crew_status(self, crew_id: str) -> Dict[str, Any]:
        """Get crew status - mock implementation."""
        return {
            "crew_id": crew_id,
            "status": "active",
            "agents": ["researcher", "writer", "reviewer"],
            "current_task": "Analyzing data",
            "completion": 0.75,
            "timestamp": "2024-01-01T12:00:00Z"
        }
    
    async def execute_crew_task(self, task_description: str, agent_role: str) -> Dict[str, Any]:
        """Execute crew task - mock implementation."""
        task_id = f"task_{abs(hash(task_description)) % 10000}"
        
        return {
            "task_id": task_id,
            "status": "completed",
            "agent_role": agent_role,
            "task_description": task_description,
            "result": f"Task '{task_description}' completed successfully by {agent_role} agent",
            "execution_time": "2.5s",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    
    def run(self, host: str = "localhost", port: int = 8000):
        """Run the MCP server."""
        uvicorn.run(self.app, host=host, port=port)