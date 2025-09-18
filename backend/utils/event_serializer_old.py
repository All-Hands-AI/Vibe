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

        # For now, create a simple generic message for all events
        # TODO: Implement specific event type handling later
        content = f"🔄 **{event_kind}**\n\nAgent event occurred"
        
        # Try to extract useful information
        if event_kind == "MessageEvent":
            llm_message = event.get("llm_message", {})
            if llm_message.get("role") == "assistant":
                content_items = llm_message.get("content", [])
                if isinstance(content_items, list):
                    text_content = ""
                    for item in content_items:
                        if isinstance(item, dict) and item.get("text"):
                            text_content += item["text"]
                    if text_content:
                        base_message.update({
                            "content": text_content,
                            "type": "assistant",
                            "metadata": base_message["metadata"],
                        })
                        return base_message
                elif isinstance(content_items, str):
                    base_message.update({
                        "content": content_items,
                        "type": "assistant", 
                        "metadata": base_message["metadata"],
                    })
                    return base_message
        
        # Generic handling for other events
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
    event: Dict[str, Any], base_message: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Serialize MessageEvent to user message format."""
    try:
        # Only process assistant messages
        source = event.get("source", "")
        llm_message = event.get("llm_message", {})
        
        if source == "assistant" or llm_message.get("role") == "assistant":
            content = ""
            
            # Extract content from llm_message
            if llm_message and llm_message.get("content"):
                content_items = llm_message["content"]
                if isinstance(content_items, list):
                    for content_item in content_items:
                        if isinstance(content_item, dict) and content_item.get("text"):
                            content += content_item["text"]
                elif isinstance(content_items, str):
                    content = content_items

            if content:
                base_message.update(
                    {
                        "content": content,
                        "type": "assistant",
                        "metadata": {
                            **base_message["metadata"],
                            "activated_microagents": event.get("activated_microagents", []),
                            "has_extended_content": bool(event.get("extended_content", [])),
                            "metrics": _extract_metrics(event),
                        },
                    }
                )
                return base_message

        return None  # Skip non-assistant messages

    except Exception as e:
        logger.error(f"❌ Error serializing MessageEvent: {e}")
        return None


def _serialize_action_event(event: Dict[str, Any], base_message: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize ActionEvent to user message format."""
    try:
        # Extract action details
        action_name = event.get("tool_name", "unknown_action")
        action_data = {}

        if "action" in event:
            action = event["action"]
            action_data = {
                "action_type": action.get("kind", "unknown") if isinstance(action, dict) else str(type(action)),
                "action_details": _safe_extract_action_details(action),
            }

        # Create friendly message based on action type
        content = _create_action_message(action_name, action_data, event)

        base_message.update(
            {
                "content": content,
                "type": "system",
                "metadata": {
                    **base_message["metadata"],
                    "tool_name": action_name,
                    "tool_call_id": event.get("tool_call_id"),
                    "action_data": action_data,
                    "thought": _extract_thought_content(event),
                    "metrics": _extract_metrics(event),
                },
            }
        )

        return base_message

    except Exception as e:
        logger.error(f"❌ Error serializing ActionEvent: {e}")
        return _create_fallback_message(event, base_message, "Action event occurred")


def _serialize_observation_event(event, base_message: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize ObservationEvent to user message format."""
    try:
        tool_name = getattr(event, "tool_name", "unknown_tool")
        observation_data = {}

        if hasattr(event, "observation"):
            observation = event.observation
            observation_data = {
                "observation_type": type(observation).__name__,
                "observation_details": _safe_extract_observation_details(observation),
            }

        # Create friendly message based on observation
        content = _create_observation_message(tool_name, observation_data, event)

        base_message.update(
            {
                "content": content,
                "type": "system",
                "metadata": {
                    **base_message["metadata"],
                    "tool_name": tool_name,
                    "tool_call_id": getattr(event, "tool_call_id", None),
                    "action_id": getattr(event, "action_id", None),
                    "observation_data": observation_data,
                },
            }
        )

        return base_message

    except Exception as e:
        logger.error(f"❌ Error serializing ObservationEvent: {e}")
        return _create_fallback_message(event, base_message, "Tool execution completed")


def _serialize_error_event(event, base_message: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize AgentErrorEvent to user message format."""
    try:
        error_message = getattr(event, "error", "Unknown error occurred")

        content = f"⚠️ **Agent Error**\n\n{error_message}"

        base_message.update(
            {
                "content": content,
                "type": "error",
                "metadata": {
                    **base_message["metadata"],
                    "error_message": error_message,
                    "metrics": _extract_metrics(event),
                },
            }
        )

        return base_message

    except Exception as e:
        logger.error(f"❌ Error serializing AgentErrorEvent: {e}")
        return _create_fallback_message(event, base_message, "An error occurred")


def _serialize_pause_event(event, base_message: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize PauseEvent to user message format."""
    try:
        content = "⏸️ **Agent Paused**\n\nThe agent has paused execution and is waiting for further instructions."

        base_message.update(
            {"content": content, "type": "system", "metadata": base_message["metadata"]}
        )

        return base_message

    except Exception as e:
        logger.error(f"❌ Error serializing PauseEvent: {e}")
        return _create_fallback_message(event, base_message, "Agent paused")


def _serialize_generic_event(event, base_message: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize unknown event types with generic handling."""
    try:
        event_type = type(event).__name__
        content = f"🔄 **{event_type}**\n\nAgent event: {event_type}"

        # Try to extract any useful information from the event
        event_info = {}
        for attr in ["source", "timestamp", "id"]:
            if hasattr(event, attr):
                event_info[attr] = getattr(event, attr)

        base_message.update(
            {
                "content": content,
                "type": "system",
                "metadata": {**base_message["metadata"], "event_info": event_info},
            }
        )

        return base_message

    except Exception as e:
        logger.error(f"❌ Error serializing generic event: {e}")
        return _create_fallback_message(event, base_message, "Agent event occurred")


def _create_action_message(action_name: str, action_data: Dict, event) -> str:
    """Create a friendly message for action events."""
    try:
        # Map common action types to friendly messages
        action_messages = {
            "execute_bash": "🖥️ **Executing Command**",
            "str_replace_editor": "📝 **Editing File**",
            "task_tracker": "📋 **Managing Tasks**",
            "finish": "✅ **Task Complete**",
            "think": "🤔 **Thinking**",
        }

        base_msg = action_messages.get(action_name, f"🔧 **Using {action_name}**")

        # Add action details if available
        details = action_data.get("action_details", {})
        if details:
            if action_name == "execute_bash" and "command" in details:
                base_msg += f"\n\nRunning: `{details['command']}`"
            elif action_name == "str_replace_editor" and "command" in details:
                cmd = details.get("command", "")
                path = details.get("path", "")
                if cmd == "view" and path:
                    base_msg += f"\n\nViewing file: `{path}`"
                elif cmd == "create" and path:
                    base_msg += f"\n\nCreating file: `{path}`"
                elif cmd == "str_replace" and path:
                    base_msg += f"\n\nEditing file: `{path}`"
            elif action_name == "think" and "thought" in details:
                base_msg += f"\n\n{details['thought']}"

        # Add thought content if available
        thought = _extract_thought_content(event)
        if thought and action_name != "think":  # Don't duplicate for think actions
            base_msg += f"\n\n*Reasoning:* {thought}"

        return base_msg

    except Exception as e:
        logger.error(f"❌ Error creating action message: {e}")
        return f"🔧 **Action: {action_name}**"


def _create_observation_message(tool_name: str, observation_data: Dict, event) -> str:
    """Create a friendly message for observation events."""
    try:
        # Map common tools to friendly messages
        tool_messages = {
            "execute_bash": "🖥️ **Command Result**",
            "str_replace_editor": "📝 **File Operation Result**",
            "task_tracker": "📋 **Task Update**",
        }

        base_msg = tool_messages.get(tool_name, f"🔍 **{tool_name} Result**")

        # Add observation details if available
        details = observation_data.get("observation_details", {})
        if details:
            if tool_name == "execute_bash":
                if "output" in details:
                    output = details["output"]
                    if output:
                        # Truncate very long output
                        if len(output) > 1000:
                            output = output[:1000] + "\n... (output truncated)"
                        base_msg += f"\n\n```\n{output}\n```"
                if "exit_code" in details:
                    exit_code = details["exit_code"]
                    if exit_code == 0:
                        base_msg += f"\n\n✅ Command completed successfully"
                    else:
                        base_msg += f"\n\n❌ Command failed with exit code {exit_code}"
            elif tool_name == "str_replace_editor":
                if "content" in details:
                    base_msg += f"\n\nOperation completed"

        return base_msg

    except Exception as e:
        logger.error(f"❌ Error creating observation message: {e}")
        return f"🔍 **{tool_name} completed**"


def _safe_extract_action_details(action) -> Dict[str, Any]:
    """Safely extract details from an action object."""
    try:
        details = {}
        # Common action attributes to extract
        for attr in ["command", "path", "content", "old_str", "new_str", "thought"]:
            if hasattr(action, attr):
                value = getattr(action, attr)
                # Truncate very long strings
                if isinstance(value, str) and len(value) > 500:
                    value = value[:500] + "... (truncated)"
                details[attr] = value
        return details
    except Exception as e:
        logger.error(f"❌ Error extracting action details: {e}")
        return {}


def _safe_extract_observation_details(observation) -> Dict[str, Any]:
    """Safely extract details from an observation object."""
    try:
        details = {}
        # Common observation attributes to extract
        for attr in ["output", "exit_code", "content", "error", "success"]:
            if hasattr(observation, attr):
                value = getattr(observation, attr)
                # Truncate very long strings
                if isinstance(value, str) and len(value) > 1000:
                    value = value[:1000] + "... (truncated)"
                details[attr] = value

        # Special handling for exit_code: if it's None or missing, try to get it from metadata
        if details.get("exit_code") is None and hasattr(observation, "metadata"):
            metadata = getattr(observation, "metadata")
            if metadata and hasattr(metadata, "exit_code"):
                details["exit_code"] = getattr(metadata, "exit_code")

        return details
    except Exception as e:
        logger.error(f"❌ Error extracting observation details: {e}")
        return {}


def _extract_thought_content(event) -> Optional[str]:
    """Extract thought content from an event."""
    try:
        if hasattr(event, "thought") and event.thought:
            thoughts = []
            for thought_item in event.thought:
                if hasattr(thought_item, "text"):
                    thoughts.append(thought_item.text)
            return " ".join(thoughts) if thoughts else None
        return None
    except Exception as e:
        logger.error(f"❌ Error extracting thought content: {e}")
        return None


def _extract_metrics(event) -> Optional[Dict[str, Any]]:
    """Extract metrics from an event if available."""
    try:
        if hasattr(event, "metrics") and event.metrics:
            metrics = event.metrics
            return {
                "completion_tokens": getattr(metrics, "completion_tokens", None),
                "prompt_tokens": getattr(metrics, "prompt_tokens", None),
                "total_tokens": getattr(metrics, "total_tokens", None),
                "cost": getattr(metrics, "cost", None),
            }
        return None
    except Exception as e:
        logger.error(f"❌ Error extracting metrics: {e}")
        return None


def _create_fallback_message(
    event, base_message: Dict[str, Any], default_content: str
) -> Dict[str, Any]:
    """Create a fallback message when serialization fails."""
    base_message.update(
        {
            "content": f"🔄 **{default_content}**\n\nEvent type: {type(event).__name__}",
            "type": "system",
            "metadata": {**base_message["metadata"], "serialization_error": True},
        }
    )
    return base_message
