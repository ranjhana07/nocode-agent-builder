from __future__ import annotations

from typer.testing import CliRunner

from nocode_agent.cli import app

runner = CliRunner()


def test_cli_lists_all_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("ingest", "search", "ask", "run", "eval", "serve", "platform", "doctor", "dataset"):
        assert command in result.output


def test_eval_has_retrieval_and_agent_subcommands() -> None:
    result = runner.invoke(app, ["eval", "--help"])
    assert "retrieval" in result.output and "agent" in result.output


def test_run_help_mentions_dry_run() -> None:
    assert "--dry-run" in runner.invoke(app, ["run", "--help"]).output
