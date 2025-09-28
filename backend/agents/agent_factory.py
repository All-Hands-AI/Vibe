"""
Agent factory for creating agents with proper tool configuration and system prompts.
Handles the creation of tools and agents with runtime-appropriate settings.
"""

import os
import sys
from typing import List
from utils.logging import get_logger
from .runtime_handler import RuntimeHandler

# Add the site-packages to the path for openhands imports
sys.path.insert(0, ".venv/lib/python3.12/site-packages")

from openhands.sdk import (
    Agent,
    LLM,
    AgentContext,
    ToolSpec,
)

# Import tools to register them automatically
from openhands.tools.str_replace_editor import FileEditorTool  # noqa: F401
from openhands.tools.task_tracker import TaskTrackerTool  # noqa: F401
from openhands.tools.execute_bash import BashTool  # noqa: F401

logger = get_logger(__name__)


def create_tools_with_validation(runtime_handler: RuntimeHandler) -> List[ToolSpec]:
    """
    Create tools with proper path validation and setup.

    Args:
        runtime_handler: RuntimeHandler instance with configuration

    Returns:
        List of configured ToolSpec instances
    """
    # Register default tools first
    from openhands.sdk.preset.default import register_default_tools

    register_default_tools(enable_browser=False)
    logger.info("✅ Registered default tools")

    # Get runtime-appropriate paths
    paths = runtime_handler.get_runtime_paths()
    project_dir = paths["project_dir"]
    tasks_dir = paths["tasks_dir"]

    runtime_handler.log_runtime_info("for tool creation")

    tools = []

    try:
        # BashTool - work in project directory
        tools.append(ToolSpec(name="BashTool", params={"working_dir": project_dir}))
        logger.info(f"✅ Created BashTool with working_dir: {project_dir}")

        # FileEditorTool - workspace root directory
        tools.append(
            ToolSpec(name="FileEditorTool", params={"workspace_root": project_dir})
        )
        logger.info(f"✅ Created FileEditorTool with workspace_root: {project_dir}")

        # TaskTrackerTool - save to tasks directory
        tools.append(ToolSpec(name="TaskTrackerTool", params={"save_dir": tasks_dir}))
        logger.info(f"✅ Created TaskTrackerTool with save_dir: {tasks_dir}")

    except Exception as e:
        logger.error(f"❌ Failed to create tools: {e}")
        raise

    return tools


def load_system_prompt(runtime_handler: RuntimeHandler) -> str:
    """
    Load system prompt from file and combine with workspace-specific information.

    Args:
        runtime_handler: RuntimeHandler instance with configuration

    Returns:
        Complete system prompt string
    """
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to backend directory, then to prompts
    prompt_file = os.path.join(
        os.path.dirname(script_dir), "prompts", "system_prompt.txt"
    )

    # Load the base system prompt from file
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            base_prompt = f.read()
    except FileNotFoundError:
        logger.error(f"❌ System prompt file not found: {prompt_file}")
        # Fallback to a minimal prompt if file is missing
        base_prompt = "You are OpenHands agent, a helpful AI assistant that can interact with a computer to solve tasks."
    except Exception as e:
        logger.error(f"❌ Error loading system prompt file: {e}")
        base_prompt = "You are OpenHands agent, a helpful AI assistant that can interact with a computer to solve tasks."

    # Get runtime-appropriate workspace path
    paths = runtime_handler.get_runtime_paths()
    agent_workspace_path = paths["agent_workspace_path"]

    # Add workspace-specific information
    workspace_info = f"""

WORKSPACE INFORMATION:
You are working in a workspace located at: {agent_workspace_path}/project/

<IMPORTANT>
Do all your work in the directory {agent_workspace_path}/project/
</IMPORTANT>

This workspace has a git repository in it.

When using the FileEditor tool, always use absolute paths.

<WORKFLOW>
Only work on the current branch. Push to its analog on the remote branch.

<IMPORTANT>
COMMIT AND PUSH your work whenever you've made an improvement. DO NOT wait for the user to tell you to push.
</IMPORTANT>

Whenever you push, ALWAYS update the PR title and description, unless you're sure they don't need updating.
PR title should ALWAYS begin with [Riff $riffname] where $riffname is the name of the current riff.
For subsequent pushes, update the PR title and description as necessary, especially if they're currently blank.

For PR descriptions: keep it short!
</WORKFLOW>"""

    return base_prompt + workspace_info


def create_agent(llm: LLM, runtime_handler: RuntimeHandler) -> Agent:
    """
    Create an agent with development tools and workspace configuration.

    Args:
        llm: LLM instance from openhands-sdk
        runtime_handler: RuntimeHandler instance with configuration

    Returns:
        Configured Agent instance
    """
    # Create tools with validation
    tools = create_tools_with_validation(runtime_handler)

    # Load the complete system prompt
    system_prompt = load_system_prompt(runtime_handler)

    # Create agent context with the complete system prompt as suffix
    # This will be appended to the default OpenHands system prompt
    agent_context = AgentContext(system_message_suffix=system_prompt)

    # Use built-in Agent with built-in system prompt template
    return Agent(
        llm=llm,
        tools=tools,
        agent_context=agent_context,
    )
