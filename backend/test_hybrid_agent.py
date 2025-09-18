#!/usr/bin/env python3
"""
Simple test script to verify hybrid agent implementation works.
"""

import os
import tempfile
import time
from hybrid_agent_loop import hybrid_agent_loop_manager

def test_hybrid_agent():
    """Test hybrid agent functionality."""
    print("🧪 Testing hybrid agent implementation...")
    
    # Get manager stats
    stats = hybrid_agent_loop_manager.get_stats()
    print(f"📊 Manager stats: {stats}")
    
    # Create temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = os.path.join(temp_dir, "workspace")
        os.makedirs(workspace_path, exist_ok=True)
        
        # Create a simple test project
        project_path = os.path.join(workspace_path, "project")
        os.makedirs(project_path, exist_ok=True)
        
        with open(os.path.join(project_path, "test.txt"), "w") as f:
            f.write("Hello, Hybrid Agent!")
        
        print(f"📁 Created test workspace at: {workspace_path}")
        
        # Create hybrid agent
        try:
            agent = hybrid_agent_loop_manager.create_agent_loop(
                user_uuid="test-user-123",
                app_slug="test-app",
                riff_slug="test-riff",
                api_key="mock-key",  # Using mock key for testing
                model="claude-sonnet-4-20250514",
                workspace_path=workspace_path,
                message_callback=lambda event: print(f"📨 Event: {event.get('kind', 'unknown')}")
            )
            
            if agent:
                print("✅ Created hybrid agent successfully!")
                
                # Get status
                status = agent.get_agent_status()
                print(f"📊 Agent status: {status}")
                
                # Send a test message
                print("💬 Sending test message...")
                response = agent.send_message("List the files in the project directory")
                print(f"📤 Response: {response}")
                
                # Wait a bit for processing
                time.sleep(2)
                
                # Get events
                events = agent.get_all_events()
                print(f"📋 Retrieved {len(events)} events")
                
                # Cleanup
                hybrid_agent_loop_manager.remove_agent_loop("test-user-123", "test-app", "test-riff")
                print("🧹 Agent cleaned up")
                
                return True
            else:
                print("❌ Failed to create agent")
                return False
                
        except Exception as e:
            print(f"❌ Error testing agent: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_hybrid_agent()
    if success:
        print("🎉 Hybrid agent test completed successfully!")
    else:
        print("💥 Hybrid agent test failed!")
        exit(1)