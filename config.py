import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Config:
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
    
    # MCP Server Configuration
    MCP_SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "localhost")
    MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8000"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required environment variables are set."""
        required_vars = [
            cls.AZURE_OPENAI_API_KEY,
            cls.AZURE_OPENAI_ENDPOINT,
            cls.AZURE_OPENAI_DEPLOYMENT_NAME
        ]
        return all(var for var in required_vars)