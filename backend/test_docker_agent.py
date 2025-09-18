#!/usr/bin/env python3
"""
Simple test script to verify Docker-based agent implementation works.
"""

import os
import tempfile
import time
from docker_agent_loop import DockerAgentLoop

def test_docker_agent():
    """Test basic Docker agent functionality."""
    print("🧪 Testing Docker-based agent implementation...")
    
    # Create temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = os.path.join(temp_dir, "workspace")
        os.makedirs(workspace_path, exist_ok=True)
        
        # Create a simple test project
        project_path = os.path.join(workspace_path, "project")
        os.makedirs(project_path, exist_ok=True)
        
        with open(os.path.join(project_path, "test.txt"), "w") as f:
            f.write("Hello, Docker Agent!")
        
        print(f"📁 Created test workspace at: {workspace_path}")
        
        # Create Docker agent
        try:
            agent = DockerAgentLoop(
                user_uuid="test-user-123",
                app_slug="test-app",
                riff_slug="test-riff",
                api_key="mock-key",  # Using mock key for testing
                model="claude-sonnet-4-20250514",
                workspace_path=workspace_path,
                message_callback=lambda event: print(f"📨 Event: {event.get('kind', 'unknown')}")
            )
            
            print("🐳 Created DockerAgentLoop instance")
            
            # Start the agent
            if agent.start():
                print("✅ Agent started successfully!")
                
                # Get status
                status = agent.get_agent_status()
                print(f"📊 Agent status: {status}")
                
                # Send a test message
                print("💬 Sending test message...")
                response = agent.send_message("List the files in the project directory")
                print(f"📤 Response: {response}")
                
                # Wait a bit for processing
                time.sleep(5)
                
                # Get events
                events = agent.get_all_events()
                print(f"📋 Retrieved {len(events)} events")
                
                # Cleanup
                agent.cleanup()
                print("🧹 Agent cleaned up")
                
                return True
            else:
                print("❌ Failed to start agent")
                return False
                
        except Exception as e:
            print(f"❌ Error testing agent: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_docker_agent()
    if success:
        print("🎉 Docker agent test completed successfully!")
    else:
        print("💥 Docker agent test failed!")
        exit(1)