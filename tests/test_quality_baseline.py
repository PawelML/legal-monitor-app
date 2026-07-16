"""Baseline test proving the package and test runner are wired correctly."""

from legal_monitor.evals.run import main


def test_evaluation_command_contract_is_available() -> None:
    assert main() == 0
