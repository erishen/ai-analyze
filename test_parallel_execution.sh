#!/bin/bash

# 并行执行测试脚本

echo "=========================================="
echo "并行执行功能测试"
echo "=========================================="

# 进入 ai-analyze 目录
cd ai-analyze

# 测试 1: 检查语法
echo ""
echo "✓ 测试 1: 检查 Python 语法..."
python -m py_compile tools/full_analyzer.py
if [ $? -eq 0 ]; then
    echo "  ✅ 语法检查通过"
else
    echo "  ❌ 语法检查失败"
    exit 1
fi

# 测试 2: 检查导入
echo ""
echo "✓ 测试 2: 检查导入..."
python -c "from tools.full_analyzer import run_analyses_parallel; print('  ✅ 导入检查通过')"
if [ $? -ne 0 ]; then
    echo "  ❌ 导入检查失败"
    exit 1
fi

# 测试 3: 检查命令行参数
echo ""
echo "✓ 测试 3: 检查命令行参数..."
python tools/full_analyzer.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ 命令行参数检查通过"
else
    echo "  ❌ 命令行参数检查失败"
    exit 1
fi

# 测试 4: 检查并行函数存在
echo ""
echo "✓ 测试 4: 检查并行函数..."
python -c "
import asyncio
from tools.full_analyzer import run_analyses_parallel
print('  ✅ 并行函数存在')
"
if [ $? -ne 0 ]; then
    echo "  ❌ 并行函数检查失败"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 所有测试通过！"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 运行完整分析: python tools/full_analyzer.py"
echo "2. 查看性能提升"
echo "3. 实施优化 2: 增强 AI 分析"

