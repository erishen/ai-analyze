# 快速开始指南

## 概述

`ai-analyze` 是一个 AI 增强代码分析工具，提供一键完整分析功能，包括：

1. **Serena 代码结构分析** - 使用 MCP Serena 进行代码结构分析
2. **AST 语法树分析** - 深度分析代码复杂度和代码质量
3. **AI 深度分析** - 使用 DeepSeek AI 进行代码质量评估和框架升级建议
4. **Docker 自动生成** - 基于规则智能生成 Docker 配置（无需 AI）

> 💡 **Docker 生成完全基于规则**：自动检测项目类型、端口、基础镜像，无需 AI 参与，节省成本！

---

## 🚀 环境准备

### 方式 1：使用 uv（推荐，极快）

[uv](https://github.com/astral-sh/uv) 是一个极快的 Python 包管理器，比 pip 快 10-100 倍。

#### 性能对比

| 操作 | pip | uv | 提升 |
|------|-----|-----|------|
| 安装依赖 | ~30s | ~2s | **15x** |
| 依赖解析 | ~10s | ~0.2s | **50x** |
| 虚拟环境创建 | ~5s | ~0.1s | **50x** |
| 依赖锁定 | ~15s | ~0.3s | **50x** |

#### 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 使用 Homebrew (macOS)
brew install uv

# 使用 pip
pip install uv
```

#### 同步依赖

```bash
# 一键安装（推荐）
make uv-install

# 同步依赖
make uv-sync

# 进入虚拟环境
make uv-shell
```

#### 常用 uv 命令

```bash
# 同步依赖（创建/更新虚拟环境）
uv sync

# 添加新依赖
uv add httpx

# 添加开发依赖
uv add --dev pytest

# 运行命令
uv run python tools/full_analyzer.py --help

# 进入虚拟环境
uv shell
```

### 方式 2：使用传统方式（pip）

```bash
# 安装依赖
make install

# 创建虚拟环境并安装
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Python 版本要求

- **Python 3.8+**

---

## ⚙️ 配置说明

### 必需配置

在 `.env` 文件中配置：

```env
# Serena 安装目录
SERENA_DIR=/path/to/serena

# 项目路径（可选，默认为当前工作目录）
PROJECT_PATH=/path/to/your/project
```

### AI 分析配置（可选）

如果需要使用 AI 增强分析：

```env
# DeepSeek API 配置
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
```

获取 API Key: https://platform.deepseek.com/api_keys

---

## 📖 使用方法

### 1. 完整分析（推荐）

运行完整的 Serena + AST + AI + Docker 分析流程：

```bash
# 使用 Makefile
make analyze-full

# 或直接运行 Python
python3 tools/full_analyzer.py
```

### 2. 只运行 Serena 分析

跳过 AST、AI 和 Docker，只生成基础的结构分析报告：

```bash
make analyze-full-serena
# 或
python3 tools/full_analyzer.py --serena-only
```

### 3. 跳过 AI 分析

运行 Serena + AST + Docker，不使用 AI 增强分析：

```bash
make analyze-full-skip-ai
# 或
python3 tools/full_analyzer.py --skip-ai
```

### 4. 跳过 Docker 生成

运行 Serena + AST + AI，不生成 Docker 配置：

```bash
make analyze-full-skip-docker
# 或
python3 tools/full_analyzer.py --skip-docker
```

### 5. 强制覆盖 Docker 配置

即使项目已有 Docker 配置，也会强制覆盖：

```bash
make analyze-full-force
# 或
python3 tools/full_analyzer.py --force-docker
```

### 6. 使用已有报告

如果已经运行过 Serena 分析并生成了 JSON 报告，可以直接使用该报告进行后续分析：

```bash
python3 tools/full_analyzer.py --report reports/project_name_analysis_20260125.json
```

### 7. 增量分析

默认启用增量分析，只分析变化的文件：

```bash
# 默认启用
python3 tools/full_analyzer.py

# 禁用增量分析
python3 tools/full_analyzer.py --no-incremental

# 清除缓存
python3 tools/full_analyzer.py --clear-cache
```

---

## 🎯 Makefile 命令参考

### 一键分析命令

| 命令 | 描述 |
|------|------|
| `make analyze-full` | 完整分析（Serena + AST + AI + Docker） |
| `make analyze-full-serena` | 只运行 Serena 分析 |
| `make analyze-full-skip-ai` | 跳过 AI，运行 Serena + AST + Docker |
| `make analyze-full-skip-docker` | 跳过 Docker，运行 Serena + AST + AI |
| `make analyze-full-force` | 强制覆盖已有 Docker 配置 |

### 依赖管理命令

| 命令 | 描述 |
|------|------|
| `make uv-install` | 使用 uv 安装依赖（推荐） |
| `make uv-sync` | 同步 uv 依赖 |
| `make uv-shell` | 进入 uv 虚拟环境 |
| `make install` | 使用 pip 安装依赖 |

查看所有可用命令：

```bash
make help
```

---

## 📊 生成的文件

### 报告文件（位于 `reports/` 目录）

- `project_name_analysis_YYYYMMDD.json` - Serena + AST 结构分析的 JSON 报告
- `project_name_analysis_YYYYMMDD.md` - Serena + AST 结构分析的 Markdown 报告
- `project_name_analysis_YYYYMMDD-ai.md` - AI 增强分析报告（包含代码质量评估、框架升级建议和 Docker 建议）

### Docker 配置文件（位于项目根目录）

- `Dockerfile` - Docker 镜像构建文件
- `docker-compose.yml` - Docker Compose 编排文件
- `.dockerignore` - Docker 忽略文件
- `docker-build.sh` - Docker 镜像构建脚本
- `docker-run.sh` - Docker 容器运行脚本

---

## 🔧 高级功能

### 框架升级建议

AI 增强分析器包含**框架升级建议**功能，自动分析项目中使用的框架和依赖版本，并提供专业的升级建议。

#### 主要特性

- **智能检测**：自动识别项目使用的编程语言和框架
- **升级建议**：推荐合适的升级路径（考虑稳定性和兼容性）
- **风险评估**：评估升级风险（低/中/高）
- **详细指导**：分步升级方案、测试要求清单、回滚方案建议
- **谨慎性原则**：只有有明显收益时才建议升级

#### 支持的语言和框架

| 语言 | 支持的框架 |
|------|-----------|
| Python | Django/Flask/FastAPI |
| JavaScript/TypeScript | React/Vue/Angular/Next.js/Nuxt.js |
| Go | Go 标准库和主流框架 |

#### 升级报告示例

AI 增强报告中会包含以下章节：

```markdown
## 🔄 AI 框架升级建议

### 📋 升级概览
**框架版本**:
- React: 17.0.2 → 18.2.0
- Next.js: 12.3.0 → 14.1.0

**升级风险等级**: ⚠️ 中风险

### 💡 升级建议
1. 建议优先升级到 React 18.x，享受自动批处理等性能优化
2. Next.js 升级需要逐步进行，建议先升级到 13.x
3. 需要更新相关依赖以确保兼容性

### 🛤️ 推荐升级路径
1. 升级 React 到 18.2.0
2. 升级 Next.js 到 13.4.x
3. 更新相关依赖包
4. 运行完整测试套件
```

#### 使用方法

框架升级建议已集成到完整分析流程中，运行 `make analyze-full` 即可自动包含。

---

## 💰 费用说明

- AI 分析使用 DeepSeek API，每次分析约消耗 10,100 tokens
- 按当前价格计算，每次完整分析成本约 ¥0.017（1.7 分）
- 大约可以分析 60+ 次才花费 ¥1
- **Docker 生成完全基于规则，不消耗 AI tokens**

详细成本：

| 分析类型 | Tokens | 成本 |
|---------|--------|------|
| Serena 结构分析 | 0 | ¥0 |
| AI 代码质量分析 | ~2,500 | ~¥0.005 |
| AI Docker 策略分析 | ~5,100 | ~¥0.007 |
| AI 框架升级建议 | ~2,500 | ~¥0.005 |
| **完整分析** | **~10,100** | **~¥0.017** |

---

## 🛠️ 使用示例

### 示例 1：快速分析现有项目

```bash
# 1. 克隆项目
git clone https://github.com/your/ai-analyze.git
cd ai-analyze

# 2. 安装依赖
make uv-install

# 3. 配置项目路径
echo "PROJECT_PATH=~/my-project" >> .env

# 4. 运行完整分析
make analyze-full

# 5. 查看报告
cat reports/*-ai.md

# 6. 构建 Docker 镜像（如果生成成功）
cd ~/my-project
./docker-build.sh
./docker-run.sh
```

### 示例 2：只分析代码结构

```bash
make analyze-full-serena
```

### 示例 3：分析但不生成 Docker

```bash
make analyze-full-skip-docker
```

### 示例 4：增量分析（CI/CD 优化）

```bash
# 第一次运行：完整分析
python3 tools/full_analyzer.py

# 后续运行：只分析变化的文件
python3 tools/full_analyzer.py  # 自动检测文件变化

# 如果需要强制重新分析
python3 tools/full_analyzer.py --no-incremental
```

---

## ⚠️ 注意事项

1. **API Key 配置**：如果未配置 `OPENAI_API_KEY`，AI 分析步骤会自动跳过
2. **Docker 配置冲突**：如果项目已有 Docker 配置，工具会提示是否覆盖
3. **项目路径**：确保 `PROJECT_PATH` 指向正确的项目根目录
4. **时间成本**：完整分析可能需要 30-60 秒，取决于项目大小和网络速度
5. **增量分析**：默认启用增量分析，CI/CD 环境下性能提升 80%

---

## ❓ 常见问题

### Q: uv 会破坏现有环境吗？

A: 不会。uv 创建独立的虚拟环境，不会影响系统 Python 或其他环境。

### Q: 可以和 pip 一起使用吗？

A: 可以。uv 完全兼容 pip，但建议统一使用 uv 以避免混乱。

### Q: 如何切换回传统方式？

A: 直接删除 `.venv` 目录，使用 `make install` 安装。

### Q: 为什么 AI 有时不建议升级？

A: AI 基于谨慎性原则，只有在有明显收益（安全、性能、功能）时才会建议升级。如果当前版本已经是最新稳定版，或者升级风险过高，AI 会明确说明不建议升级。

### Q: 框架升级建议的准确性如何？

A: AI 基于项目的依赖文件和官方最佳实践进行分析，提供专业的参考建议。但由于每个项目的具体情况不同，建议在升级前结合实际项目需求进行评估。

---

## 📚 更多信息

- [FEATURES.md](FEATURES.md) - 功能详解（AST 分析、增量分析、智能 Docker）
- [OPTIMIZATION_HISTORY.md](OPTIMIZATION_HISTORY.md) - 优化历程和性能提升
- [INDEX.md](INDEX.md) - 完整文档索引
- [README.md](../README.md) - 项目完整文档
