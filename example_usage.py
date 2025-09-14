#!/usr/bin/env python3
"""
Example usage of loaded microagents.
This demonstrates how to use the microagent content in your application.
"""

import sys
from pathlib import Path

# Ensure we import from the installed package
venv_site_packages = Path(__file__).parent / ".venv" / "lib" / "python3.12" / "site-packages"
if venv_site_packages.exists():
    sys.path.insert(0, str(venv_site_packages))

from microagent_loader import load_microagents

def example_usage():
    """Example of how to use loaded microagents in your application."""
    print("📖 Example: Using Microagents in Your Application")
    print("=" * 55)
    
    # Load the microagents
    repo_agents, knowledge_agents = load_microagents()
    
    # Example 1: Access repository instructions
    if 'repo' in repo_agents:
        repo_agent = repo_agents['repo']
        print(f"\n🏗️  Repository Agent: {repo_agent.name}")
        print(f"📝 Instructions for developers:")
        print("-" * 30)
        
        # Extract key information from the content
        content = repo_agent.content
        
        # Find important sections
        if "IMPORTANT" in content:
            important_start = content.find("<IMPORTANT>")
            important_end = content.find("</IMPORTANT>")
            if important_start != -1 and important_end != -1:
                important_text = content[important_start:important_end + len("</IMPORTANT>")]
                print("⚠️  Critical Information:")
                print(important_text)
        
        # Find testing commands
        if "Test and Lint Commands" in content:
            print("\n🧪 Available Commands:")
            lines = content.split('\n')
            in_commands = False
            for line in lines:
                if "Test and Lint Commands" in line:
                    in_commands = True
                    continue
                if in_commands and line.strip():
                    if line.startswith('**') or line.startswith('- '):
                        print(f"  {line}")
    
    # Example 2: Use microagent content for configuration
    print(f"\n⚙️  Configuration extracted from microagents:")
    print(f"  • Total agents loaded: {len(repo_agents) + len(knowledge_agents)}")
    print(f"  • Repository agents: {list(repo_agents.keys())}")
    print(f"  • Knowledge agents: {list(knowledge_agents.keys())}")
    
    # Example 3: Access agent metadata
    for name, agent in repo_agents.items():
        print(f"\n📊 Agent '{name}' metadata:")
        print(f"  • Type: {agent.type}")
        print(f"  • Source file: {Path(agent.source).name if agent.source else 'N/A'}")
        print(f"  • Content size: {len(agent.content)} characters")
        print(f"  • Has MCP tools: {'Yes' if agent.mcp_tools else 'No'}")

if __name__ == "__main__":
    example_usage()