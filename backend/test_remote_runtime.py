#!/usr/bin/env python3
"""
Test script for remote runtime functionality.

This script tests the RemoteRuntimeClient and modified AgentLoop
to ensure they work correctly with remote agent servers.
"""

import os
import sys
import time
from pydantic import SecretStr

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from remote_runtime_client import RemoteRuntimeClient
from agent_loop import AgentLoopManager
from openhands.sdk import LLM
from utils.logging import get_logger

logger = get_logger(__name__)


def test_remote_runtime_client():
    """Test the RemoteRuntimeClient directly."""
    logger.info("🧪 Testing RemoteRuntimeClient...")
    
    # Create a simple event callback
    def event_callback(event):
        logger.info(f"📨 Received event: {event.get('kind', 'unknown')} - {event.get('message', '')}")
    
    # Initialize the client
    client = RemoteRuntimeClient(
        runtime_api_url="https://runtime.staging.all-hands.dev",
        runtime_api_key="ODu0HV9KL1wc1NUerIgZWqn1w8WctjWD",
        event_callback=event_callback,
    )
    
    try:
        # Test starting a remote runtime
        logger.info("🚀 Starting remote runtime...")
        runtime_info = client.start_remote_runtime()
        logger.info(f"✅ Runtime started: {runtime_info.runtime_id}")
        
        # Test creating a conversation
        logger.info("💬 Creating conversation...")
        llm_config = {
            "model": "anthropic/claude-3-5-sonnet-20241022",
            "api_key": os.getenv("ANTHROPIC_API_KEY", "test-key"),
            "base_url": "https://api.anthropic.com",
        }
        
        conversation_info = client.create_conversation(
            runtime_info=runtime_info,
            llm_config=llm_config,
            workspace_path="/workspace/project",
            initial_message="Hello! Can you help me test this remote runtime?",
        )
        logger.info(f"✅ Conversation created: {conversation_info.conversation_id}")
        
        # Wait a bit for the initial message to process
        time.sleep(5)
        
        # Test getting conversation status
        logger.info("📊 Getting conversation status...")
        status = client.get_conversation_status(conversation_info)
        logger.info(f"✅ Status: {status}")
        
        # Test getting events
        logger.info("📥 Getting conversation events...")
        events = client.get_conversation_events(conversation_info, limit=10)
        logger.info(f"✅ Retrieved {len(events)} events")
        
        # Test sending another message
        logger.info("📤 Sending another message...")
        success = client.send_message(
            conversation_info,
            "What is the current working directory?",
            run=True
        )
        logger.info(f"✅ Message sent: {success}")
        
        # Wait a bit for processing
        time.sleep(10)
        
        # Get events again
        logger.info("📥 Getting updated events...")
        events = client.get_conversation_events(conversation_info, limit=20)
        logger.info(f"✅ Retrieved {len(events)} events")
        
        # Test pause/resume
        logger.info("⏸️ Testing pause...")
        paused = client.pause_conversation(conversation_info)
        logger.info(f"✅ Paused: {paused}")
        
        logger.info("▶️ Testing resume...")
        resumed = client.resume_conversation(conversation_info)
        logger.info(f"✅ Resumed: {resumed}")
        
        logger.info("✅ RemoteRuntimeClient test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ RemoteRuntimeClient test failed: {e}")
        return False
    finally:
        # Cleanup
        try:
            if 'conversation_info' in locals():
                client.cleanup_conversation(conversation_info.conversation_id)
            if 'runtime_info' in locals():
                client.cleanup_runtime(runtime_info.runtime_id)
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")


def test_agent_loop_with_remote_runtime():
    """Test the AgentLoop with remote runtime."""
    logger.info("🧪 Testing AgentLoop with remote runtime...")
    
    try:
        # Create LLM instance
        llm = LLM(
            model="anthropic/claude-3-5-sonnet-20241022",
            api_key=SecretStr(os.getenv("ANTHROPIC_API_KEY", "test-key")),
            base_url="https://api.anthropic.com",
        )
        
        # Create event callback
        def message_callback(event):
            logger.info(f"📨 AgentLoop event: {event}")
        
        # Create remote runtime client
        remote_client = RemoteRuntimeClient(
            runtime_api_url="https://runtime.staging.all-hands.dev",
            runtime_api_key="ODu0HV9KL1wc1NUerIgZWqn1w8WctjWD",
            event_callback=message_callback,
        )
        
        # Get manager and create agent loop
        manager = AgentLoopManager()
        
        agent_loop = manager.create_agent_loop(
            user_uuid="test-user-123",
            app_slug="test-app",
            riff_slug="test-riff",
            llm=llm,
            workspace_path="/workspace/project",
            message_callback=message_callback,
            use_remote_runtime=True,
            remote_runtime_client=remote_client,
        )
        
        logger.info("✅ AgentLoop created with remote runtime")
        
        # Test sending a message
        logger.info("📤 Sending message via AgentLoop...")
        response = agent_loop.send_message("Hello! Can you list the files in the current directory?")
        logger.info(f"✅ Message response: {response}")
        
        # Wait for processing
        time.sleep(10)
        
        # Test getting status
        logger.info("📊 Getting agent status...")
        status = agent_loop.get_agent_status()
        logger.info(f"✅ Agent status: {status}")
        
        # Test getting events
        logger.info("📥 Getting all events...")
        events = agent_loop.get_all_events()
        logger.info(f"✅ Retrieved {len(events)} events")
        
        # Test pause/resume
        logger.info("⏸️ Testing pause via AgentLoop...")
        paused = agent_loop.pause_agent()
        logger.info(f"✅ Paused: {paused}")
        
        logger.info("▶️ Testing resume via AgentLoop...")
        resumed = agent_loop.resume_agent()
        logger.info(f"✅ Resumed: {resumed}")
        
        logger.info("✅ AgentLoop remote runtime test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ AgentLoop remote runtime test failed: {e}")
        return False
    finally:
        # Cleanup
        try:
            if 'agent_loop' in locals():
                agent_loop.cleanup()
        except Exception as e:
            logger.error(f"❌ AgentLoop cleanup error: {e}")


def main():
    """Run all tests."""
    logger.info("🚀 Starting remote runtime tests...")
    
    # Test 1: RemoteRuntimeClient directly
    logger.info("\n" + "="*50)
    logger.info("TEST 1: RemoteRuntimeClient")
    logger.info("="*50)
    
    client_test_passed = test_remote_runtime_client()
    
    # Test 2: AgentLoop with remote runtime
    logger.info("\n" + "="*50)
    logger.info("TEST 2: AgentLoop with Remote Runtime")
    logger.info("="*50)
    
    agent_loop_test_passed = test_agent_loop_with_remote_runtime()
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("TEST SUMMARY")
    logger.info("="*50)
    logger.info(f"RemoteRuntimeClient: {'✅ PASSED' if client_test_passed else '❌ FAILED'}")
    logger.info(f"AgentLoop Remote: {'✅ PASSED' if agent_loop_test_passed else '❌ FAILED'}")
    
    if client_test_passed and agent_loop_test_passed:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())