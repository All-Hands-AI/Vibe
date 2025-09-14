#!/usr/bin/env python3
"""
Production-ready microagent loader using the OpenHands Agent SDK.
This script loads microagents from .openhands/microagents/ directory.
"""

import sys
from pathlib import Path

# Ensure we import from the installed package, not the system openhands
venv_site_packages = Path(__file__).parent / ".venv" / "lib" / "python3.12" / "site-packages"
if venv_site_packages.exists():
    sys.path.insert(0, str(venv_site_packages))

from openhands.sdk.context.microagents import load_microagents_from_dir
from openhands.sdk.logger import get_logger

def load_microagents(microagents_dir_path: str = None):
    """
    Load microagents from the specified directory.
    
    Args:
        microagents_dir_path: Path to microagents directory. If None, uses .openhands/microagents
        
    Returns:
        tuple: (repo_agents, knowledge_agents) dictionaries
    """
    logger = get_logger(__name__)
    
    if microagents_dir_path is None:
        microagents_dir = Path(__file__).parent / ".openhands" / "microagents"
    else:
        microagents_dir = Path(microagents_dir_path)
    
    if not microagents_dir.exists():
        logger.warning(f"Microagents directory not found: {microagents_dir}")
        return {}, {}
    
    logger.info(f"Loading microagents from: {microagents_dir}")
    
    try:
        repo_agents, knowledge_agents = load_microagents_from_dir(microagents_dir)
        logger.info(f"Successfully loaded {len(repo_agents)} repo agents and {len(knowledge_agents)} knowledge agents")
        return repo_agents, knowledge_agents
    except Exception as e:
        logger.error(f"Failed to load microagents: {e}")
        raise

def main():
    """Main function to demonstrate microagent loading."""
    print("🤖 OpenHands Agent SDK - Microagent Loader")
    print("=" * 50)
    
    try:
        repo_agents, knowledge_agents = load_microagents()
        
        print(f"✅ Loaded {len(repo_agents) + len(knowledge_agents)} microagents")
        
        if repo_agents:
            print(f"\n📁 Repository Agents ({len(repo_agents)}):")
            for name, agent in repo_agents.items():
                print(f"  • {name} - {agent.type} ({len(agent.content)} chars)")
                print(f"    Source: {agent.source}")
        
        if knowledge_agents:
            print(f"\n🧠 Knowledge Agents ({len(knowledge_agents)}):")
            for name, agent in knowledge_agents.items():
                print(f"  • {name} - {agent.type} ({len(agent.content)} chars)")
                print(f"    Source: {agent.source}")
        
        if not repo_agents and not knowledge_agents:
            print("⚠️  No microagents found.")
            
        return repo_agents, knowledge_agents
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}, {}

if __name__ == "__main__":
    main()