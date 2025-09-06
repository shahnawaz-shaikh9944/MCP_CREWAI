import asyncio
import threading
import time
from mcp_server import SimpleMCPServer
from crewai_connector import UpdatedCrewAIConnector
from config import Config

class FixedIntegrationTester:
    def __init__(self):
        self.mcp_server = SimpleMCPServer()
        self.connector = None
        self.server_thread = None
    
    def start_mcp_server(self):
        """Start MCP server in background thread."""
        def run_server():
            self.mcp_server.run(Config.MCP_SERVER_HOST, Config.MCP_SERVER_PORT)
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        time.sleep(3)  # Wait for server to start
    
    async def test_configuration(self) -> bool:
        """Test configuration validation."""
        print("Testing configuration...")
        if Config.validate():
            print("✅ Configuration is valid")
            print(f"   Endpoint: {Config.AZURE_OPENAI_ENDPOINT}")
            print(f"   Deployment: {Config.AZURE_OPENAI_DEPLOYMENT_NAME}")
            print(f"   MCP Server: {Config.MCP_SERVER_HOST}:{Config.MCP_SERVER_PORT}")
            return True
        else:
            print("❌ Configuration is invalid. Check your .env file:")
            print(f"   API Key: {'✓' if Config.AZURE_OPENAI_API_KEY else '✗'}")
            print(f"   Endpoint: {'✓' if Config.AZURE_OPENAI_ENDPOINT else '✗'}")
            print(f"   Deployment: {'✓' if Config.AZURE_OPENAI_DEPLOYMENT_NAME else '✗'}")
            return False
    
    async def test_mcp_server_health(self) -> bool:
        """Test MCP server health."""
        print("Testing MCP server health...")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"http://{Config.MCP_SERVER_HOST}:{Config.MCP_SERVER_PORT}/health"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ MCP server is healthy: {data['status']}")
                        return True
                    else:
                        print(f"❌ MCP server returned status {response.status}")
                        return False
        except Exception as e:
            print(f"❌ MCP server connection failed: {e}")
            return False
    
    async def test_mcp_tools(self) -> bool:
        """Test MCP tools listing."""
        print("Testing MCP tools...")
        try:
            self.connector = UpdatedCrewAIConnector()
            tools = await self.connector.list_mcp_tools()
            
            print(f"✅ Found {len(tools)} MCP tools:")
            for tool in tools:
                print(f"   • {tool['name']}: {tool['description']}")
            
            return len(tools) > 0
        except Exception as e:
            print(f"❌ MCP tools test failed: {e}")
            return False
    
    async def test_crew_status(self) -> bool:
        """Test crew status retrieval."""
        print("Testing crew status retrieval...")
        try:
            if not self.connector:
                self.connector = UpdatedCrewAIConnector()
            
            status_response = await self.connector.get_crew_status_from_mcp("test-crew")
            
            if status_response.get("success"):
                status_data = status_response.get("data", {})
                print(f"✅ Crew status retrieved successfully")
                print(f"   Crew ID: {status_data.get('crew_id', 'N/A')}")
                print(f"   Status: {status_data.get('status', 'N/A')}")
                print(f"   Completion: {status_data.get('completion', 'N/A')}")
                return True
            else:
                print(f"❌ Failed to get crew status: {status_response.get('error')}")
                return False
        except Exception as e:
            print(f"❌ Crew status test failed: {e}")
            return False
    
    async def test_crew_execution(self) -> bool:
        """Test CrewAI execution with MCP."""
        print("Testing CrewAI execution with MCP integration...")
        try:
            if not self.connector:
                self.connector = UpdatedCrewAIConnector()
            
            task_description = "Analyze current trends in AI and machine learning"
            result = await self.connector.execute_crew_with_mcp(
                task_description=task_description,
                agent_role="researcher"
            )
            
            if result.get("status") == "success":
                print("✅ CrewAI execution successful")
                crew_result = result.get("crew_result", "")
                print(f"   Task completed, result length: {len(crew_result)} characters")
                
                mcp_response = result.get("mcp_response", {})
                if mcp_response.get("success"):
                    mcp_data = mcp_response.get("data", {})
                    print(f"   MCP task ID: {mcp_data.get('task_id', 'N/A')}")
                    print(f"   MCP status: {mcp_data.get('status', 'N/A')}")
                
                return True
            else:
                print(f"❌ CrewAI execution failed: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ CrewAI execution test failed: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all integration tests."""
        print("🚀 Starting Fixed CrewAI + MCP + Azure OpenAI Integration Tests")
        print("=" * 70)
        
        tests = [
            ("Configuration Validation", self.test_configuration),
            ("MCP Server Health Check", self.test_mcp_server_health),
            ("MCP Tools Discovery", self.test_mcp_tools),
            ("Crew Status Retrieval", self.test_crew_status),
            ("CrewAI Task Execution", self.test_crew_execution)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n🔍 {test_name}")
            print("-" * 50)
            try:
                results[test_name] = await test_func()
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                results[test_name] = False
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 70)
        
        passed = 0
        for test_name, result in results.items():
            status_emoji = "✅" if result else "❌"
            status_text = "PASS" if result else "FAIL"
            print(f"{status_emoji} {test_name}: {status_text}")
            if result:
                passed += 1
        
        total = len(results)
        print(f"\n📈 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Integration is working correctly.")
        else:
            print(f"⚠️  {total - passed} test(s) failed. Check the errors above.")
        
        return passed == total

def main():
    """Main test runner."""
    tester = FixedIntegrationTester()
    
    try:
        print("Starting MCP server...")
        tester.start_mcp_server()
        
        # Run tests
        success = asyncio.run(tester.run_all_tests())
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())