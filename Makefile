.DEFAULT_GOAL := help
.PHONY: help install lint format typecheck quality fixtures test all

VENV_PY := $(firstword $(wildcard .venv/Scripts/python.exe) $(wildcard .venv/bin/python))
PYTHON ?= $(if $(VENV_PY),$(VENV_PY),python)

# Colors (ANSI)
YELLOW := \033[33m
GREEN  := \033[32m
BLUE   := \033[34m
RED    := \033[31m
RESET  := \033[0m

# Print helper
PRINT = printf "%b\n"

# Max pytest-xdist workers
MAX_XDIST ?= 6

# Compute worker count using Python (cross-platform)
XDIST_WORKERS := $(shell MAX_XDIST=$(MAX_XDIST) $(PYTHON) -c "import multiprocessing as mp, os; print(min(mp.cpu_count(), int(os.environ.get('MAX_XDIST', 6))))")

help: ## Show this help message
	@$(PRINT) "$(BLUE)BalatroBot Development Makefile$(RESET)"
	@$(PRINT) ""
	@$(PRINT) "$(YELLOW)Available targets:$(RESET)"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "help"      "Show this help message"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "install"   "Install balatrobot and all dependencies (including dev)"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "lint"      "Run ruff linter (check only)"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "format"    "Run formatters (ruff, mdformat, stylua)"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "typecheck" "Run type checkers (Python and Lua)"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "quality"   "Run all code quality checks"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "fixtures"  "Generate fixtures"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "test"      "Run all tests"
	@printf "  $(GREEN)%-18s$(RESET) %s\n" "all"       "Run all code quality checks and tests"

install: ## Install balatrobot and all dependencies (including dev)
	@$(PRINT) "$(YELLOW)Installing all dependencies...$(RESET)"
	uv sync --group dev --group test

lint: ## Run ruff linter (check only)
	@$(PRINT) "$(YELLOW)Running ruff linter...$(RESET)"
	$(PYTHON) -m ruff check --fix --select I .
	$(PYTHON) -m ruff check --fix .

format: ## Run formatters (ruff, mdformat, stylua)
	@$(PRINT) "$(YELLOW)Running ruff formatter...$(RESET)"
	$(PYTHON) -m ruff check --select I --fix .
	$(PYTHON) -m ruff format .
	@$(PRINT) "$(YELLOW)Running mdformat formatter...$(RESET)"
	$(PYTHON) -m mdformat --no-validate ./docs README.md AGENTS.md .claude/skills/balatrobot/SKILL.md
	@if command -v stylua >/dev/null 2>&1; then \
		$(PRINT) "$(YELLOW)Running stylua formatter...$(RESET)"; \
		stylua src/lua; \
	else \
		$(PRINT) "$(BLUE)Skipping stylua formatter (stylua not found)$(RESET)"; \
	fi

typecheck: ## Run type checkers (Python and Lua)
	@$(PRINT) "$(YELLOW)Running Python type checker...$(RESET)"
	@$(PYTHON) -m ty check
	@if command -v lua-language-server >/dev/null 2>&1 && [ -f .luarc.json ]; then \
		$(PRINT) "$(YELLOW)Running Lua type checker...$(RESET)"; \
		lua-language-server --check balatrobot.lua src/lua \
			--configpath="$(CURDIR)/.luarc.json" 2>/dev/null; \
	else \
		$(PRINT) "$(BLUE)Skipping Lua type checker (lua-language-server not found or .luarc.json missing)$(RESET)"; \
	fi

quality: lint typecheck format ## Run all code quality checks
	@$(PRINT) "$(GREEN)✓ All checks completed$(RESET)"

fixtures: ## Generate and verify test fixtures
	@$(PRINT) "$(YELLOW)Checking Balatro is running...$(RESET)"
	@balatrobot api health || (echo ''; echo '  Start Balatro in another terminal:'; echo '    balatrobot serve --fast --debug'; echo ''; exit 1)
	@$(PRINT) "$(GREEN)  Connected!$(RESET)"
	@$(PRINT) "$(YELLOW)Generating all fixtures...$(RESET)"
	$(PYTHON) tests/fixtures/generate.py
	$(PYTHON) tests/fixtures/verify.py

test: ## Run all tests
	@$(PRINT) "$(YELLOW)Running tests/cli with 2 workers...$(RESET)"
	$(PYTHON) -m pytest -n 2 tests/cli
	@$(PRINT) "$(YELLOW)Running production tests/lua with $(XDIST_WORKERS) workers...$(RESET)"
	$(PYTHON) -m pytest -n $(XDIST_WORKERS) tests/lua -m "not debug"
	@$(PRINT) "$(YELLOW)Running debug tests/lua...$(RESET)"
	$(PYTHON) -m pytest -n 1 tests/lua -m debug


all: lint format typecheck test ## Run all code quality checks and tests
	@$(PRINT) "$(GREEN)✓ All checks completed$(RESET)"
