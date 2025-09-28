"""
Command tracking service for monitoring action commands sent to agents.
Tracks command IDs and their execution status for install, run, test, and lint actions.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from utils.logging import get_logger
from storage.base_storage import DATA_DIR

logger = get_logger(__name__)


class CommandTracker:
    """Service for tracking command execution for riff actions"""
    
    def __init__(self):
        self.commands_dir = DATA_DIR / "commands"
        self.commands_dir.mkdir(exist_ok=True)
    
    def _get_command_file_path(self, user_uuid: str, app_slug: str, riff_slug: str) -> str:
        """Get the file path for storing command tracking data"""
        user_dir = self.commands_dir / user_uuid / app_slug / riff_slug
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir / "commands.json"
    
    def _load_commands(self, user_uuid: str, app_slug: str, riff_slug: str) -> Dict[str, Any]:
        """Load command tracking data from file"""
        try:
            file_path = self._get_command_file_path(user_uuid, app_slug, riff_slug)
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"❌ Error loading commands for {user_uuid[:8]}:{app_slug}:{riff_slug}: {e}")
            return {}
    
    def _save_commands(self, user_uuid: str, app_slug: str, riff_slug: str, commands: Dict[str, Any]) -> bool:
        """Save command tracking data to file"""
        try:
            file_path = self._get_command_file_path(user_uuid, app_slug, riff_slug)
            with open(file_path, 'w') as f:
                json.dump(commands, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"❌ Error saving commands for {user_uuid[:8]}:{app_slug}:{riff_slug}: {e}")
            return False
    
    def track_command_sent(
        self, 
        user_uuid: str, 
        app_slug: str, 
        riff_slug: str, 
        action: str, 
        command: str,
        agent_result: str = None
    ) -> str:
        """
        Track when a command is sent to the agent
        
        Args:
            user_uuid: User UUID
            app_slug: App slug
            riff_slug: Riff slug
            action: Action type (install, run, test, lint)
            command: The actual command sent
            agent_result: Result from agent.send_message()
            
        Returns:
            Command tracking ID
        """
        try:
            commands = self._load_commands(user_uuid, app_slug, riff_slug)
            
            # Generate a unique command ID
            command_id = f"{action}_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
            
            # Initialize action tracking if not exists
            if action not in commands:
                commands[action] = {
                    "latest_command_id": None,
                    "commands": []
                }
            
            # Create command record
            command_record = {
                "command_id": command_id,
                "command": command,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "status": "sent",
                "agent_result": agent_result,
                "tool_call_id": None,
                "action_id": None,
                "completed_at": None,
                "exit_code": None,
                "output": None
            }
            
            # Add to commands list and update latest
            commands[action]["commands"].append(command_record)
            commands[action]["latest_command_id"] = command_id
            
            # Keep only last 10 commands per action to prevent file bloat
            commands[action]["commands"] = commands[action]["commands"][-10:]
            
            # Save to file
            if self._save_commands(user_uuid, app_slug, riff_slug, commands):
                logger.info(f"✅ Tracked command sent: {command_id} for {action}")
                return command_id
            else:
                logger.error(f"❌ Failed to save command tracking for {command_id}")
                return command_id  # Return ID even if save failed
                
        except Exception as e:
            logger.error(f"❌ Error tracking command sent: {e}")
            return f"{action}_error_{int(datetime.now(timezone.utc).timestamp())}"
    
    def update_command_with_event(
        self, 
        user_uuid: str, 
        app_slug: str, 
        riff_slug: str, 
        tool_call_id: str = None,
        action_id: str = None,
        event_type: str = None,
        event_data: Dict[str, Any] = None
    ) -> bool:
        """
        Update command tracking with event information
        
        Args:
            user_uuid: User UUID
            app_slug: App slug  
            riff_slug: Riff slug
            tool_call_id: Tool call ID from event
            action_id: Action ID from event
            event_type: Type of event (ActionEvent, ObservationEvent, etc.)
            event_data: Additional event data
            
        Returns:
            True if update was successful
        """
        try:
            commands = self._load_commands(user_uuid, app_slug, riff_slug)
            
            # Find the most recent command that matches this event
            updated = False
            for action in ["install", "run", "test", "lint"]:
                if action in commands and commands[action]["commands"]:
                    # Look for the most recent command that doesn't have this event data yet
                    for command_record in reversed(commands[action]["commands"]):
                        if (command_record["status"] == "sent" and 
                            (not command_record.get("tool_call_id") or 
                             command_record.get("tool_call_id") == tool_call_id)):
                            
                            # Update with event information
                            if tool_call_id:
                                command_record["tool_call_id"] = tool_call_id
                            if action_id:
                                command_record["action_id"] = action_id
                            
                            # Handle different event types
                            if event_type == "ObservationEvent" and event_data:
                                command_record["status"] = "completed"
                                command_record["completed_at"] = datetime.now(timezone.utc).isoformat()
                                command_record["exit_code"] = event_data.get("exit_code")
                                command_record["output"] = event_data.get("output", "")[:1000]  # Limit output size
                            elif event_type == "ActionEvent" and event_data:
                                command_record["status"] = "executing"
                            
                            updated = True
                            break
                    
                    if updated:
                        break
            
            if updated:
                self._save_commands(user_uuid, app_slug, riff_slug, commands)
                logger.info(f"✅ Updated command with event: {event_type}")
                return True
            else:
                logger.debug(f"🔍 No matching command found for event: {event_type}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating command with event: {e}")
            return False
    
    def get_latest_command_id(
        self, 
        user_uuid: str, 
        app_slug: str, 
        riff_slug: str, 
        action: str
    ) -> Optional[str]:
        """
        Get the latest command ID for a specific action
        
        Args:
            user_uuid: User UUID
            app_slug: App slug
            riff_slug: Riff slug
            action: Action type (install, run, test, lint)
            
        Returns:
            Latest command ID or None if not found
        """
        try:
            commands = self._load_commands(user_uuid, app_slug, riff_slug)
            return commands.get(action, {}).get("latest_command_id")
        except Exception as e:
            logger.error(f"❌ Error getting latest command ID: {e}")
            return None
    
    def get_command_status(
        self, 
        user_uuid: str, 
        app_slug: str, 
        riff_slug: str, 
        action: str
    ) -> Dict[str, Any]:
        """
        Get the status of the latest command for an action
        
        Args:
            user_uuid: User UUID
            app_slug: App slug
            riff_slug: Riff slug
            action: Action type (install, run, test, lint)
            
        Returns:
            Dictionary with command status information
        """
        try:
            commands = self._load_commands(user_uuid, app_slug, riff_slug)
            
            if action not in commands or not commands[action]["commands"]:
                return {"status": "none", "message": "No commands found"}
            
            # Get the latest command
            latest_command = commands[action]["commands"][-1]
            
            return {
                "status": latest_command["status"],
                "command_id": latest_command["command_id"],
                "command": latest_command["command"],
                "sent_at": latest_command["sent_at"],
                "completed_at": latest_command.get("completed_at"),
                "exit_code": latest_command.get("exit_code"),
                "output": latest_command.get("output", "")[:200] + "..." if latest_command.get("output", "") else ""
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting command status: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_all_commands_status(
        self, 
        user_uuid: str, 
        app_slug: str, 
        riff_slug: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get status for all actions
        
        Args:
            user_uuid: User UUID
            app_slug: App slug
            riff_slug: Riff slug
            
        Returns:
            Dictionary with status for each action
        """
        try:
            result = {}
            for action in ["install", "run", "test", "lint"]:
                result[action] = self.get_command_status(user_uuid, app_slug, riff_slug, action)
            return result
        except Exception as e:
            logger.error(f"❌ Error getting all commands status: {e}")
            return {}


# Global instance
command_tracker = CommandTracker()