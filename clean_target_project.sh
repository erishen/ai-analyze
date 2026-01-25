#!/bin/bash
# 清理目标项目中由 ai-analyze 生成的 Docker 相关文件
# 用法：./clean_target_project.sh /path/to/target/project [--yes]
#      --yes: 跳过确认，直接删除

set -e

SKIP_CONFIRM=""
TARGET_DIR=""

# 解析参数
if [ $# -eq 1 ]; then
    TARGET_DIR="$1"
elif [ $# -eq 2 ] && [ "$1" = "--yes" ]; then
    SKIP_CONFIRM="--yes"
    TARGET_DIR="$2"
else
    echo "用法: $0 /path/to/target/project [--yes]"
    echo "      --yes: 跳过确认，直接删除"
    exit 1
fi

if [ ! -d "$TARGET_DIR" ]; then
    echo "错误: 目标目录不存在: $TARGET_DIR"
    exit 1
fi

# 调用 Python 脚本
if [ -n "$SKIP_CONFIRM" ]; then
    python tools/clean_generated_files.py "$TARGET_DIR" --yes
else
    python tools/clean_generated_files.py "$TARGET_DIR"
fi