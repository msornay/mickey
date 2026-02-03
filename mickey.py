#!/usr/bin/env python3
"""Mickey - Manage Claude Code agents in Docker sandboxes."""

import json
import subprocess
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path

# === Configuration ===
MICKEY_HOME = Path.home() / ".mickey"
WORKSPACES_DIR = MICKEY_HOME / "workspaces"
AGENTS_FILE = MICKEY_HOME / "agents.json"
SYSTEM_PROMPT_FILE = Path(__file__).parent / "mickey_system_promt.txt"


# === Agent Model ===
@dataclass
class Agent:
    name: str
    repo_url: str
    workspace_path: str
    sandbox_name: str
    status: str = "ready"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def from_dict(cls, data: dict) -> "Agent":
        return cls(**data)

    def to_dict(self) -> dict:
        return asdict(self)


# === Storage Functions ===
def ensure_dirs():
    """Create necessary directories if they don't exist."""
    MICKEY_HOME.mkdir(parents=True, exist_ok=True)
    WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)


def load_agents() -> dict[str, Agent]:
    """Load agents from JSON file."""
    if not AGENTS_FILE.exists():
        return {}
    with open(AGENTS_FILE) as f:
        data = json.load(f)
    return {name: Agent.from_dict(agent) for name, agent in data.items()}


def save_agents(agents: dict[str, Agent]):
    """Save agents to JSON file."""
    ensure_dirs()
    data = {name: agent.to_dict() for name, agent in agents.items()}
    with open(AGENTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


# === Docker Sandbox Functions ===
def sandbox_create(name: str, workspace: str) -> bool:
    """Create a Docker sandbox for the agent."""
    result = subprocess.run(
        ["docker", "sandbox", "create", "--name", name, "claude", workspace],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error creating sandbox: {result.stderr}", file=sys.stderr)
        return False
    return True


def sandbox_run(name: str, prompt: str, system_prompt: str) -> int:
    """Run a command in the sandbox with streaming output."""
    result = subprocess.run(
        [
            "docker",
            "sandbox",
            "run",
            name,
            "--",
            "--system-prompt",
            system_prompt,
            "-p",
            prompt,
        ],
    )
    return result.returncode


def sandbox_list() -> list[dict]:
    """List all Docker sandboxes."""
    result = subprocess.run(
        ["docker", "sandbox", "ls", "--json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        return data.get("vms", [])
    except json.JSONDecodeError:
        return []


def sandbox_exists(name: str) -> bool:
    """Check if a sandbox exists."""
    sandboxes = sandbox_list()
    return any(s.get("name") == name for s in sandboxes)


def sandbox_remove(name: str) -> bool:
    """Remove a Docker sandbox."""
    result = subprocess.run(
        ["docker", "sandbox", "rm", name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error removing sandbox: {result.stderr}", file=sys.stderr)
        return False
    return True


# === Git Functions ===
def git_clone(repo_url: str, destination: Path) -> bool:
    """Clone a git repository."""
    result = subprocess.run(
        ["git", "clone", repo_url, str(destination)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error cloning repository: {result.stderr}", file=sys.stderr)
        return False
    return True


# === Commands ===
def cmd_create(name: str, repo_url: str) -> int:
    """Create a new agent with a Docker sandbox."""
    ensure_dirs()
    agents = load_agents()

    # Check if agent already exists
    if name in agents:
        print(f"Error: Agent '{name}' already exists", file=sys.stderr)
        return 1

    workspace = WORKSPACES_DIR / name
    sandbox_name = f"mickey-{name}"

    # Check if workspace already exists
    if workspace.exists():
        print(f"Error: Workspace directory already exists: {workspace}", file=sys.stderr)
        return 1

    # Clone the repository
    print(f"Cloning {repo_url}...")
    if not git_clone(repo_url, workspace):
        return 1

    # Create Docker sandbox
    print(f"Creating sandbox '{sandbox_name}'...")
    if not sandbox_create(sandbox_name, str(workspace)):
        # Cleanup on failure
        import shutil

        shutil.rmtree(workspace, ignore_errors=True)
        return 1

    # Save agent
    agent = Agent(
        name=name,
        repo_url=repo_url,
        workspace_path=str(workspace),
        sandbox_name=sandbox_name,
    )
    agents[name] = agent
    save_agents(agents)

    print(f"Agent '{name}' created successfully")
    return 0


def cmd_list() -> int:
    """List all agents with their status."""
    agents = load_agents()

    if not agents:
        print("No agents found")
        return 0

    # Get sandbox status
    sandboxes = sandbox_list()
    sandbox_status = {s.get("name"): s.get("status", "unknown") for s in sandboxes}

    # Try to use rich for nice table output
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Mickey Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Repository")
        table.add_column("Sandbox Status", style="green")
        table.add_column("Created")

        for agent in agents.values():
            status = sandbox_status.get(agent.sandbox_name, "not found")
            created = agent.created_at[:10] if agent.created_at else "unknown"
            table.add_row(agent.name, agent.repo_url, status, created)

        console.print(table)

    except ImportError:
        # Fallback to simple output
        print(f"{'Name':<20} {'Repository':<40} {'Status':<15} {'Created':<12}")
        print("-" * 90)
        for agent in agents.values():
            status = sandbox_status.get(agent.sandbox_name, "not found")
            created = agent.created_at[:10] if agent.created_at else "unknown"
            print(f"{agent.name:<20} {agent.repo_url:<40} {status:<15} {created:<12}")

    return 0


def cmd_run(name: str, prompt: str) -> int:
    """Run a task on an agent."""
    agents = load_agents()

    if name not in agents:
        print(f"Error: Agent '{name}' not found", file=sys.stderr)
        return 1

    agent = agents[name]

    # Check sandbox exists
    if not sandbox_exists(agent.sandbox_name):
        print(f"Error: Sandbox '{agent.sandbox_name}' not found", file=sys.stderr)
        return 1

    # Load system prompt
    if not SYSTEM_PROMPT_FILE.exists():
        print(f"Error: System prompt file not found: {SYSTEM_PROMPT_FILE}", file=sys.stderr)
        return 1

    system_prompt = SYSTEM_PROMPT_FILE.read_text()

    print(f"Running task on agent '{name}'...")
    return sandbox_run(agent.sandbox_name, prompt, system_prompt)


def cmd_delete(name: str, force: bool = False) -> int:
    """Delete an agent and clean up resources."""
    agents = load_agents()

    if name not in agents:
        print(f"Error: Agent '{name}' not found", file=sys.stderr)
        return 1

    agent = agents[name]

    # Confirm deletion unless force flag is set
    if not force:
        response = input(f"Delete agent '{name}' and all associated data? [y/N] ")
        if response.lower() != "y":
            print("Aborted")
            return 0

    # Remove sandbox
    print(f"Removing sandbox '{agent.sandbox_name}'...")
    sandbox_remove(agent.sandbox_name)

    # Remove workspace
    workspace = Path(agent.workspace_path)
    if workspace.exists():
        import shutil

        print(f"Removing workspace '{workspace}'...")
        shutil.rmtree(workspace)

    # Remove from agents
    del agents[name]
    save_agents(agents)

    print(f"Agent '{name}' deleted successfully")
    return 0


# === CLI Entry Point ===
def print_usage():
    """Print usage information."""
    print("""Mickey - Manage Claude Code agents in Docker sandboxes

Usage:
    mickey create <name> <repo-url>    Clone repo and create Docker sandbox
    mickey list                        Show all agents with status
    mickey run <name> "<prompt>"       Execute task using system prompt
    mickey delete <name> [--force]     Remove agent and cleanup

Examples:
    mickey create my-agent https://github.com/user/repo.git
    mickey list
    mickey run my-agent "Add a hello world endpoint"
    mickey delete my-agent
""")


def main() -> int:
    """Main entry point."""
    args = sys.argv[1:]

    if not args or args[0] in ["-h", "--help", "help"]:
        print_usage()
        return 0

    command = args[0]

    if command == "create":
        if len(args) < 3:
            print("Error: create requires <name> and <repo-url>", file=sys.stderr)
            print("Usage: mickey create <name> <repo-url>", file=sys.stderr)
            return 1
        return cmd_create(args[1], args[2])

    elif command == "list":
        return cmd_list()

    elif command == "run":
        if len(args) < 3:
            print("Error: run requires <name> and <prompt>", file=sys.stderr)
            print('Usage: mickey run <name> "<prompt>"', file=sys.stderr)
            return 1
        return cmd_run(args[1], args[2])

    elif command == "delete":
        if len(args) < 2:
            print("Error: delete requires <name>", file=sys.stderr)
            print("Usage: mickey delete <name> [--force]", file=sys.stderr)
            return 1
        force = "--force" in args or "-f" in args
        return cmd_delete(args[1], force)

    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print_usage()
        return 1


if __name__ == "__main__":
    sys.exit(main())
