"""
Event serialization utilities for converting Docker agent server events into user-friendly messages.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from utils.logging import get_logger

logger = get_logger(__name__)


def serialize_agent_event_to_message(
    event: Dict[str, Any], user_uuid: str, app_slug: str, riff_slug: str
) -> Optional[Dict[str, Any]]:
    """
    Convert Docker agent server event into a user-friendly message format.

    Args:
        event: The event dictionary from Docker agent server
        user_uuid: User UUID for the message
        app_slug: App slug for the message
        riff_slug: Riff slug for the message

    Returns:
        Dict containing the serialized message, or None if event should be skipped
    """
    try:
        event_kind = event.get("kind", "unknown")
        message_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        # Base message structure
        base_message = {
            "id": message_id,
            "riff_slug": riff_slug,
            "app_slug": app_slug,
            "created_at": created_at,
            "created_by": "assistant",
            "metadata": {
                "event_type": event_kind,
                "source": event.get("source", "unknown"),
                "event_id": event.get("id"),
                "timestamp": event.get("timestamp"),
            },
        }

        # Handle MessageEvent specially for assistant responses
        if event_kind == "MessageEvent":
            llm_message = event.get("llm_message", {})
            if llm_message.get("role") == "assistant":
                content_items = llm_message.get("content", [])
                text_content = ""
                
                if isinstance(content_items, list):
                    for item in content_items:
                        if isinstance(item, dict) and item.get("text"):
                            text_content += item["text"]
                elif isinstance(content_items, str):
                    text_content = content_items
                
                if text_content:
                    base_message.update({
                        "content": text_content,
                        "type": "assistant",
                        "metadata": base_message["metadata"],
                    })
                    return base_message
            
            # Skip non-assistant messages
            return None
        
        # Handle ActionEvent
        elif event_kind == "ActionEvent":
            tool_name = event.get("tool_name", "unknown_tool")
            action = event.get("action", {})
            
            # Create friendly message based on tool
            if tool_name == "execute_bash":
                command = action.get("command", "") if isinstance(action, dict) else ""
                content = f"🖥️ **Executing Command**\n\nRunning: `{command}`"
            elif tool_name == "str_replace_editor":
                cmd = action.get("command", "") if isinstance(action, dict) else ""
                path = action.get("path", "") if isinstance(action, dict) else ""
                if cmd == "view":
                    content = f"📝 **Viewing File**\n\nFile: `{path}`"
                elif cmd == "create":
                    content = f"📝 **Creating File**\n\nFile: `{path}`"
                elif cmd == "str_replace":
                    content = f"📝 **Editing File**\n\nFile: `{path}`"
                else:
                    content = f"📝 **File Operation**\n\nOperation: {cmd} on `{path}`"
            else:
                content = f"🔧 **Using {tool_name}**\n\nTool action executed"
            
            base_message.update({
                "content": content,
                "type": "system",
                "metadata": {
                    **base_message["metadata"],
                    "tool_name": tool_name,
                },
            })
            return base_message
        
        # Handle ObservationEvent
        elif event_kind == "ObservationEvent":
            tool_name = event.get("tool_name", "unknown_tool")
            observation = event.get("observation", {})
            
            if tool_name == "execute_bash":
                output = observation.get("output", "") if isinstance(observation, dict) else ""
                exit_code = observation.get("exit_code", 0) if isinstance(observation, dict) else 0
                
                content = "🖥️ **Command Result**\n\n"
                if output:
                    # Truncate very long output
                    if len(output) > 1000:
                        output = output[:1000] + "\n... (output truncated)"
                    content += f"```\n{output}\n```\n\n"
                
                if exit_code == 0:
                    content += "✅ Command completed successfully"
                else:
                    content += f"❌ Command failed with exit code {exit_code}"
            
            elif tool_name == "str_replace_editor":
                content = "📝 **File Operation Result**\n\nOperation completed successfully"
            
            else:
                content = f"🔍 **{tool_name} Result**\n\nTool execution completed"
            
            base_message.update({
                "content": content,
                "type": "system",
                "metadata": {
                    **base_message["metadata"],
                    "tool_name": tool_name,
                },
            })
            return base_message
        
        # Handle other event types generically
        else:
            content = f"🔄 **{event_kind}**\n\nAgent event occurred"
            
            base_message.update({
                "content": content,
                "type": "system",
                "metadata": {
                    **base_message["metadata"],
                    "raw_event": event,  # Include raw event for debugging
                },
            })
            return base_message

    except Exception as e:
        logger.error(f"❌ Error serializing event {event.get('kind', 'unknown')}: {e}")
        return None