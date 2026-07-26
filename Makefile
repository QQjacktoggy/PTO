.PHONY: setup lint typecheck test validate-config project-info phase0 phase1 data-download data-validate features-build replay-test holdout-freeze holdout-run report-final

UV_CACHE_DIR ?= .uv-cache
export UV_CACHE_DIR

setup:
	uv sync --locked --extra dev

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

typecheck:
	uv run mypy src

test:
	uv run pytest -q

validate-config:
	uv run python -m pto_quant.cli config validate --config-dir config

project-info:
	uv run python -m pto_quant.cli project info --config-dir config

phase0: validate-config lint typecheck test

data-download:
	@test -n "$(START)" -a -n "$(END)" || (echo "usage: make data-download START=<UTC> END=<UTC>" >&2; exit 2)
	uv run pto data acquire --start "$(START)" --end "$(END)"

data-validate:
	uv run pto data validate

phase1: validate-config lint typecheck test
	uv run pto data gate

features-build:
	@echo "Phase 2 command is not implemented in Phase 0" >&2; exit 2

replay-test:
	@echo "Replay is not implemented in Phase 0" >&2; exit 2

holdout-freeze:
	@echo "Holdout workflow is not implemented by this Phase 0 CLI scaffold" >&2; exit 2

holdout-run:
	@echo "Sealed holdout cannot be run from the normal Phase 0 command set" >&2; exit 2

report-final:
	@echo "Final reporting is not implemented in Phase 0" >&2; exit 2
