# Makefile for AI-Analyze
# 优化版本 - 删除了无用和冗余的命令

.PHONY: help init check-env test clean clean-reports clean-target lint format format-check ci-verify uv-install uv-sync uv-shell install-dev type-check debug version analyze-full analyze-full-serena analyze-full-skip-ai analyze-full-skip-docker analyze-full-skip-ast analyze-full-force analyze-full-no-cache analyze-full-custom-ttl analyze-ast analyze-ast-md docker-check docker-generate docker-build docker-run docker-verify docker-all docker-compose-up docker-compose-down cache-clear cache-clear-project cache-list

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
DOCS_DIR := docs
EXAMPLES_DIR := examples
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

## check-env: 检查环境变量配置
check-env:
	@echo -e "$(GREEN)检查环境变量配置...$(NC)"
	@if [ -z "$CI" ]; then \
		if [ ! -f .env ]; then \
			echo -e "$(YELLOW)⚠ .env 文件不存在，请先创建: make init$(NC)"; \
			exit 1; \
		fi; \
	fi
	@if [ -z "$OPENAI_API_KEY" ]; then \
		echo -e "$(YELLOW)⚠ OPENAI_API_KEY 未设置$(NC)"; \
		exit 1; \
	fi
	@if [ -z "$PROJECT_PATH" ]; then \
		echo -e "$(YELLOW)⚠ PROJECT_PATH 未设置$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)✓ 环境变量配置正确$(NC)"

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

## uv-shell: 进入 uv 虚拟环境
uv-shell:
	@echo -e "$(GREEN)🐚 进入 uv 虚拟环境...$(NC)"
	@uv shell

## install-dev: 安装开发依赖
install-dev:
	@echo -e "$(GREEN)安装开发依赖...$(NC)"
	@$(PYTHON) -m pip install -e .[dev]
	@echo -e "$(GREEN)✓ 开发依赖安装完成$(NC)"

## test: 运行所有测试
test:
	@echo -e "$(GREEN)运行测试...$(NC)"
	@$(PYTHON) -m pytest $(TESTS_DIR)/ -v

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

## analyze-full-skip-ast: 跳过 AST 分析，运行 Serena + AI + Docker
analyze-full-skip-ast:
	@echo -e "$(GREEN)🚀 跳过 AST 分析，运行 Serena + AI + Docker...$(NC)"
	@$(PYTHON) tools/full_analyzer.py --skip-ast --yes

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

## docker-build: 构建 Docker 镜像
docker-build:
	@echo -e "$(GREEN)📦 构建 Docker 镜像...$(NC)"
	@if [ -z "$(PROJECT_PATH)" ]; then \
		echo -e "$(YELLOW)⚠️  未找到目标项目路径$(NC)"; \
		exit 1; \
	fi
	@cd $(PROJECT_PATH) && ./docker-build.sh

## docker-run: 运行 Docker 容器
docker-run:
	@echo -e "$(GREEN)🚀 运行 Docker 容器...$(NC)"
	@if [ -z "$(PROJECT_PATH)" ]; then \
		echo -e "$(YELLOW)⚠️  未找到目标项目路径$(NC)"; \
		exit 1; \
	fi
	@cd $(PROJECT_PATH) && ./docker-run.sh

## docker-verify: 验证目标项目的 Docker 配置
docker-verify:
	@echo -e "$(GREEN)🔍 验证目标项目 Docker 配置...$(NC)"
	@if [ -z "$(PROJECT_PATH)" ]; then \
		echo -e "$(YELLOW)⚠️  未找到目标项目路径$(NC)"; \
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

## docker-all: 构建并运行 Docker 容器（一键完成）
docker-all: docker-verify docker-build docker-run
	@echo -e "$(GREEN)🎉 Docker 构建和运行完成！$(NC)"

## docker-compose-up: 使用 docker-compose 启动
docker-compose-up:
	@echo -e "$(GREEN)🐳 启动 docker-compose...$(NC)"
	@if [ -z "$(PROJECT_PATH)" ]; then \
		echo -e "$(YELLOW)⚠️  未找到目标项目路径$(NC)"; \
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
		exit 1; \
	fi
	@if [ ! -f "$(PROJECT_PATH)/docker-compose.yml" ]; then \
		echo -e "$(YELLOW)⚠  docker-compose.yml 不存在$(NC)"; \
		exit 1; \
	fi
	@cd $(PROJECT_PATH) && docker-compose down

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
		if [ -n "$(ls -A .cache)" ]; then \
			for file in .cache/*.json; do \
				if [ -f "$file" ]; then \
					echo -e "  $(basename $file)"; \
				fi; \
			done; \
		else \
			echo -e "  $(YELLOW)无缓存文件$(NC)"; \
		fi; \
	else \
		echo -e "  $(YELLOW)缓存目录不存在$(NC)"; \
	fi
