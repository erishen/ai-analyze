# Documentation Index

Welcome to the ai-analyze documentation. This index helps you find the right guide for your needs.

---

## 📚 Quick Navigation

### Getting Started

- [QUICK_START.md](QUICK_START.md) - 快速开始指南
  - 环境准备（uv 或 pip）
  - 配置说明
  - 使用方法（完整分析、单独功能、各种运行模式）
  - 框架升级建议
  - 费用说明
  - 常见问题

### Core Features

- [FEATURES.md](FEATURES.md) - 功能详解
  - **AST 分析**：代码复杂度分析、代码坏味道检测、代码指标收集
  - **增量分析**：缓存分析结果、只重新分析变化文件
  - **智能 Docker 配置**：自动分析代码复杂度、生成优化的 Docker 配置

### Optimization History

- [OPTIMIZATION_HISTORY.md](OPTIMIZATION_HISTORY.md) - 优化历程
  - 5 个主要优化阶段
  - 集成分析完成报告
  - 代码质量改进
  - 总体性能提升统计
  - 未来优化方向

---

## 🎯 Find What You Need

### By Use Case

#### I want to...

**Start using the tool**
→ [QUICK_START.md](QUICK_START.md)

**Understand AST analysis**
→ [FEATURES.md](FEATURES.md#1-ast-代码分析功能)

**Learn about incremental analysis**
→ [FEATURES.md](FEATURES.md#2-增量分析)

**Generate smart Docker configs**
→ [FEATURES.md](FEATURES.md#3-智能-docker-配置)

**See what optimizations were made**
→ [OPTIMIZATION_HISTORY.md](OPTIMIZATION_HISTORY.md)

**Learn about framework upgrades**
→ [QUICK_START.md](QUICK_START.md#-高级功能)

**Troubleshoot common issues**
→ [QUICK_START.md](QUICK_START.md#-常见问题)

### By Topic

#### Performance

- [OPTIMIZATION_HISTORY.md](OPTIMIZATION_HISTORY.md) - 详细的优化历程
- [FEATURES.md](FEATURES.md#2-增量分析) - 增量分析性能提升

#### Code Analysis

- [FEATURES.md](FEATURES.md#1-ast-代码分析功能) - AST 分析详解

#### Docker

- [FEATURES.md](FEATURES.md#3-智能-docker-配置) - 智能 Docker 配置指南

#### Setup

- [QUICK_START.md](QUICK_START.md#-环境准备) - 安装和配置指南

---

## 📊 Documentation Structure

```
ai-analyze/docs/
├── QUICK_START.md              # 快速开始指南
├── FEATURES.md                # 功能详解
├── OPTIMIZATION_HISTORY.md    # 优化历程
└── INDEX.md                   # 本文档（索引）
```

---

## 🚀 Common Workflows

### First Time Setup

1. Read [QUICK_START.md](QUICK_START.md)
2. Install dependencies (uv recommended)
3. Configure `.env` file
4. Run `make analyze-full`

### Running Analysis

1. Use [QUICK_START.md](QUICK_START.md#-使用方法) for basic usage
2. See [FEATURES.md](FEATURES.md) for detailed feature explanations
3. Enable [incremental analysis](FEATURES.md#2-增量分析) for CI/CD

### Docker Deployment

1. Run `make analyze-full`
2. Review generated Docker files
3. Follow [SMART_DOCKER Guide](FEATURES.md#3-智能-docker-配置) for optimization tips
4. Deploy with `./docker-build.sh` and `./docker-run.sh`

### Understanding Performance

1. Start with [OPTIMIZATION_HISTORY.md](OPTIMIZATION_HISTORY.md)
2. Learn about incremental analysis for CI/CD optimization
3. Use smart Docker config for cost savings

---

## 📖 Document Descriptions

### QUICK_START.md (快速开始指南)

**Content**:
- 环境准备（uv 或 pip）
- 配置说明（必需配置和可选 AI 配置）
- 使用方法（完整分析、单独功能、各种运行模式）
- 高级功能（框架升级建议）
- 费用说明
- 常见问题

**Who should read**: New users, anyone setting up the tool

### FEATURES.md (功能详解)

**Content**:
- **AST 代码分析**：
  - 核心功能（复杂度分析、代码坏味道检测、代码指标）
  - 支持的语言
  - 使用方法
  - 输出格式
  - 性能优化
  - 配置选项
  - 常见问题

- **增量分析**：
  - 概述和工作原理
  - 快速开始
  - 缓存管理
  - 使用场景
  - 性能示例
  - CI/CD 集成
  - 常见问题

- **智能 Docker 配置**：
  - 概述
  - 快速开始
  - 资源配置文件
  - 如何计算复杂度
  - 生成的 Docker Compose 和 Kubernetes 配置
  - 成本优化
  - 高级用法
  - 最佳实践
  - CI/CD 集成

**Who should read**: Users wanting detailed feature explanations

### OPTIMIZATION_HISTORY.md (优化历程)

**Content**:
- 总体优化成果（表格汇总）
- **优化 1**: 并行执行 (+20-30%)
- **优化 2**: 增强 AI 分析 (+15-25%)
- **优化 3**: 数据融合 (+30-50%)
- **优化 4**: 增量分析 (+80% CI/CD)
- **优化 5**: Smart Docker Configuration (+10-15% 容器效率，20-30% 成本节省)
- 集成分析完成（相似性 + 质量评分）
- 代码质量改进（日志、异常、配置、重试）
- 总体性能提升
- 验证和测试
- 未来优化方向

**Who should read**: Developers, contributors, anyone interested in performance improvements

---

## 💡 Tips

### New to the project?

Start with [QUICK_START.md](QUICK_START.md) to get up and running quickly.

### Want to understand features?

Check out [FEATURES.md](FEATURES.md) for detailed explanations of all major features.

### Interested in performance?

Read [OPTIMIZATION_HISTORY.md](OPTIMIZATION_HISTORY.md) to see how performance was improved over time.

### Need help with Docker?

The Smart Docker Configuration section in [FEATURES.md](FEATURES.md#3-智能-docker-配置) provides comprehensive guidance.

---

## 🔗 Related Resources

### Main Documentation

- [README.md](../README.md) - 项目完整文档
- [TODO.md](../TODO.md) - 任务跟踪和进度

### External Resources

- [uv 官方文档](https://docs.astral.sh/uv/)
- [DeepSeek API](https://platform.deepseek.com/api_keys)
- [Docker 官方文档](https://docs.docker.com/)
- [Kubernetes 官方文档](https://kubernetes.io/docs/)

---

## 📝 Conventions

### Code Blocks

All code examples are provided in Markdown code blocks with language labels:

```bash
# Bash/shell commands
```

```python
# Python code
```

```yaml
# YAML/Docker configs
```

### Terminology

- **Serena**: MCP Serena 代码结构分析工具
- **AST**: Abstract Syntax Tree，抽象语法树
- **Docker**: 容器化平台
- **uv**: 极快的 Python 包管理器

---

## 🤝 Feedback

If you have questions, suggestions, or want to contribute:

- Check [README.md](../README.md) for contribution guidelines
- Submit issues via GitHub
- Start discussions for feature requests

---

**Last Updated**: 2026年2月25日

**Version**: 1.0 (文档整合版本)
