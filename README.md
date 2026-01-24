# Serena MCP 客户端工具

一套基于 MCP (Model Context Protocol) 的代码分析工具，支持多语言项目的智能分析。

## 📦 项目结构

```
.
├── tools/                          # 工具脚本目录
│   ├── analyze_project_multilang.py  # 一键多语言分析工具
│   └── serena_stdio_client.py        # Stdio 客户端
├── reports/                        # 生成的分析报告目录
├── src/                            # 源代码
├── tests/                          # 测试用例
├── examples/                       # 示例代码
├── Makefile                        # 项目管理命令
├── requirements.txt                # Python 依赖
├── environment.yml                 # Conda 环境配置
├── pyproject.toml                  # 项目配置
└── .env.example                    # 环境变量示例
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 使用 Makefile 一键安装
make install

# 或手动安装
pip install -e .
```

### 2. 配置环境

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，配置你的 SERENA_DIR 和 PROJECT_PATH
```

### 3. 运行分析

```bash
# 生成 Markdown 分析报告
make analyze

# 生成 JSON 分析报告
make analyze-json

# 清理旧的报告
make clean-reports
```

## 📋 可用命令

使用 `make help` 查看所有可用命令：

```bash
make help
```

主要命令：
- `make install` - 安装依赖
- `make analyze` - 分析项目并生成 Markdown 报告
- `make analyze-json` - 分析项目并生成 JSON 报告
- `make clean` - 清理缓存和临时文件
- `make clean-reports` - 清理旧的分析报告
- `make test` - 运行测试

## 📖 详细文档

- [Makefile 使用指南](MAKEFILE_USAGE.md) - Makefile 命令详解
- [Conda 环境设置](CONDA_SETUP.md) - Conda 环境配置指南

## 🛠️ 功能特性

- 🔍 多语言支持（Python、JavaScript、TypeScript、Java、Go、Rust、C/C++）
- 📊 自动代码结构分析
- 🎯 符号查找和引用追踪
- 📄 生成人类可读的分析报告
- 📁 智能项目结构识别
- ⏱️ 时间戳报告管理

## 🔧 技术要求

- Python 3.8+
- Serena MCP 服务器
- 依赖包详见 `requirements.txt`
