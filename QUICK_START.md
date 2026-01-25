# 一键完整分析工具使用指南

## 概述

`full_analyzer.py` 是一个一键完整分析工具，整合了以下三个步骤：

1. **Serena 代码结构分析** - 使用 MCP Serena 进行代码结构分析
2. **AI 深度分析** - 使用 DeepSeek AI 进行代码质量和 Docker 策略分析
3. **Docker 自动生成** - 基于分析结果生成完整的 Docker 配置

## 使用方法

### 1. 完整分析（推荐）

运行完整的 Serena + AI + Docker 分析流程：

```bash
# 使用 Makefile
make analyze-full

# 或直接运行 Python
python3 tools/full_analyzer.py
```

### 2. 只运行 Serena 分析

跳过 AI 和 Docker，只生成基础的结构分析报告：

```bash
make analyze-full-serena
# 或
python3 tools/full_analyzer.py --serena-only
```

### 3. 跳过 AI 分析

运行 Serena + Docker，不使用 AI 增强分析：

```bash
make analyze-full-skip-ai
# 或
python3 tools/full_analyzer.py --skip-ai
```

### 4. 跳过 Docker 生成

运行 Serena + AI，不生成 Docker 配置：

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

## 生成的文件

### 报告文件（位于 `reports/` 目录）

- `project_name_analysis_YYYYMMDD.json` - Serena 结构分析的 JSON 报告
- `project_name_analysis_YYYYMMDD.md` - Serena 结构分析的 Markdown 报告
- `project_name_analysis_YYYYMMDD-ai.md` - AI 增强分析报告（包含代码质量评估和 Docker 建议）

### Docker 配置文件（位于项目根目录）

- `Dockerfile` - Docker 镜像构建文件
- `docker-compose.yml` - Docker Compose 编排文件
- `.dockerignore` - Docker 忽略文件
- `docker-build.sh` - Docker 镜像构建脚本
- `docker-run.sh` - Docker 容器运行脚本

## 配置要求

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

## 使用示例

### 示例 1：快速分析现有项目

```bash
# 1. 配置项目路径
echo "PROJECT_PATH=~/my-project" >> .env

# 2. 运行完整分析
make analyze-full

# 3. 查看报告
cat reports/*-ai.md

# 4. 构建 Docker 镜像（如果生成成功）
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

### 示例 4：强制更新 Docker 配置

```bash
make analyze-full-force
```

## 注意事项

1. **API Key 配置**：如果未配置 `OPENAI_API_KEY`，AI 分析步骤会自动跳过
2. **Docker 配置冲突**：如果项目已有 Docker 配置，工具会提示是否覆盖
3. **项目路径**：确保 `PROJECT_PATH` 指向正确的项目根目录
4. **时间成本**：完整分析可能需要 30-60 秒，取决于项目大小和网络速度

## Makefile 命令参考

所有一键分析相关的 Makefile 命令：

| 命令 | 描述 |
|------|------|
| `make analyze-full` | 完整分析（Serena + AI + Docker） |
| `make analyze-full-serena` | 只运行 Serena 分析 |
| `make analyze-full-skip-ai` | 跳过 AI，运行 Serena + Docker |
| `make analyze-full-skip-docker` | 跳过 Docker，运行 Serena + AI |
| `make analyze-full-force` | 强制覆盖已有 Docker 配置 |

查看所有可用命令：

```bash
make help
```

## 故障排查

### 问题：Serena 分析失败

**解决方案**：
- 检查 `SERENA_DIR` 是否正确配置
- 确保 Serena 已正确安装

### 问题：AI 分析失败

**解决方案**：
- 检查 `OPENAI_API_KEY` 是否有效
- 确认网络连接正常
- 查看错误日志了解详情

### 问题：Docker 生成失败

**解决方案**：
- 检查项目路径是否正确
- 确保项目有可识别的配置文件（如 `package.json`, `requirements.txt` 等）
- 查看错误日志了解详情

## 费用说明

- AI 分析使用 DeepSeek API，每次分析约消耗 7,600 tokens
- 按当前价格计算，每次分析成本约 ¥0.012（1.2 分）
- 大约可以分析 80+ 次才花费 ¥1

## 更多信息

- [README.md](README.md) - 项目完整文档
- [AI_ENHANCED_ANALYSIS.md](AI_ENHANCED_ANALYSIS.md) - AI 增强分析详细说明
- [TOKEN_USAGE_ANALYSIS.md](TOKEN_USAGE_ANALYSIS.md) - Token 使用情况分析
- [IDE_VS_SCRIPT_COMPARISON.md](IDE_VS_SCRIPT_COMPARISON.md) - IDE vs 脚本对比
- [CRITICAL_ANALYSIS.md](CRITICAL_ANALYSIS.md) - 技术限制和风险分析
