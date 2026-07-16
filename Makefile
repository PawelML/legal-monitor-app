.DEFAULT_GOAL := help

UV ?= uv

.PHONY: help bootstrap lint format format-check typecheck test eval quality ci

help: ## Show available development commands.
	@awk 'BEGIN {FS = ":.*##"}; /^[a-zA-Z_-]+:.*##/ {printf "%-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

bootstrap: ## Install or synchronize development dependencies.
	$(UV) sync --group dev

lint: ## Run lint checks.
	$(UV) run ruff check .

format: ## Apply safe formatting.
	$(UV) run ruff format .

format-check: ## Verify formatting without changing files.
	$(UV) run ruff format --check .

typecheck: ## Run strict static type checks.
	$(UV) run mypy

test: ## Run unit and integration tests.
	$(UV) run pytest

eval: ## Verify the evaluation-command contract (full harness arrives in Phase 1).
	$(UV) run python -m legal_monitor.evals.run

quality: lint format-check typecheck test ## Run mandatory code-quality gates.

ci: quality eval ## Run every CI gate locally.
