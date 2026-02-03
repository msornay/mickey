"""Tests for Mickey CLI."""

from pathlib import Path
from unittest.mock import patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mickey import (
    Agent,
    load_agents,
    save_agents,
    cmd_create,
    cmd_list,
    cmd_run,
    cmd_delete,
    main,
)


# === Fixtures ===
@pytest.fixture
def temp_mickey_home(tmp_path, monkeypatch):
    """Set up temporary Mickey home directory."""
    mickey_home = tmp_path / ".mickey"
    workspaces = mickey_home / "workspaces"
    agents_file = mickey_home / "agents.json"

    monkeypatch.setattr("mickey.MICKEY_HOME", mickey_home)
    monkeypatch.setattr("mickey.WORKSPACES_DIR", workspaces)
    monkeypatch.setattr("mickey.AGENTS_FILE", agents_file)

    mickey_home.mkdir(parents=True)
    workspaces.mkdir(parents=True)

    return mickey_home


@pytest.fixture
def sample_agent():
    """Create a sample agent for testing."""
    return Agent(
        name="test-agent",
        repo_url="https://github.com/user/repo.git",
        workspace_path="/tmp/workspaces/test-agent",
        sandbox_name="mickey-test-agent",
        status="ready",
        created_at="2026-02-03T10:30:00",
    )


# === Agent Model Tests ===
class TestAgent:
    def test_agent_creation(self):
        agent = Agent(
            name="test",
            repo_url="https://github.com/user/repo.git",
            workspace_path="/tmp/test",
            sandbox_name="mickey-test",
        )
        assert agent.name == "test"
        assert agent.status == "ready"
        assert agent.created_at != ""

    def test_agent_to_dict(self, sample_agent):
        data = sample_agent.to_dict()
        assert data["name"] == "test-agent"
        assert data["repo_url"] == "https://github.com/user/repo.git"

    def test_agent_from_dict(self):
        data = {
            "name": "test",
            "repo_url": "https://github.com/user/repo.git",
            "workspace_path": "/tmp/test",
            "sandbox_name": "mickey-test",
            "status": "ready",
            "created_at": "2026-02-03T10:30:00",
        }
        agent = Agent.from_dict(data)
        assert agent.name == "test"
        assert agent.repo_url == "https://github.com/user/repo.git"


# === Storage Tests ===
class TestStorage:
    def test_load_agents_empty(self, temp_mickey_home):
        agents = load_agents()
        assert agents == {}

    def test_save_and_load_agents(self, temp_mickey_home, sample_agent):
        agents = {"test-agent": sample_agent}
        save_agents(agents)

        loaded = load_agents()
        assert "test-agent" in loaded
        assert loaded["test-agent"].name == "test-agent"
        assert loaded["test-agent"].repo_url == sample_agent.repo_url

    def test_load_agents_creates_dirs(self, temp_mickey_home, sample_agent):
        # Save should create directories
        save_agents({"test": sample_agent})
        assert temp_mickey_home.exists()


# === Command Tests ===
class TestCreateCommand:
    @patch("mickey.git_clone")
    @patch("mickey.sandbox_create")
    def test_create_success(self, mock_sandbox, mock_clone, temp_mickey_home):
        mock_clone.return_value = True
        mock_sandbox.return_value = True

        result = cmd_create("test-agent", "https://github.com/user/repo.git")

        assert result == 0
        mock_clone.assert_called_once()
        mock_sandbox.assert_called_once()

        agents = load_agents()
        assert "test-agent" in agents

    @patch("mickey.git_clone")
    @patch("mickey.sandbox_create")
    def test_create_duplicate(self, mock_sandbox, mock_clone, temp_mickey_home, sample_agent):
        mock_clone.return_value = True
        mock_sandbox.return_value = True

        # Save existing agent
        save_agents({"test-agent": sample_agent})

        result = cmd_create("test-agent", "https://github.com/user/other.git")
        assert result == 1

    @patch("mickey.git_clone")
    def test_create_clone_fails(self, mock_clone, temp_mickey_home):
        mock_clone.return_value = False

        result = cmd_create("test-agent", "https://github.com/user/repo.git")
        assert result == 1

    @patch("mickey.git_clone")
    @patch("mickey.sandbox_create")
    def test_create_sandbox_fails_cleanup(self, mock_sandbox, mock_clone, temp_mickey_home):
        mock_clone.return_value = True
        mock_sandbox.return_value = False

        result = cmd_create("test-agent", "https://github.com/user/repo.git")
        assert result == 1

        # Verify agent was not saved
        agents = load_agents()
        assert "test-agent" not in agents


class TestListCommand:
    @patch("mickey.sandbox_list")
    def test_list_empty(self, mock_sandbox_list, temp_mickey_home, capsys):
        mock_sandbox_list.return_value = []

        result = cmd_list()
        assert result == 0

        captured = capsys.readouterr()
        assert "No agents found" in captured.out

    @patch("mickey.sandbox_list")
    def test_list_with_agents(self, mock_sandbox_list, temp_mickey_home, sample_agent, capsys):
        mock_sandbox_list.return_value = [
            {"name": "mickey-test-agent", "status": "running"}
        ]
        save_agents({"test-agent": sample_agent})

        result = cmd_list()
        assert result == 0

        captured = capsys.readouterr()
        assert "test-agent" in captured.out


class TestRunCommand:
    @patch("mickey.sandbox_exists")
    @patch("mickey.sandbox_run")
    def test_run_success(self, mock_run, mock_exists, temp_mickey_home, sample_agent, tmp_path):
        mock_exists.return_value = True
        mock_run.return_value = 0

        # Create system prompt file
        system_prompt = tmp_path / "mickey_system_promt.txt"
        system_prompt.write_text("Test system prompt")

        import mickey
        original = mickey.SYSTEM_PROMPT_FILE
        mickey.SYSTEM_PROMPT_FILE = system_prompt

        try:
            save_agents({"test-agent": sample_agent})
            result = cmd_run("test-agent", "test prompt")
            assert result == 0
            mock_run.assert_called_once()
        finally:
            mickey.SYSTEM_PROMPT_FILE = original

    def test_run_agent_not_found(self, temp_mickey_home):
        result = cmd_run("nonexistent", "test prompt")
        assert result == 1

    @patch("mickey.sandbox_exists")
    def test_run_sandbox_not_found(self, mock_exists, temp_mickey_home, sample_agent):
        mock_exists.return_value = False
        save_agents({"test-agent": sample_agent})

        result = cmd_run("test-agent", "test prompt")
        assert result == 1


class TestDeleteCommand:
    @patch("mickey.sandbox_remove")
    @patch("builtins.input", return_value="y")
    def test_delete_success(self, mock_input, mock_remove, temp_mickey_home, sample_agent):
        mock_remove.return_value = True
        save_agents({"test-agent": sample_agent})

        result = cmd_delete("test-agent")
        assert result == 0

        agents = load_agents()
        assert "test-agent" not in agents

    @patch("mickey.sandbox_remove")
    def test_delete_force(self, mock_remove, temp_mickey_home, sample_agent):
        mock_remove.return_value = True
        save_agents({"test-agent": sample_agent})

        result = cmd_delete("test-agent", force=True)
        assert result == 0

    @patch("builtins.input", return_value="n")
    def test_delete_abort(self, mock_input, temp_mickey_home, sample_agent, capsys):
        save_agents({"test-agent": sample_agent})

        result = cmd_delete("test-agent")
        assert result == 0

        captured = capsys.readouterr()
        assert "Aborted" in captured.out

        # Agent should still exist
        agents = load_agents()
        assert "test-agent" in agents

    def test_delete_not_found(self, temp_mickey_home):
        result = cmd_delete("nonexistent", force=True)
        assert result == 1


# === CLI Entry Point Tests ===
class TestMain:
    def test_help(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["mickey", "--help"])
        result = main()
        assert result == 0

        captured = capsys.readouterr()
        assert "Mickey" in captured.out
        assert "create" in captured.out

    def test_no_args(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["mickey"])
        result = main()
        assert result == 0

        captured = capsys.readouterr()
        assert "Usage" in captured.out

    def test_unknown_command(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["mickey", "unknown"])
        result = main()
        assert result == 1

        captured = capsys.readouterr()
        assert "Unknown command" in captured.err

    def test_create_missing_args(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["mickey", "create", "only-name"])
        result = main()
        assert result == 1

    def test_run_missing_args(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["mickey", "run", "agent-name"])
        result = main()
        assert result == 1

    def test_delete_missing_args(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["mickey", "delete"])
        result = main()
        assert result == 1
