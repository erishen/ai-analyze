# Makefile for Serena MCP Client
# 提供便捷的项目管理命令

.PHONY: help install init check-env test clean clean-reports clean-target lint format format-check conda-create conda-activate conda-update conda-remove conda-export conda-list uv-install uv-sync uv-shell docker-build docker-run docker-verify docker-all docker-compose-up docker-compose-down docker-generate

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

# Python 相关命令（优先级：venv > 指定conda环境 > 激活的conda环境 > 系统python）
ifeq ($(shell test -f venv/bin/python && echo venv),venv)
    # venv 存在，使用 venv
    PYTHON := venv/bin/python
    PIP := venv/bin/pip
    CONDA_AVAILABLE := 0
else ifeq ($(shell test -f /opt/anaconda3/envs/serena-client/bin/python && echo conda),conda)
    # serena-client conda 环境存在，使用它
    PYTHON := /opt/anaconda3/envs/serena-client/bin/python
    PIP := /opt/anaconda3/envs/serena-client/bin/pip
    CONDA_AVAILABLE := 1
    CONDA_ENV := serena-client
else ifneq ($(CONDA_DEFAULT_ENV),)
    # 当前在 conda 环境中，直接使用
    PYTHON := python
    PIP := pip
    CONDA_AVAILABLE := 1
    CONDA_ENV := $(CONDA_DEFAULT_ENV)
else
    # 使用系统 python
    PYTHON := python3
    PIP := pip3
    CONDA_AVAILABLE := 0
endif

# 目录路径
SRC_DIR := src
DOCS_DIR := docs
EXAMPLES_DIR := examples
TESTS_DIR := tests
SCRIPTS_DIR := scripts

## help: 显示帮助信息
help:
	@echo -e "$(CYAN)Serena MCP Client - 可用命令$(NC)"
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

## check-env: 检查环境变量配置
check-env:
	@echo -e "$(GREEN)检查环境变量配置...$(NC)"
	@if [ ! -f .env ]; then \
		echo -e "$(YELLOW)⚠ .env 文件不存在，请先创建: make init$(NC)"; \
		exit 1; \
	fi
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo -e "$(YELLOW)⚠ OPENAI_API_KEY 未设置$(NC)"; \
		exit 1; \
	fi
	@if [ -z "$$PROJECT_PATH" ]; then \
		echo -e "$(YELLOW)⚠ PROJECT_PATH 未设置$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)✓ 环境变量配置正确$(NC)"

## install: 安装依赖（可编辑模式）
install:
	@echo -e "$(GREEN)检查 Python 环境...$(NC)"
	@if [ -n "$$VIRTUAL_ENV" ]; then \
		echo -e "$(GREEN)✓ 在虚拟环境中: $$VIRTUAL_ENV$(NC)"; \
	elif command -v conda &> /dev/null; then \
		if ! conda env list | grep -q "^serena-client "; then \
			echo -e "$(YELLOW)⚠ 'serena-client' conda 环境不存在$(NC)"; \
			echo -e "$(YELLOW)  请先创建环境:$(NC)"; \
			echo -e "$(YELLOW)  • make conda-create$(NC)"; \
			exit 1; \
		fi; \
		CURRENT_ENV=$$(conda info --envs | grep '*' | awk '{print $$1}'); \
		if [ "$$CURRENT_ENV" != "serena-client" ]; then \
			echo -e "$(YELLOW)⚠ 当前 conda 环境: $$CURRENT_ENV (应为 serena-client)$(NC)"; \
			echo -e "$(YELLOW)  请激活正确的环境:$(NC)"; \
			echo -e "$(YELLOW)  • conda activate serena-client$(NC)"; \
			exit 1; \
		else \
			echo -e "$(GREEN)✓ 在正确的 conda 环境中: serena-client$(NC)"; \
		fi; \
	else \
		echo -e "$(YELLOW)⚠ 未检测到 conda 或虚拟环境$(NC)"; \
		echo -e "$(YELLOW)  请先设置环境:$(NC)"; \
		echo -e "$(YELLOW)  • 使用 conda: make conda-create$(NC)"; \
		echo -e "$(YELLOW)  • 或激活现有环境: conda activate serena-client$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)安装 Python 依赖（可编辑模式）...$(NC)"
	@PIP_BREAK_SYSTEM_PACKAGES=1 $(PYTHON) -m pip install -e .
	@echo -e "$(GREEN)✓ 依赖安装完成$(NC)"

## uv-install: 使用 uv 安装依赖（推荐）
uv-install:
	@echo -e "$(GREEN)🚀 使用 uv 安装依赖...$(NC)"
	@if ! command -v uv &> /dev/null; then \
		echo -e "$(YELLOW)📦 uv 未安装，正在安装...$(NC)"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		export PATH="$$HOME/.cargo/bin:$$PATH"; \
	fi
	@echo -e "$(GREEN)✅ uv 版本: $$(uv --version)$(NC)"
	@if [ -n "$$CONDA_DEFAULT_ENV" ]; then \
		echo -e "$(CYAN)🐍 检测到 conda 环境: $$CONDA_DEFAULT_ENV$(NC)"; \
		echo -e "$(CYAN)📦 使用 conda 的 Python 创建虚拟环境...$(NC)"; \
		UV_PYTHON=$$(which python) uv sync; \
		UV_PYTHON=$$(which python) uv sync --extra dev; \
	else \
		echo -e "$(CYAN)🐍 使用系统 Python 创建虚拟环境...$(NC)"; \
		uv sync; \
		uv sync --extra dev; \
	fi
	@echo -e "$(GREEN)✓ 依赖安装完成（使用 uv）$(NC)"

## uv-sync: 同步 uv 依赖
uv-sync:
	@echo -e "$(GREEN)🔄 同步 uv 依赖...$(NC)"
	@uv sync
	@echo -e "$(GREEN)✓ 依赖同步完成$(NC)"

## uv-shell: 进入 uv 虚拟环境
uv-shell:
	@echo -e "$(GREEN)🐚 进入 uv 虚拟环境...$(NC)"
	@uv shell

## install-dev: 安装开发依赖
install-dev:
	@echo -e "$(GREEN)检查 Python 环境...$(NC)"
	@if [ -n "$$VIRTUAL_ENV" ]; then \
		echo -e "$(GREEN)✓ 在虚拟环境中: $$VIRTUAL_ENV$(NC)"; \
	elif command -v conda &> /dev/null; then \
		if ! conda env list | grep -q "^serena-client "; then \
			echo -e "$(YELLOW)⚠ 'serena-client' conda 环境不存在$(NC)"; \
			echo -e "$(YELLOW)  请先创建环境:$(NC)"; \
			echo -e "$(YELLOW)  • make conda-create$(NC)"; \
			exit 1; \
		fi; \
		CURRENT_ENV=$$(conda info --envs | grep '*' | awk '{print $$1}'); \
		if [ "$$CURRENT_ENV" != "serena-client" ]; then \
			echo -e "$(YELLOW)⚠ 当前 conda 环境: $$CURRENT_ENV (应为 serena-client)$(NC)"; \
			echo -e "$(YELLOW)  请激活正确的环境:$(NC)"; \
			echo -e "$(YELLOW)  • conda activate serena-client$(NC)"; \
			exit 1; \
		else \
			echo -e "$(GREEN)✓ 在正确的 conda 环境中: serena-client$(NC)"; \
		fi; \
	else \
		echo -e "$(YELLOW)⚠ 未检测到 conda 或虚拟环境$(NC)"; \
		echo -e "$(YELLOW)  请先设置环境:$(NC)"; \
		echo -e "$(YELLOW)  • 使用 conda: make conda-create$(NC)"; \
		echo -e "$(YELLOW)  • 或激活现有环境: conda activate serena-client$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)安装开发依赖...$(NC)"
	@PIP_BREAK_SYSTEM_PACKAGES=1 $(PYTHON) -m pip install -e .[dev]
	@echo -e "$(GREEN)✓ 开发依赖安装完成$(NC)"

## conda-create: 创建 conda 环境（已弃用，建议使用 uv）
conda-create:
	@echo -e "$(YELLOW)⚠ conda 命令已弃用，建议使用 uv$(NC)"
	@echo -e "$(CYAN)请使用: make uv-install$(NC)"

## conda-activate: 显示如何激活 conda 环境（已弃用，建议使用 uv）
conda-activate:
	@echo -e "$(YELLOW)⚠ conda 命令已弃用，建议使用 uv$(NC)"
	@echo -e "$(CYAN)请使用: make uv-shell$(NC)"

## conda-install: 在 conda 环境中安装依赖（已弃用，建议使用 uv）
conda-install:
	@echo -e "$(YELLOW)⚠ conda 命令已弃用，建议使用 uv$(NC)"
	@echo -e "$(CYAN)请使用: make uv-sync$(NC)"

## conda-update: 更新 conda 环境（已弃用，建议使用 uv）
conda-update:
	@echo -e "$(YELLOW)⚠ conda 命令已弃用，建议使用 uv$(NC)"
	@echo -e "$(CYAN)请使用: make uv-sync$(NC)"

## conda-remove: 删除 conda 环境（已弃用，建议使用 uv）
conda-remove:
	@echo -e "$(YELLOW)⚠ conda 命令已弃用，建议使用 uv$(NC)"
	@echo -e "$(CYAN)如需清理虚拟环境，删除 .venv 目录即可$(NC)"

## conda-export: 导出当前环境配置（已弃用，建议使用 uv）
conda-export:
	@echo -e "$(YELLOW)⚠ conda 命令已弃用，建议使用 uv$(NC)"
	@echo -e "$(CYAN)uv.lock 文件即为环境配置$(NC)"

## conda-list: 列出 conda 环境（已弃用，建议使用 uv）
conda-list:
	@echo -e "$(YELLOW)⚠ conda 命令已弃用，建议使用 uv$(NC)"
	@echo -e "$(CYAN)uv 使用 .venv 目录管理环境$(NC)"

## test: 运行所有测试
test:
	@echo -e "$(GREEN)运行测试...$(NC)"
	@$(PYTHON) -m pytest $(TESTS_DIR)/ -v

## test-stdio: 运行 Stdio 客户端测试
test-stdio:
	@echo -e "$(GREEN)运行 Stdio 客户端测试...$(NC)"
	@$(PYTHON) -m pytest $(TESTS_DIR)/test_stdio_client.py -v

## run-example: 运行示例代码
run-example:
	@echo -e "$(GREEN)运行示例代码...$(NC)"
	@$(PYTHON) $(EXAMPLES_DIR)/serena_example.py

## find-symbol: 查找符号（参数：PATTERN）
find-symbol:
	@if [ -z "$(PATTERN)" ]; then \
		echo -e "$(YELLOW)用法: make find-symbol PATTERN=\"pattern\" [PATH=\"path\"]$(NC)"; \
	else \
		$(PYTHON) $(SRC_DIR)/serena_stdio_client.py find-symbol "$(PATTERN)" $(if $(PATH),--path "$(PATH)",); \
	fi

## find-references: 查找引用（参数：NAME_PATH FILE_PATH）
find-references:
	@if [ -z "$(NAME_PATH)" ] || [ -z "$(FILE_PATH)" ]; then \
		echo -e "$(YELLOW)用法: make find-references NAME_PATH=\"path\" FILE_PATH=\"file\"$(NC)"; \
	else \
		$(PYTHON) $(SRC_DIR)/serena_stdio_client.py find-references "$(NAME_PATH)" "$(FILE_PATH)"; \
	fi

## symbols-overview: 获取文件符号概览（参数：FILE_PATH）
symbols-overview:
	@if [ -z "$(FILE_PATH)" ]; then \
		echo -e "$(YELLOW)用法: make symbols-overview FILE_PATH=\"file\" [DEPTH=N]$(NC)"; \
	else \
		$(PYTHON) $(SRC_DIR)/serena_stdio_client.py symbols-overview "$(FILE_PATH)" $(if $(DEPTH),--depth $(DEPTH),); \
	fi

## search-pattern: 搜索代码模式（参数：PATTERN）
search-pattern:
	@if [ -z "$(PATTERN)" ]; then \
		echo -e "$(YELLOW)用法: make search-pattern PATTERN=\"pattern\" [INCLUDE=\"*.py\"]$(NC)"; \
	else \
		$(PYTHON) $(SRC_DIR)/serena_stdio_client.py search-pattern "$(PATTERN)" $(if $(INCLUDE),--include "$(INCLUDE)",); \
	fi

## find-file: 查找文件（参数：MASK）
find-file:
	@if [ -z "$(MASK)" ]; then \
		echo -e "$(YELLOW)用法: make find-file MASK=\"*.py\" [PATH=\".\"]$(NC)"; \
	else \
		$(PYTHON) $(SRC_DIR)/serena_stdio_client.py find-file "$(MASK)" $(if $(PATH),--path "$(PATH)",); \
	fi

## list-dir: 列出目录（参数：PATH）
list-dir:
	@$(PYTHON) $(SRC_DIR)/serena_stdio_client.py list-dir "$(if $(PATH),$(PATH),.)" $(if $(RECURSIVE),--recursive,)

## list-tools: 列出所有可用工具
list-tools:
	@$(PYTHON) $(SRC_DIR)/serena_stdio_client.py list-tools

## lint: 代码检查
lint:
	@echo -e "$(GREEN)运行代码检查...$(NC)"
	@flake8 $(SRC_DIR)/ $(EXAMPLES_DIR)/ $(TESTS_DIR)/ --max-line-length=120
	@echo -e "$(GREEN)✓ 代码检查完成$(NC)"

## format: 格式化代码
format:
	@echo -e "$(GREEN)格式化代码...$(NC)"
	@black $(SRC_DIR)/ $(EXAMPLES_DIR)/ $(TESTS_DIR)/ --line-length=120
	@echo -e "$(GREEN)✓ 代码格式化完成$(NC)"

## format-check: 检查代码格式（不修改）
format-check:
	@echo -e "$(GREEN)检查代码格式...$(NC)"
	@black $(SRC_DIR)/ $(EXAMPLES_DIR)/ $(TESTS_DIR)/ --check --line-length=120
	@echo -e "$(GREEN)✓ 代码格式检查完成$(NC)"

## type-check: 类型检查
type-check:
	@echo -e "$(GREEN)运行类型检查...$(NC)"
	@mypy $(SRC_DIR)/ --ignore-missing-imports
	@echo -e "$(GREEN)✓ 类型检查完成$(NC)"

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

## debug: 显示调试信息
debug:
	@echo -e "$(CYAN)调试信息:$(NC)"
	@echo -e "CONDA_DEFAULT_ENV: $$CONDA_DEFAULT_ENV"
	@echo -e "PYTHON: $(PYTHON)"
	@echo -e "PIP: $(PIP)"
	@echo -e "CONDA_AVAILABLE: $(CONDA_AVAILABLE)"
	@echo -e "CONDA_ENV: $(CONDA_ENV)"

## analyze: 一键分析目标项目并生成 Markdown 报告（支持多语言，加 --format json 可生成 JSON）
analyze:
	@echo -e "$(GREEN)🔍 开始一键分析项目（生成 Markdown 报告，多语言支持）...$(NC)"
	@$(PYTHON) tools/analyze_project_multilang.py --format text
	@echo -e "$(GREEN)✓ 分析完成，报告见 serena_analysis_report.md$(NC)"

## analyze-json: 一键分析目标项目并生成 JSON 报告（支持多语言）
analyze-json:
	@echo -e "$(GREEN)🔍 开始一键分析项目（生成 JSON 报告，多语言支持）...$(NC)"
	@$(PYTHON) tools/analyze_project_multilang.py --format json
	@echo -e "$(GREEN)✓ 分析完成，报告见 serena_analysis_report.json$(NC)"

## analyze-ai: 一键 AI 增强分析（Serena + DeepSeek）
analyze-ai:
	@echo -e "$(GREEN)🤖 开始 AI 增强代码分析（Serena + DeepSeek）...$(NC)"
	@$(PYTHON) tools/analyze_with_ai.py

## analyze-ai-only: 对已有的 Serena 报告进行 AI 增强分析（带参数）
analyze-ai-only-report:
	@if [ -z "$(REPORT)" ]; then \
		echo -e "$(YELLOW)⚠️  请指定报告路径: make analyze-ai-only REPORT=path/to/report.json$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)🤖 对指定报告进行 AI 增强分析...$(NC)"
	@$(PYTHON) tools/analyze_with_ai.py --ai-only --report "$(REPORT)"

## analyze-skip-ai: 只运行 Serena 分析，跳过 AI 增强
analyze-skip-ai:
	@echo -e "$(GREEN)🔍 运行 Serena 分析（跳过 AI 增强）...$(NC)"
	@$(PYTHON) tools/analyze_with_ai.py --skip-ai

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

## docker-build: 构建 Docker 镜像
docker-build:
	@echo -e "$(GREEN)📦 构建 Docker 镜像...$(NC)"
	@if [ -z "$(PROJECT_PATH)" ]; then \
		echo -e "$(YELLOW)⚠️  未找到目标项目路径$(NC)"; \
		echo -e "$(YELLOW)  请在 .env 文件中设置 PROJECT_PATH 或通过命令行指定:$(NC)"; \
		echo -e "$(YELLOW)  • make docker-build PROJECT_PATH=/path/to/project$(NC)"; \
		exit 1; \
	fi
	@cd $(PROJECT_PATH) && ./docker-build.sh

## docker-run: 运行 Docker 容器
docker-run:
	@echo -e "$(GREEN)🚀 运行 Docker 容器...$(NC)"
	@if [ -z "$(PROJECT_PATH)" ]; then \
		echo -e "$(YELLOW)⚠️  未找到目标项目路径$(NC)"; \
		echo -e "$(YELLOW)  请在 .env 文件中设置 PROJECT_PATH 或通过命令行指定:$(NC)"; \
		echo -e "$(YELLOW)  • make docker-run PROJECT_PATH=/path/to/project$(NC)"; \
		exit 1; \
	fi
	@cd $(PROJECT_PATH) && ./docker-run.sh

## docker-verify: 验证目标项目的 Docker 配置
docker-verify:
	@echo -e "$(GREEN)🔍 验证目标项目 Docker 配置...$(NC)"
	@if [ -z "$(PROJECT_PATH)" ]; then \
		echo -e "$(YELLOW)⚠️  未找到目标项目路径$(NC)"; \
		echo -e "$(YELLOW)  请在 .env 文件中设置 PROJECT_PATH 或通过命令行指定:$(NC)"; \
		echo -e "$(YELLOW)  • make docker-build PROJECT_PATH=/path/to/project$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(CYAN)目标项目路径: $(PROJECT_PATH)$(NC)"
	@if [ ! -f "$(PROJECT_PATH)/docker-build.sh" ]; then \
		echo -e "$(YELLOW)⚠  docker-build.sh 不存在$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "$(PROJECT_PATH)/docker-run.sh" ]; then \
		echo -e "$(YELLOW)⚠  docker-run.sh 不存在$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)✓ Docker 配置验证通过$(NC)"
	@echo -e "$(CYAN)可用命令:$(NC)"
	@echo -e "  • make docker-build    # 构建镜像"
	@echo -e "  • make docker-run      # 运行容器"
	@echo -e "  • make docker-all      # 构建并运行"

## docker-all: 构建并运行 Docker 容器（一键完成）
docker-all: docker-verify docker-build docker-run
	@echo -e "$(GREEN)🎉 Docker 构建和运行完成！$(NC)"

## docker-compose-up: 使用 docker-compose 启动
docker-compose-up:
	@echo -e "$(GREEN)🐳 启动 docker-compose...$(NC)"
	@if [ -z "$(PROJECT_PATH)" ]; then \
		echo -e "$(YELLOW)⚠️  未找到目标项目路径$(NC)"; \
		echo -e "$(YELLOW)  请在 .env 文件中设置 PROJECT_PATH 或通过命令行指定:$(NC)"; \
		echo -e "$(YELLOW)  • make docker-compose-up PROJECT_PATH=/path/to/project$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "$(PROJECT_PATH)/docker-compose.yml" ]; then \
		echo -e "$(YELLOW)⚠  docker-compose.yml 不存在$(NC)"; \
		exit 1; \
	fi
	@cd $(PROJECT_PATH) && docker-compose up -d

## docker-compose-down: 停止 docker-compose
docker-compose-down:
	@echo -e "$(YELLOW)⏹️  停止 docker-compose...$(NC)"
	@if [ -z "$(PROJECT_PATH)" ]; then \
		echo -e "$(YELLOW)⚠️  未找到目标项目路径$(NC)"; \
		echo -e "$(YELLOW)  请在 .env 文件中设置 PROJECT_PATH 或通过命令行指定:$(NC)"; \
		echo -e "$(YELLOW)  • make docker-compose-down PROJECT_PATH=/path/to/project$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "$(PROJECT_PATH)/docker-compose.yml" ]; then \
		echo -e "$(YELLOW)⚠  docker-compose.yml 不存在$(NC)"; \
		exit 1; \
	fi
	@cd $(PROJECT_PATH) && docker-compose down

## version: 显示版本信息
version:
	@echo -e "$(CYAN)Serena MCP Client$(NC)"
	@echo -e "Python: $$($(PYTHON) --version)"
	@echo -e "Pip: $$($(PIP) --version)"
	@if [ -n "$$CONDA_DEFAULT_ENV" ]; then \
		echo -e "$(GREEN)Conda 环境: $(CONDA_DEFAULT_ENV)$(NC)"; \
		echo -e "Conda: $$(conda --version)"; \
	else \
		echo -e "$(YELLOW)未使用 conda 环境$(NC)"; \
	fi

## clean-reports: 清理旧的分析报告（reports/ 目录下的 .md 和 .json 文件）
clean-reports:
	@echo -e "$(GREEN)清理旧的分析报告...$(NC)"
	@if [ -d reports ]; then \
		find reports/ -type f \( -name "*.md" -o -name "*.json" \) -delete; \
		echo -e "$(GREEN)✓ 已删除 reports/ 下的所有 .md 和 .json 文件$(NC)"; \
	else \
		echo -e "$(YELLOW)⚠ reports/ 目录不存在$(NC)"; \
	fi

## clean-target: 清理目标项目中生成的 Docker 相关文件（使用 git status 检查新增文件）
##   参数: PROJECT_PATH 可从 .env 文件读取或通过命令行指定
##   参数: SKIP_CONFIRM=true 跳过确认模式
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

## analyze-full: 一键完整分析（Serena + AI + Docker）
analyze-full:
	@echo -e "$(GREEN)🚀 一键完整分析（Serena + AI + Docker）...$(NC)"
	@$(PYTHON) tools/full_analyzer.py --yes

## analyze-full-serena: 只运行 Serena 分析
analyze-full-serena:
	@echo -e "$(GREEN)🔍 只运行 Serena 分析...$(NC)"
	@$(PYTHON) tools/full_analyzer.py --serena-only --yes

## analyze-full-skip-ai: 跳过 AI 分析，只运行 Serena + Docker
analyze-full-skip-ai:
	@echo -e "$(GREEN)🐳 跳过 AI 分析，运行 Serena + Docker...$(NC)"
	@$(PYTHON) tools/full_analyzer.py --skip-ai --yes

## analyze-full-skip-docker: 跳过 Docker 生成，只运行 Serena + AI
analyze-full-skip-docker:
	@echo -e "$(GREEN)🤖 跳过 Docker 生成，运行 Serena + AI...$(NC)"
	@$(PYTHON) tools/full_analyzer.py --skip-docker --yes

## analyze-full-force: 强制覆盖已有 Docker 配置
analyze-full-force:
	@echo -e "$(YELLOW)⚠️  强制覆盖已有 Docker 配置...$(NC)"
	@$(PYTHON) tools/full_analyzer.py --force-docker --yes

## analyze-full-no-cache: 禁用缓存，强制调用 AI API
analyze-full-no-cache:
	@echo -e "$(YELLOW)⚠️  禁用缓存，强制调用 AI API...$(NC)"
	@$(PYTHON) tools/full_analyzer.py --no-cache --yes

## analyze-full-custom-ttl: 自定义缓存有效期（参数：TTL）
analyze-full-custom-ttl:
	@if [ -z "$(TTL)" ]; then \
		echo -e "$(YELLOW)⚠️  请指定缓存有效期（秒）: make analyze-full-custom-ttl TTL=3600$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)🚀 一键完整分析（缓存有效期: $(TTL) 秒）...$(NC)"
	@$(PYTHON) tools/full_analyzer.py --cache-ttl $(TTL) --yes

## cache-clear: 清除所有 AI 分析缓存
cache-clear:
	@echo -e "$(GREEN)🗑️  清除所有 AI 分析缓存...$(NC)"
	@$(PYTHON) tools/ai_enhanced_analyzer.py --clear-cache

## cache-clear-project: 清除指定项目的缓存（参数：PROJECT_PATH）
cache-clear-project:
	@if [ -z "$(PROJECT_PATH)" ]; then \
		echo -e "$(YELLOW)⚠️  请指定项目路径: make cache-clear-project PROJECT_PATH=/path/to/project$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)🗑️  清除项目缓存: $(PROJECT_PATH)$(NC)"
	@$(PYTHON) tools/ai_enhanced_analyzer.py --clear-project-cache "$(PROJECT_PATH)"

## cache-list: 列出所有缓存文件
cache-list:
	@echo -e "$(CYAN)AI 分析缓存文件:$(NC)"
	@if [ -d .cache ]; then \
		if [ -n "$$(ls -A .cache)" ]; then \
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

