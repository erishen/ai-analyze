# Makefile for AI-Analyze

.PHONY: help init test clean lint format format-check ci-verify uv-install uv-sync install-dev type-check debug version analyze-ast analyze-ast-md docker-check docker-generate clean-target clean-reports cache-clear cache-list coverage

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
NC := \033[0m # No Color

# Echo 命令（支持颜色转义）
ECHO := echo -e

# 加载 .env 文件（如果存在）
-include .env

# Python 相关命令（优先级：.venv(uv) > venv > 系统python）
ifeq ($(shell test -f .venv/bin/python && echo .venv),.venv)
    PYTHON := .venv/bin/python
    PIP := .venv/bin/pip
else ifeq ($(shell test -f venv/bin/python && echo venv),venv)
    PYTHON := venv/bin/python
    PIP := venv/bin/pip
else
    PYTHON := python3
    PIP := pip3
endif

# 目录路径
SRC_DIR := src
TESTS_DIR := tests
SCRIPTS_DIR := scripts

## help: 显示帮助信息
help:
	@echo -e "$(CYAN)AI-Analyze - 可用命令$(NC)"
	@echo -e ""
	@grep -E '^##' $(MAKEFILE_LIST) | sed 's/## //g' | column -t -s ':'

## init: 初始化项目（创建 .env 文件）
init:
	@echo -e "$(GREEN)初始化项目...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo -e "$(GREEN)✓ 已创建 .env 文件，请编辑配置$(NC)"; \
	else \
		echo -e "$(YELLOW)⚠ .env 文件已存在$(NC)"; \
	fi

## uv-install: 使用 uv 安装依赖（推荐）
uv-install:
	@echo -e "$(GREEN)🚀 使用 uv 安装依赖...$(NC)"
	@if ! command -v uv &> /dev/null; then \
		echo -e "$(YELLOW)📦 uv 未安装，正在安装...$(NC)"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		export PATH="$HOME/.cargo/bin:$PATH"; \
	fi
	@echo -e "$(GREEN)✅ uv 版本: $(uv --version)$(NC)"
	@uv sync
	@uv sync --extra dev
	@echo -e "$(GREEN)✓ 依赖安装完成$(NC)"

## uv-sync: 同步 uv 依赖
uv-sync:
	@echo -e "$(GREEN)🔄 同步 uv 依赖...$(NC)"
	@uv sync
	@echo -e "$(GREEN)✓ 依赖同步完成$(NC)"

## install-dev: 安装开发依赖
install-dev:
	@echo -e "$(GREEN)安装开发依赖...$(NC)"
	@$(PYTHON) -m pip install -e .[dev]
	@echo -e "$(GREEN)✓ 开发依赖安装完成$(NC)"

## test: 运行所有测试
test:
	@echo -e "$(GREEN)运行测试...$(NC)"
	@$(PYTHON) -m pytest $(TESTS_DIR)/ -v

## coverage: 运行测试并生成覆盖率报告
coverage:
	@echo -e "$(GREEN)运行测试覆盖率分析...$(NC)"
	@$(PYTHON) -m pytest $(TESTS_DIR)/ -v --cov=src --cov-report=term-missing --cov-report=html:.coverage-report
	@echo -e "$(GREEN)✓ 覆盖率报告已生成 (.coverage-report/)$(NC)"

## lint: 代码检查
lint:
	@echo -e "$(GREEN)运行代码检查...$(NC)"
	@ruff check $(SRC_DIR)/ $(TESTS_DIR)/
	@echo -e "$(GREEN)✓ 代码检查完成$(NC)"

## format: 格式化代码
format:
	@echo -e "$(GREEN)格式化代码...$(NC)"
	@ruff format $(SRC_DIR)/ $(TESTS_DIR)/
	@echo -e "$(GREEN)✓ 代码格式化完成$(NC)"

## format-check: 检查代码格式（不修改）
format-check:
	@echo -e "$(GREEN)检查代码格式...$(NC)"
	@ruff format --check $(SRC_DIR)/ $(TESTS_DIR)/
	@echo -e "$(GREEN)✓ 代码格式检查完成$(NC)"

## type-check: 类型检查
type-check:
	@echo -e "$(GREEN)运行类型检查...$(NC)"
	@mypy $(SRC_DIR)/ --ignore-missing-imports
	@echo -e "$(GREEN)✓ 类型检查完成$(NC)"

## ci-verify: 本地模拟 CI 环境，运行所有检查
ci-verify:
	@echo -e "$(GREEN)本地 CI 验证...$(NC)"
	@if [ -f $(SCRIPTS_DIR)/ci-verify.sh ]; then \
		chmod +x $(SCRIPTS_DIR)/ci-verify.sh; \
		$(SCRIPTS_DIR)/ci-verify.sh; \
	else \
		echo -e "$(YELLOW)⚠ 脚本不存在: $(SCRIPTS_DIR)/ci-verify.sh$(NC)"; \
	fi

## clean: 清理缓存和临时文件
clean:
	@echo -e "$(GREEN)清理项目...$(NC)"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.pyc' -delete
	@find . -type f -name '*.pyo' -delete
	@find . -type f -name '*.pyd' -delete
	@find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name '*.egg' -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/
	@rm -rf .pytest_cache archive/
	@rm -f .coverage
	@echo -e "$(GREEN)✓ 清理完成$(NC)"

## clean-reports: 清理旧的分析报告
clean-reports:
	@echo -e "$(GREEN)清理旧的分析报告...$(NC)"
	@if [ -d reports ]; then \
		find reports/ -type f \( -name "*.md" -o -name "*.json" \) -delete; \
		echo -e "$(GREEN)✓ 已删除 reports/ 下的所有 .md 和 .json 文件$(NC)"; \
	else \
		echo -e "$(YELLOW)⚠ reports/ 目录不存在$(NC)"; \
	fi

## clean-target: 清理目标项目中生成的 Docker 相关文件
clean-target:
	@if [ -z "$(PROJECT_PATH)" ]; then \
		echo -e "$(YELLOW)⚠️  未找到目标项目路径$(NC)"; \
		echo -e "$(YELLOW)  请在 .env 文件中设置 PROJECT_PATH 或通过命令行指定:$(NC)"; \
		echo -e "$(YELLOW)  • make clean-target PROJECT_PATH=/path/to/project$(NC)"; \
		exit 1; \
	fi
	@if [ "$(SKIP_CONFIRM)" = "true" ]; then \
		echo -e "$(GREEN)跳过确认模式...$(NC)"; \
		$(PYTHON) tools/clean_generated_files.py "$(PROJECT_PATH)" --yes; \
	else \
		$(PYTHON) tools/clean_generated_files.py "$(PROJECT_PATH)"; \
	fi

## debug: 显示调试信息
debug:
	@echo -e "$(CYAN)调试信息:$(NC)"
	@echo -e "PYTHON: $(PYTHON)"
	@echo -e "PIP: $(PIP)"

## version: 显示版本信息
version:
	@echo -e "$(CYAN)AI-Analyze$(NC)"
	@echo -e "Python: $($(PYTHON) --version)"
	@echo -e "Pip: $($(PIP) --version)"

## analyze-ast: 运行 AST 代码分析
analyze-ast:
	@echo -e "$(GREEN)🌳 运行 AST 代码分析...$(NC)"
	@$(PYTHON) tools/ast_analyzer_tool.py $(PROJECT_PATH) --format json

## analyze-ast-md: 生成 AST Markdown 报告
analyze-ast-md:
	@echo -e "$(GREEN)🌳 生成 AST Markdown 报告...$(NC)"
	@$(PYTHON) tools/ast_analyzer_tool.py $(PROJECT_PATH) --format markdown

## docker-check: 检查项目 Docker 配置
docker-check:
	@echo -e "$(GREEN)🐳 检查 Docker 配置...$(NC)"
	@if [ -z "$(PROJECT_PATH)" ]; then \
		echo -e "$(YELLOW)⚠️  未找到目标项目路径$(NC)"; \
		echo -e "$(YELLOW)  请在 .env 文件中设置 PROJECT_PATH 或通过命令行指定:$(NC)"; \
		echo -e "$(YELLOW)  • make docker-check PROJECT_PATH=/path/to/project$(NC)"; \
		exit 1; \
	fi
	@$(PYTHON) tools/docker_generator.py $(PROJECT_PATH)

## docker-generate: 生成 Docker 配置（覆盖已存在的）
docker-generate:
	@echo -e "$(YELLOW)⚠️  生成 Docker 配置（将覆盖已有文件）...$(NC)"
	@if [ -z "$(PROJECT_PATH)" ]; then \
		echo -e "$(YELLOW)⚠️  未找到目标项目路径$(NC)"; \
		echo -e "$(YELLOW)  请在 .env 文件中设置 PROJECT_PATH 或通过命令行指定:$(NC)"; \
		echo -e "$(YELLOW)  • make docker-generate PROJECT_PATH=/path/to/project$(NC)"; \
		exit 1; \
	fi
	@$(PYTHON) tools/docker_generator.py $(PROJECT_PATH) --force

## cache-clear: 清除所有 AI 分析缓存
cache-clear:
	@echo -e "$(GREEN)🗑️  清除所有 AI 分析缓存...$(NC)"
	@rm -rf .cache/
	@echo -e "$(GREEN)✓ 缓存已清除$(NC)"

## cache-list: 列出所有缓存文件
cache-list:
	@echo -e "$(CYAN)AI 分析缓存文件:$(NC)"
	@if [ -d .cache ]; then \
		if [ -n "$(ls -A .cache 2>/dev/null)" ]; then \
			for file in .cache/*.json; do \
				if [ -f "$$file" ]; then \
					echo -e "  $$(basename $$file)"; \
				fi; \
			done; \
		else \
			echo -e "  $(YELLOW)无缓存文件$(NC)"; \
		fi; \
	else \
		echo -e "  $(YELLOW)缓存目录不存在$(NC)"; \
	fi
