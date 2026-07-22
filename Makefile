PYTHON := uv run python
UNITY_BIN ?= unity
PLATFORM := $(shell $(PYTHON) -c "import platform; print({'Darwin':'macos','Linux':'linux','Windows':'windows'}[platform.system()])")
SKILL_DIR := skills/unity-cli

.PHONY: install format lint typecheck test collect parse merge generate diff validate update check

install:
	uv sync --frozen

format:
	uv run ruff format .

lint:
	uv run ruff format --check .
	uv run ruff check .

typecheck:
	uv run mypy scripts tests

test:
	uv run pytest

collect:
	$(PYTHON) -m scripts.collect_help --unity "$(UNITY_BIN)" --platform "$(PLATFORM)" --output "$(SKILL_DIR)/snapshots/$(PLATFORM)/help.json" --progress

parse:
	$(PYTHON) -m scripts.parse_help "$(SKILL_DIR)/snapshots/$(PLATFORM)/help.json" "$(SKILL_DIR)/snapshots/$(PLATFORM)/command-tree.json"

merge:
	$(PYTHON) -m scripts.merge_platforms $(SKILL_DIR)/snapshots/linux/command-tree.json $(SKILL_DIR)/snapshots/macos/command-tree.json $(SKILL_DIR)/snapshots/windows/command-tree.json --output $(SKILL_DIR)/data/command-tree.json

generate:
	$(PYTHON) -m scripts.generate_references $(SKILL_DIR)/data/command-tree.json --output $(SKILL_DIR)/references

diff:
	$(PYTHON) -m scripts.semantic_diff $(SKILL_DIR)/data/command-tree.json $(SKILL_DIR)/data/command-tree.next.json

validate:
	$(PYTHON) -m scripts.validate_generated
	uv run skills-ref validate $(SKILL_DIR)

update:
	$(PYTHON) -m scripts.update_skill --collect --unity "$(UNITY_BIN)" --allow-partial

check: lint typecheck test validate
	npx skills add . --list
