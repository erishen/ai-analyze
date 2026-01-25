#!/bin/bash
# uv 初始化和安装脚本（支持 conda）

set -e

echo "🚀 使用 uv 管理 ai-analyze 项目依赖..."

# 检查 uv 是否已安装
if ! command -v uv &> /dev/null; then
    echo "📦 安装 uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "✅ uv 版本: $(uv --version)"

# 检测当前 Python 环境
if [ -n "$CONDA_DEFAULT_ENV" ]; then
    echo "🐍 检测到 conda 环境: $CONDA_DEFAULT_ENV"
    echo "📦 使用 conda 管理的 Python 创建虚拟环境..."

    # 使用 conda 的 Python 创建虚拟环境
    UV_PYTHON_PATH=$(which python)
    echo "🔧 使用 Python: $UV_PYTHON_PATH"

    # 同步依赖(创建虚拟环境并安装)
    echo "📥 同步依赖..."
    UV_PYTHON="$UV_PYTHON_PATH" uv sync

    # 安装开发依赖
    echo "🛠️  安装开发依赖..."
    UV_PYTHON="$UV_PYTHON_PATH" uv sync --extra dev
else
    echo "🐍 使用系统 Python 创建虚拟环境..."

    # 同步依赖(创建虚拟环境并安装)
    echo "📥 同步依赖..."
    uv sync

    # 安装开发依赖
    echo "🛠️  安装开发依赖..."
    uv sync --extra dev
fi

echo ""
echo "✅ 依赖安装完成!"
echo ""
echo "使用方法:"
echo "  运行工具: uv run python tools/full_analyzer.py --help"
echo "  运行测试: uv run pytest"
echo "  进入环境: uv shell"
echo ""
echo "提示:"
echo "  - 如果在 conda 环境中,uv 会使用 conda 的 Python"
echo "  - 虚拟环境位置: .venv"
echo "  - 可以通过 uv shell 进入虚拟环境"
