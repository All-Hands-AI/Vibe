"""
Event serialization utilities for converting OpenHands agent events into user-friendly messages.
"""

import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from utils.logging import get_logger

# Add the site-packages to the path for openhands imports
sys.path.insert(0, ".venv/lib/python3.12/site-packages")

from openhands.sdk.event import (
    MessageEvent,
    ActionEvent,
    ObservationEvent,
    AgentErrorEvent,
    PauseEvent,
)

logger = get_logger(__name__)


def serialize_agent_event_to_message(
    event: Any, user_uuid: str, app_slug: str, riff_slug: str
) -> Optional[Dict[str, Any]]:
    """
    Convert any OpenHands agent event into a user-friendly message format.

    Args:
        event: The OpenHands event object
        user_uuid: User UUID for the message
        app_slug: App slug for the message
        riff_slug: Riff slug for the message

    Returns:
        Dict containing the serialized message, or None if event should be skipped
    """
    try:
        event_type = type(event).__name__
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
                "event_type": event_type,
                "source": getattr(event, "source", "unknown"),
            },
        }

        # Handle different event types
        if isinstance(event, MessageEvent):
            return _serialize_message_event(event, base_message)
        elif isinstance(event, ActionEvent):
            return _serialize_action_event(event, base_message)
        elif isinstance(event, ObservationEvent):
            return _serialize_observation_event(event, base_message)
        elif isinstance(event, AgentErrorEvent):
            return _serialize_error_event(event, base_message)
        elif isinstance(event, PauseEvent):
            return _serialize_pause_event(event, base_message)
        else:
            # Handle unknown event types with generic serialization
            return _serialize_generic_event(event, base_message)

    except Exception as e:
        logger.error(f"❌ Error serializing event {type(event).__name__}: {e}")
        return None


def _serialize_message_event(
    event, base_message: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Serialize MessageEvent to user message format."""
    try:
        # Only process assistant messages
        if event.source == "assistant" or (
            hasattr(event, "llm_message") and event.llm_message.role == "assistant"
        ):

            content = ""
            if hasattr(event, "llm_message") and event.llm_message.content:
                for content_item in event.llm_message.content:
                    if hasattr(content_item, "text"):
                        content += content_item.text

            if content:
                base_message.update(
                    {
                        "content": content,
                        "type": "assistant",
                        "metadata": {
                            **base_message["metadata"],
                            "activated_microagents": getattr(
                                event, "activated_microagents", []
                            ),
                            "has_extended_content": bool(
                                getattr(event, "extended_content", [])
                            ),
                            "metrics": _extract_metrics(event),
                        },
                    }
                )
                return base_message

        return None  # Skip non-assistant messages

    except Exception as e:
        logger.error(f"❌ Error serializing MessageEvent: {e}")
        return None


def _serialize_action_event(event, base_message: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize ActionEvent to user message format."""
    try:
        # Extract action details
        action_name = getattr(event, "tool_name", "unknown_action")
        action_data = {}

        if hasattr(event, "action"):
            action = event.action
            action_data = {
                "action_type": type(action).__name__,
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
                    "tool_call_id": getattr(event, "tool_call_id", None),
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
            elif tool_name == "task_tracker":
                # For task tracker, show the current task list
                task_list = _extract_task_list_from_details(details)
                if task_list:
                    base_msg += f"\n\n{task_list}"

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


def _extract_task_list_from_details(details: Dict[str, Any]) -> Optional[str]:
    """Extract and format task list from task_tracker observation details."""
    try:
        # Look for task list in various possible locations in the observation details
        task_list_data = None

        # Check common locations where task list might be stored
        if "output" in details:
            output = details["output"]
            # Try to parse JSON output if it looks like task data
            if isinstance(output, str):
                import json

                try:
                    parsed_output = json.loads(output)
                    if isinstance(parsed_output, dict) and "task_list" in parsed_output:
                        task_list_data = parsed_output["task_list"]
                    elif isinstance(parsed_output, list):
                        # Output might be the task list directly
                        task_list_data = parsed_output
                except json.JSONDecodeError:
                    # Not JSON, might be plain text task list
                    if "task" in output.lower() or "todo" in output.lower():
                        return f"```\n{output}\n```"
            elif isinstance(output, (list, dict)):
                task_list_data = output

        # Check if there's a direct task_list field
        if "task_list" in details:
            task_list_data = details["task_list"]

        # Format the task list if we found it
        if task_list_data and isinstance(task_list_data, list):
            return _format_task_list(task_list_data)
        elif task_list_data:
            # If it's not a list, try to format it as is
            return f"```\n{str(task_list_data)}\n```"

        return None

    except Exception as e:
        logger.error(f"❌ Error extracting task list from details: {e}")
        return None


def _format_task_list(tasks: list) -> str:
    """Format a task list into a readable markdown format."""
    try:
        if not tasks:
            return "**Current Tasks:** No tasks defined"

        formatted_tasks = ["**Current Tasks:**"]

        for i, task in enumerate(tasks, 1):
            if isinstance(task, dict):
                title = task.get("title", f"Task {i}")
                status = task.get("status", "unknown")
                notes = task.get("notes", "")

                # Format status with emoji
                status_emoji = {"todo": "⏳", "in_progress": "🔄", "done": "✅"}.get(
                    status, "❓"
                )

                task_line = f"{i}. {status_emoji} **{title}** ({status})"
                if notes:
                    task_line += f" - {notes}"
                formatted_tasks.append(task_line)
            else:
                # Handle simple string tasks
                formatted_tasks.append(f"{i}. {task}")

        return "\n".join(formatted_tasks)

    except Exception as e:
        logger.error(f"❌ Error formatting task list: {e}")
        return f"**Current Tasks:** {len(tasks)} tasks (formatting error)"


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
