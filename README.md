# 🤖 AI 增强代码分析工具

一套基于 **MCP (Model Context Protocol)** 和 **DeepSeek AI** 的智能代码分析工具，提供 Serena 代码结构分析、AI 深度质量评估、Docker 自动生成等全流程解决方案。

## ✨ 核心特性

- 🔍 **Serena 代码结构分析**：多语言支持（20+ 语言），智能符号解析
- 🤖 **AI 增强分析**：DeepSeek 深度评估代码质量、架构设计
- 🐳 **Docker 自动生成**：AI 驱动，智能推荐最优容器化方案
- 💰 **超低成本**：每次完整分析仅需 **¥0.01-0.03**
- ⚡ **一键自动化**：Makefile 驱动，2-3 分钟完成全流程
- 📊 **多格式报告**：Markdown + JSON 双格式输出
- 🎯 **智能优化**：基于最佳实践的 15+ 个优化维度

## 📦 项目结构

```
.
├── tools/                          # 工具脚本目录
│   ├── analyze_project_multilang.py  # Serena 多语言分析工具
│   ├── ai_enhanced_analyzer.py       # AI 增强分析器（DeepSeek 集成）
│   ├── docker_generator.py          # Docker 配置自动生成器
│   ├── analyze_with_ai.py           # 一键 AI 分析脚本
│   ├── full_analyzer.py             # 一键完整分析工具（Serena + AI + Docker）
│   └── serena_stdio_client.py       # Stdio 客户端
├── reports/                        # 生成的分析报告目录
├── docs/                          # 文档目录
├── src/                           # 源代码
├── tests/                         # 测试用例
├── examples/                      # 示例代码
├── Makefile                       # 项目管理命令（30+ 命令）
├── requirements.txt               # Python 依赖
├── environment.yml               # Conda 环境配置
├── pyproject.toml               # 项目配置
├── .env.example                 # 环境变量示例
├── QUICK_START.md               # 一键分析工具快速指南
├── TOKEN_USAGE_ANALYSIS.md      # Token 使用分析报告
├── IDE_VS_SCRIPT_COMPARISON.md  # 方案对比文档
└── CRITICAL_ANALYSIS.md         # 问题与商业化分析
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 使用 Makefile 一键安装所有依赖
make install

# 或手动安装
pip install -e .
pip install -r requirements.txt
```

### 2. 配置环境

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，配置以下关键变量：
# - PROJECT_PATH: 要分析的目标项目路径
# - OPENAI_API_KEY: DeepSeek API 密钥（用于 AI 分析）
# - OPENAI_BASE_URL: https://api.deepseek.com
# - OPENAI_MODEL: deepseek-chat
```

### 3. 一键完整分析（最推荐）

```bash
# 完整分析：Serena + AI + Docker
make analyze-full

# 只运行 Serena 分析
make analyze-full-serena

# 跳过 AI 分析，运行 Serena + Docker
make analyze-full-skip-ai

# 跳过 Docker 生成，运行 Serena + AI
make analyze-full-skip-docker

# 强制覆盖已有 Docker 配置
make analyze-full-force
```

### 4. 单独功能使用

```bash
# 只运行 AI 增强（已有 Serena 报告）
make analyze-ai-only REPORT=reports/your_report.json

# 只生成 Docker 配置
make docker-generate

# 构建并运行 Docker
make docker-build
make docker-run
```

## 📋 可用命令（35+）

使用 `make help` 查看所有命令：

```bash
make help
```

### 🔍 一键分析命令（推荐）

|| 命令 | 说明 | AI 成本 |
||------|------|---------|
|| `make analyze-full` | 一键完整分析（Serena + AI + Docker） | ~¥0.012 |
|| `make analyze-full-serena` | 只运行 Serena 分析 | ¥0 |
|| `make analyze-full-skip-ai` | 跳过 AI，运行 Serena + Docker | ¥0 |
|| `make analyze-full-skip-docker` | 跳过 Docker，运行 Serena + AI | ~¥0.012 |
|| `make analyze-full-force` | 强制覆盖已有 Docker 配置 | ~¥0.012 |

### 🔍 核心分析命令

|| 命令 | 说明 | AI 成本 |
||------|------|---------|
|| `make analyze-ai` | 一键 AI 增强分析（完整流程） | ~¥0.012 |
|| `make analyze-skip-ai` | 仅 Serena 分析（跳过 AI） | ¥0 |
|| `make analyze-ai-only` | 对已有报告进行 AI 增强 | ~¥0.012 |
|| `make analyze` | 生成 Markdown 报告（多语言）| ¥0 |
|| `make analyze-json` | 生成 JSON 报告（多语言）| ¥0 |

### 🐳 Docker 命令

|| 命令 | 说明 |
||------|------|
|| `make docker-check` | 检查项目 Docker 配置 |
|| `make docker-generate` | 生成 Docker 配置（AI 增强）|
|| `make docker-build` | 构建 Docker 镜像 |
|| `make docker-run` | 运行 Docker 容器 |
|| `make docker-compose-up` | 启动 docker-compose |
|| `make docker-compose-down` | 停止 docker-compose |

### 🧹 清理命令

|| 命令 | 说明 |
||------|------|
|| `make clean` | 清理缓存和临时文件 |
|| `make clean-reports` | 清理旧的分析报告 |
|| `make clean-all` | 清理所有生成文件 |

### 🛠️ 开发命令

|| 命令 | 说明 |
||------|------|
|| `make install` | 安装依赖 |
|| `make test` | 运行测试 |
|| `make lint` | 代码检查 |
|| `make format` | 格式化代码 |
|| `make debug` | 显示调试信息 |

### 🐍 Conda 环境命令

|| 命令 | 说明 |
||------|------|
|| `make conda-create` | 创建 Conda 环境 |
|| `make conda-activate` | 激活 Conda 环境 |
|| `make conda-install` | 安装 Conda 依赖 |

## 📖 详细文档

- [一键分析工具快速指南](QUICK_START.md) - full_analyzer.py 使用说明（推荐先看这个！）
- [AI 增强分析详解](AI_ENHANCED_ANALYSIS.md) - AI 分析架构和使用指南
- [Token 使用分析](TOKEN_USAGE_ANALYSIS.md) - Token 消耗和成本分析（每次分析仅需 ¥0.012）
- [方案对比](IDE_VS_SCRIPT_COMPARISON.md) - Python 脚本 vs IDE + AI 对比
- [问题与商业化分析](CRITICAL_ANALYSIS.md) - 方案缺陷、风险和赚钱可能性
- [Makefile 使用指南](MAKEFILE_USAGE.md) - Makefile 命令详解
- [Conda 环境设置](CONDA_SETUP.md) - Conda 环境配置指南

## 🎯 功能详解

### 1. Serena 多语言代码分析

- **支持语言**：Python、JavaScript、TypeScript、Java、Go、Rust、C/C++、PHP、Ruby、Swift 等 20+ 语言
- **分析内容**：
  - 目录结构和文件分布
  - 代码符号（类、函数、变量）
  - 语言使用比例
  - 项目规模统计
- **输出**：Markdown 和 JSON 双格式报告

### 2. AI 增强深度分析（DeepSeek）

- **成本**：每次分析约 **¥0.01-0.03**（超低成本）
- **分析维度**：
  - 项目架构评估
  - 技术栈现代化程度
  - 代码质量评分（1-10）
  - 潜在问题识别
  - 改进建议（8-15 条）
  - 可扩展性和可维护性分析
  - **Docker 策略建议**（新增）
- **输出**：AI 增强的 Markdown 报告（包含专业建议）

### 3. AI 驱动的 Docker 自动生成

- **智能检测**：
  - 项目类型（Next.js、FastAPI、Django、React、Vue、Go、Java 等）
  - 数据库需求（PostgreSQL、MySQL、MongoDB、Redis）
  - 依赖关系
  - 配置文件
- **AI 优化建议**：
  - 基础镜像选择（alpine、slim、distroless）
  - 多阶段构建策略
  - 端口配置优化
  - 性能和安全优化
  - 健康检查配置
  - CI/CD 集成方案
- **生成文件**：
  - `Dockerfile`
  - `docker-compose.yml`
  - `.dockerignore`
  - `docker-build.sh`
  - `docker-run.sh`
  - `DOCKER_USAGE.md`

### 4. 报告管理

```bash
reports/
├── ai-chat_analysis_20260125.json      # Serena 原始数据
├── ai-chat_analysis_20260125.md        # Serena Markdown 报告
└── ai-chat_analysis_20260125-ai.md     # AI 增强报告（包含 Docker 策略）
```

## 💰 成本分析

### Token 消耗

|| 分析类型 | Tokens | 成本 |
||---------|--------|------|
|| Serena 结构分析 | 0 | ¥0 |
|| AI 代码质量分析 | ~2,500 | ~¥0.005 |
|| AI Docker 策略分析 | ~5,100 | ~¥0.007 |
|| **完整分析** | **~7,600** | **¥0.012** |

### 实际案例（ai-chat 项目）

- **文件数**：49 个（TypeScript 44, JavaScript 5）
- **Token 消耗**：7,500 tokens
- **实际成本**：**¥0.018**（不到 2 分钱）
- **节省时间**：30-60 分钟人工
- **获得价值**：优化的 Next.js Docker 配置 + 15+ 条 AI 建议

### 成本对比

|| 方案 | 成本 | 时间 | 质量 |
||------|------|------|------|
|| Python 脚本 | **¥0.018/次** | 2-3 分钟 | 专业级 |
|| IDE + AI | 免费（有额度限制） | 15-30 分钟 | 依赖提示 |
|| 人工编写 | ¥50-200 | 30-60 分钟 | 参差不齐 |

## 🎬 使用场景

### 场景 1：快速了解新项目
```bash
# 5 分钟获得完整项目分析
export PROJECT_PATH=/path/to/new/project
make analyze-full
# 查看 reports/ 目录下的完整报告
```

### 场景 2：批量分析多个项目
```bash
# 批量分析所有微服务
for dir in services/*/; do
    PROJECT_PATH="$dir" make analyze-full
done
# 自动生成所有项目的报告和 Docker 配置
```

### 场景 3：CI/CD 集成
```yaml
# GitHub Actions 示例
- name: Analyze code
  run: make analyze-full

- name: Build and test
  run: |
    make docker-build
    make docker-run
```

### 场景 4：代码审查辅助
```bash
# 在 PR 前进行 AI 审查
make analyze-full-skip-docker
# 查看 AI 指出的潜在问题和改进建议
# 根据 AI 建议优化代码
```

### 场景 5：容器化现有项目
```bash
# 老项目添加 Docker 支持
export PROJECT_PATH=/path/to/legacy/project
make analyze-full-skip-ai
# AI 自动生成优化的 Docker 配置
# 直接运行：make docker-build && make docker-run
```

## 🔧 技术要求

- **Python**：3.8+
- **Serena MCP**：最新版本
- **AI API**：DeepSeek API Key（或其他 OpenAI 兼容 API）
- **操作系统**：macOS、Linux、Windows（WSL）

## 🤝 贡献

欢迎贡献代码、提交 Issue 或提出改进建议！

## 📄 许可证

MIT License - 详见 LICENSE 文件

## ⭐ Star 历史

如果这个项目对你有帮助，请给它一个 ⭐！

---

**💡 提示**：每个功能的详细说明和文档都在 `docs/` 目录下，建议查看！

**💰 成本提醒**：AI 分析功能需要配置 API Key，每次分析仅需约 ¥0.01-0.03，超低成本！

**🚀 快速开始**：强烈建议先阅读 [QUICK_START.md](QUICK_START.md) 了解一键完整分析工具的使用！
