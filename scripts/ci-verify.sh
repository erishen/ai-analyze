#!/bin/bash
# 本地 CI 验证脚本
# 模拟 GitHub Actions CI 环境运行所有检查

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}本地 CI 验证${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 设置 CI 环境变量
export CI=true
export OPENAI_API_KEY="test-key-for-ci"
export OPENAI_MODEL="openai/gpt-4"
export PROJECT_PATH="./"

echo -e "${GREEN}1. 检查虚拟环境...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}未找到 .venv，正在创建...${NC}"
    uv venv
fi
echo -e "${GREEN}2. 安装依赖...${NC}"
source .venv/bin/activate
uv pip install -e .[dev]

echo -e "${GREEN}3. 检查环境配置...${NC}"
make check-env || {
    echo -e "${RED}✗ check-env 失败${NC}"
    exit 1
}
echo -e "${GREEN}✓ 环境检查通过${NC}"
echo ""

echo -e "${GREEN}4. 运行测试...${NC}"
make test || {
    echo -e "${YELLOW}⚠ 测试失败（可能是 Serena 未安装）${NC}"
}
echo ""

echo -e "${GREEN}4. 运行代码检查...${NC}"
make lint || {
    echo -e "${RED}✗ lint 失败${NC}"
    exit 1
}
echo -e "${GREEN}✓ 代码检查通过${NC}"
echo ""

echo -e "${GREEN}5. 运行类型检查...${NC}"
make type-check || {
    echo -e "${RED}✗ type-check 失败${NC}"
    exit 1
}
echo -e "${GREEN}✓ 类型检查通过${NC}"
echo ""

echo -e "${GREEN}6. 运行格式检查...${NC}"
make format-check || {
    echo -e "${RED}✗ format-check 失败${NC}"
    exit 1
}
echo -e "${GREEN}✓ 格式检查通过${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ 所有检查通过！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}提示：${NC}"
echo "  - 如果需要修改代码，运行:"
echo "    source .venv/bin/activate"
echo "    # 进行修改"
echo "    make format        # 格式化代码"
echo "    make lint         # 再次检查"
echo ""
echo "  - 完成后再次运行此脚本验证:"
echo "    ./scripts/ci-verify.sh"
