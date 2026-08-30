.PHONY: install
install:
	uv sync
	uv run pre-commit install 2>/dev/null || true

.PHONY: test
test:
	uv run pytest

.PHONY: lint
lint:
	@echo "Running lint and autoformat"
	-uv run ruff format bench
	-uv run ruff check --fix bench

.PHONY: lint-check
lint-check: lint-no-approach-names
	@echo "Running lint check only"
	uv run ruff check bench

# Guard against approach-specific references leaking back into bench/.
# bench/ must stay generic; user-specific approaches live under examples/.
.PHONY: lint-no-approach-names
lint-no-approach-names:
	@echo "Checking bench/ for approach-specific identifiers"
	@if grep -rEn "dc_approaches|forge_dc|lucid_dc|hybrid_raw|doc_naive|doc_chunk|mem0|zep" bench/ --include="*.py"; then \
		echo "ERROR: approach-specific identifiers found in bench/. Move them to examples/."; \
		exit 1; \
	fi

.PHONY: typing
typing:
	uv run mypy bench

.PHONY: clean
clean:
	@echo "Cleaning..."
	-rm -rf dist build *.egg-info
	-find . -name __pycache__ -exec rm -rf {} \;
	-find . -name .pytest_cache -exec rm -rf {} \;
	-find . -name .mypy_cache -exec rm -rf {} \;
	-find . -name .ruff_cache -exec rm -rf {} \;

.PHONY: seeds-list
seeds-list:
	uv run python bench/seedgen/build_scenario.py --list

.PHONY: seeds-build
seeds-build:
	uv run python bench/seedgen/build_scenario.py --all
