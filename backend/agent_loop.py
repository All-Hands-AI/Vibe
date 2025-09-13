"""
OpenHands Agent Loop Manager

This module manages OpenHands agent conversations, including:
- Initializing agent conversations with proper workspace setup
- Managing conversation state persistence
- Running conversations in background threads
- Handling GitHub branch and PR operations
"""

import os
import json
import uuid
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import requests

from pydantic import SecretStr

# OpenHands SDK imports
try:
    from openhands.sdk import (
        LLM,
        Agent,
        Conversation,
        Event,
        LLMConvertibleEvent,
        LocalFileStore,
        Message,
        TextContent,
        get_logger,
    )
    from openhands.tools import (
        BashTool,
        FileEditorTool,
        TaskTrackerTool,
    )
    OPENHANDS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"OpenHands SDK not available: {e}")
    OPENHANDS_AVAILABLE = False

logger = logging.getLogger(__name__)

class ConversationThread:
    """Represents a running conversation thread"""
    
    def __init__(self, conversation_id: str, project_id: str, thread: threading.Thread):
        self.conversation_id = conversation_id
        self.project_id = project_id
        self.thread = thread
        self.created_at = datetime.utcnow()
        self.status = "running"
        self.events: List[Event] = []
        self.error: Optional[str] = None

class AgentLoopManager:
    """Manages OpenHands agent conversations and their lifecycle"""
    
    def __init__(self, data_dir: str = "/data"):
        self.data_dir = Path(data_dir)
        self.running_conversations: Dict[str, ConversationThread] = {}
        self.lock = threading.Lock()
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🤖 AgentLoopManager initialized with data_dir: {self.data_dir}")
    
    def _get_conversation_workspace_dir(self, project_id: str, conversation_id: str) -> Path:
        """Get the workspace directory for a conversation"""
        return self.data_dir / project_id / "conversations" / conversation_id / "workspace"
    
    def _get_conversation_state_dir(self, project_id: str, conversation_id: str) -> Path:
        """Get the state directory for a conversation"""
        return self.data_dir / project_id / "conversations" / conversation_id / "state"
    
    def _setup_conversation_directories(self, project_id: str, conversation_id: str) -> tuple[Path, Path]:
        """Setup workspace and state directories for a conversation"""
        workspace_dir = self._get_conversation_workspace_dir(project_id, conversation_id)
        state_dir = self._get_conversation_state_dir(project_id, conversation_id)
        
        workspace_dir.mkdir(parents=True, exist_ok=True)
        state_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 Created directories for conversation {conversation_id}")
        logger.debug(f"  - Workspace: {workspace_dir}")
        logger.debug(f"  - State: {state_dir}")
        
        return workspace_dir, state_dir
    
    def _create_github_branch(self, repo_url: str, branch_name: str, github_token: str) -> tuple[bool, str]:
        """Create or adopt a GitHub branch"""
        try:
            # Extract owner and repo from URL
            if not repo_url or 'github.com' not in repo_url:
                return False, "Invalid GitHub URL"
            
            parts = repo_url.replace('https://github.com/', '').split('/')
            if len(parts) < 2:
                return False, "Cannot parse GitHub URL"
            
            owner, repo = parts[0], parts[1]
            
            headers = {
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'OpenVibe-Backend/1.0'
            }
            
            # Get the default branch SHA
            default_branch_response = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}',
                headers=headers,
                timeout=10
            )
            
            if default_branch_response.status_code != 200:
                return False, f"Failed to get repository info: {default_branch_response.status_code}"
            
            repo_data = default_branch_response.json()
            default_branch = repo_data.get('default_branch', 'main')
            
            # Get the SHA of the default branch
            branch_response = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{default_branch}',
                headers=headers,
                timeout=10
            )
            
            if branch_response.status_code != 200:
                return False, f"Failed to get default branch SHA: {branch_response.status_code}"
            
            branch_data = branch_response.json()
            base_sha = branch_data['object']['sha']
            
            # Check if branch already exists
            check_response = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch_name}',
                headers=headers,
                timeout=10
            )
            
            if check_response.status_code == 200:
                logger.info(f"✅ Branch '{branch_name}' already exists, adopting it")
                return True, f"Adopted existing branch '{branch_name}'"
            
            # Create new branch
            create_data = {
                'ref': f'refs/heads/{branch_name}',
                'sha': base_sha
            }
            
            create_response = requests.post(
                f'https://api.github.com/repos/{owner}/{repo}/git/refs',
                headers=headers,
                json=create_data,
                timeout=10
            )
            
            if create_response.status_code == 201:
                logger.info(f"✅ Created new branch '{branch_name}'")
                return True, f"Created new branch '{branch_name}'"
            else:
                return False, f"Failed to create branch: {create_response.status_code} - {create_response.text}"
        
        except Exception as e:
            logger.error(f"💥 Error creating GitHub branch: {str(e)}")
            return False, f"Error creating branch: {str(e)}"
    
    def _create_github_pr(self, repo_url: str, branch_name: str, title: str, github_token: str) -> tuple[bool, str, Optional[int]]:
        """Create or adopt a GitHub PR"""
        try:
            # Extract owner and repo from URL
            parts = repo_url.replace('https://github.com/', '').split('/')
            if len(parts) < 2:
                return False, "Cannot parse GitHub URL", None
            
            owner, repo = parts[0], parts[1]
            
            headers = {
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'OpenVibe-Backend/1.0'
            }
            
            # Get the default branch
            repo_response = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}',
                headers=headers,
                timeout=10
            )
            
            if repo_response.status_code != 200:
                return False, f"Failed to get repository info: {repo_response.status_code}", None
            
            repo_data = repo_response.json()
            default_branch = repo_data.get('default_branch', 'main')
            
            # Check if PR already exists
            prs_response = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}/pulls',
                headers=headers,
                params={'head': f'{owner}:{branch_name}', 'state': 'open'},
                timeout=10
            )
            
            if prs_response.status_code == 200:
                prs_data = prs_response.json()
                if prs_data:
                    pr_number = prs_data[0]['number']
                    logger.info(f"✅ PR #{pr_number} already exists for branch '{branch_name}', adopting it")
                    return True, f"Adopted existing PR #{pr_number}", pr_number
            
            # Create new PR
            pr_data = {
                'title': title,
                'head': branch_name,
                'base': default_branch,
                'body': f"Automated PR created for conversation.\n\nBranch: `{branch_name}`\nCreated: {datetime.utcnow().isoformat()}Z",
                'draft': True
            }
            
            create_response = requests.post(
                f'https://api.github.com/repos/{owner}/{repo}/pulls',
                headers=headers,
                json=pr_data,
                timeout=10
            )
            
            if create_response.status_code == 201:
                pr_data = create_response.json()
                pr_number = pr_data['number']
                logger.info(f"✅ Created new PR #{pr_number}")
                return True, f"Created new PR #{pr_number}", pr_number
            else:
                return False, f"Failed to create PR: {create_response.status_code} - {create_response.text}", None
        
        except Exception as e:
            logger.error(f"💥 Error creating GitHub PR: {str(e)}")
            return False, f"Error creating PR: {str(e)}", None
    
    def _create_llm(self, api_key: str) -> Optional[LLM]:
        """Create an LLM instance"""
        if not OPENHANDS_AVAILABLE:
            logger.error("❌ OpenHands SDK not available")
            return None
        
        try:
            return LLM(
                model="litellm_proxy/anthropic/claude-sonnet-4-20250514",
                base_url="https://llm-proxy.eval.all-hands.dev",
                api_key=SecretStr(api_key),
            )
        except Exception as e:
            logger.error(f"💥 Error creating LLM: {str(e)}")
            return None
    
    def _create_agent(self, llm: LLM, workspace_dir: Path) -> Optional[Agent]:
        """Create an agent with tools"""
        if not OPENHANDS_AVAILABLE:
            logger.error("❌ OpenHands SDK not available")
            return None
        
        try:
            tools = [
                BashTool.create(working_dir=str(workspace_dir)),
                FileEditorTool.create(),
                TaskTrackerTool.create(save_dir=str(workspace_dir)),
            ]
            
            return Agent(llm=llm, tools=tools)
        except Exception as e:
            logger.error(f"💥 Error creating agent: {str(e)}")
            return None
    
    def _conversation_callback(self, conversation_id: str, event: Event):
        """Callback for conversation events"""
        with self.lock:
            if conversation_id in self.running_conversations:
                self.running_conversations[conversation_id].events.append(event)
                logger.debug(f"📝 Event recorded for conversation {conversation_id}: {type(event).__name__}")
    
    def _run_conversation_thread(self, conversation_id: str, project_id: str, 
                                initial_message: str, api_key: str,
                                repo_url: Optional[str] = None, github_token: Optional[str] = None):
        """Run a conversation in a background thread"""
        try:
            logger.info(f"🚀 Starting conversation thread {conversation_id}")
            
            # Setup directories
            workspace_dir, state_dir = self._setup_conversation_directories(project_id, conversation_id)
            
            # Create LLM and agent
            llm = self._create_llm(api_key)
            if not llm:
                raise Exception("Failed to create LLM")
            
            agent = self._create_agent(llm, workspace_dir)
            if not agent:
                raise Exception("Failed to create agent")
            
            # Setup file store for persistence
            file_store = LocalFileStore(str(state_dir))
            
            # Create conversation with callback
            callback = lambda event: self._conversation_callback(conversation_id, event)
            conversation = Conversation(
                agent=agent,
                callbacks=[callback],
                persist_filestore=file_store,
                conversation_id=conversation_id,
            )
            
            # Send initial message
            conversation.send_message(
                Message(
                    role="user",
                    content=[TextContent(text=initial_message)]
                )
            )
            
            # Run conversation
            conversation.run()
            
            # Update status
            with self.lock:
                if conversation_id in self.running_conversations:
                    self.running_conversations[conversation_id].status = "completed"
            
            logger.info(f"✅ Conversation {conversation_id} completed successfully")
            
        except Exception as e:
            logger.error(f"💥 Error in conversation thread {conversation_id}: {str(e)}")
            with self.lock:
                if conversation_id in self.running_conversations:
                    self.running_conversations[conversation_id].status = "error"
                    self.running_conversations[conversation_id].error = str(e)
    
    def start_conversation(self, project_id: str, initial_message: str, api_key: str,
                          repo_url: Optional[str] = None, github_token: Optional[str] = None,
                          conversation_id: Optional[str] = None) -> tuple[bool, str, str]:
        """
        Start a new conversation
        
        Returns:
            tuple: (success, message, conversation_id)
        """
        if not OPENHANDS_AVAILABLE:
            return False, "OpenHands SDK not available", ""
        
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        logger.info(f"🎯 Starting conversation {conversation_id} for project {project_id}")
        
        # Create GitHub branch if repo_url and github_token provided
        branch_name = None
        pr_number = None
        if repo_url and github_token:
            branch_name = f"conversation-{conversation_id[:8]}"
            success, message = self._create_github_branch(repo_url, branch_name, github_token)
            if not success:
                logger.warning(f"⚠️ Failed to create GitHub branch: {message}")
            else:
                # Create PR
                success, pr_message, pr_number = self._create_github_pr(
                    repo_url, branch_name, f"Conversation {conversation_id[:8]}", github_token
                )
                if not success:
                    logger.warning(f"⚠️ Failed to create GitHub PR: {pr_message}")
        
        # Start conversation thread
        thread = threading.Thread(
            target=self._run_conversation_thread,
            args=(conversation_id, project_id, initial_message, api_key, repo_url, github_token),
            daemon=True
        )
        
        # Track the conversation
        with self.lock:
            self.running_conversations[conversation_id] = ConversationThread(
                conversation_id=conversation_id,
                project_id=project_id,
                thread=thread
            )
        
        thread.start()
        
        result_message = f"Started conversation {conversation_id}"
        if branch_name:
            result_message += f" with branch '{branch_name}'"
        if pr_number:
            result_message += f" and PR #{pr_number}"
        
        return True, result_message, conversation_id
    
    def get_conversation_status(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a conversation"""
        with self.lock:
            if conversation_id not in self.running_conversations:
                return None
            
            conv_thread = self.running_conversations[conversation_id]
            return {
                'conversation_id': conv_thread.conversation_id,
                'project_id': conv_thread.project_id,
                'status': conv_thread.status,
                'created_at': conv_thread.created_at.isoformat(),
                'is_alive': conv_thread.thread.is_alive(),
                'event_count': len(conv_thread.events),
                'error': conv_thread.error
            }
    
    def get_conversation_events(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get events for a conversation"""
        with self.lock:
            if conversation_id not in self.running_conversations:
                return []
            
            conv_thread = self.running_conversations[conversation_id]
            events = []
            
            for event in conv_thread.events:
                event_data = {
                    'type': type(event).__name__,
                    'timestamp': getattr(event, 'timestamp', datetime.utcnow().isoformat()),
                }
                
                # Add event-specific data
                if hasattr(event, 'to_dict'):
                    event_data.update(event.to_dict())
                elif hasattr(event, '__dict__'):
                    event_data.update({k: v for k, v in event.__dict__.items() 
                                     if not k.startswith('_')})
                
                events.append(event_data)
            
            return events
    
    def send_message_to_conversation(self, conversation_id: str, message: str) -> tuple[bool, str]:
        """Send a message to an existing conversation"""
        # This would require modifying the conversation thread to accept new messages
        # For now, return not implemented
        return False, "Sending messages to existing conversations not yet implemented"
    
    def list_conversations(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all conversations, optionally filtered by project"""
        with self.lock:
            conversations = []
            for conv_id, conv_thread in self.running_conversations.items():
                if project_id is None or conv_thread.project_id == project_id:
                    conversations.append({
                        'conversation_id': conv_thread.conversation_id,
                        'project_id': conv_thread.project_id,
                        'status': conv_thread.status,
                        'created_at': conv_thread.created_at.isoformat(),
                        'is_alive': conv_thread.thread.is_alive(),
                        'event_count': len(conv_thread.events),
                        'error': conv_thread.error
                    })
            return conversations
    
    def cleanup_finished_conversations(self):
        """Clean up finished conversation threads"""
        with self.lock:
            to_remove = []
            for conv_id, conv_thread in self.running_conversations.items():
                if not conv_thread.thread.is_alive() and conv_thread.status in ['completed', 'error']:
                    to_remove.append(conv_id)
            
            for conv_id in to_remove:
                logger.info(f"🧹 Cleaning up finished conversation {conv_id}")
                del self.running_conversations[conv_id]