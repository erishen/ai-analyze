#!/bin/bash
# 快速设置 conda 环境的脚本

set -e

# 颜色定义
GREEN='\033[32m'
CYAN='\033[36m'
YELLOW='\033[33m'
NC='\033[0m'

echo -e "${CYAN}======================================${NC}"
echo -e "${CYAN}Serena MCP Client - Conda 环境设置${NC}"
echo -e "${CYAN}======================================${NC}"
echo -e ""

# 检查 conda 是否已安装
if ! command -v conda &> /dev/null; then
    echo -e "${YELLOW}⚠ 未找到 conda${NC}"
    echo -e "请先安装 Anaconda 或 Miniconda:"
    echo -e "  - Anaconda: https://www.anaconda.com/download"
    echo -e "  - Miniconda: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo -e "${GREEN}✓ 找到 conda: $(conda --version)${NC}"
echo -e ""

# 检查环境是否已存在
ENV_NAME="serena-client"
if conda env list | grep -q "^${ENV_NAME} "; then
    echo -e "${YELLOW}⚠ conda 环境 '${ENV_NAME}' 已存在${NC}"
    read -p "是否要重新创建? (y/N) " -n 1 -r
    echo -e
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "删除现有环境..."
        conda env remove -n ${ENV_NAME} -y
    else
        echo -e "使用现有环境"
        echo -e "${YELLOW}请手动激活环境: conda activate ${ENV_NAME}${NC}"
        exit 0
    fi
fi

# 创建 conda 环境
echo -e "${GREEN}创建 conda 环境...${NC}"
conda env create -f environment.yml

# 激活环境
echo -e ""
echo -e "${GREEN}✓ conda 环境创建成功！${NC}"
echo -e ""
echo -e "${CYAN}下一步操作：${NC}"
echo -e "  1. 激活环境:"
echo -e "     ${YELLOW}conda activate ${ENV_NAME}${NC}"
echo -e ""
echo -e "  2. 初始化项目:"
echo -e "     ${YELLOW}make init${NC}"
echo -e ""
echo -e "  3. 安装依赖:"
echo -e "     ${YELLOW}make install${NC}"
echo -e ""
echo -e "  4. 运行测试:"
echo -e "     ${YELLOW}make test${NC}"
echo -e ""
echo -e "${CYAN}详细文档: docs/CONDA_SETUP.md${NC}"
