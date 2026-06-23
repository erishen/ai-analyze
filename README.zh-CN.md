<div align="right">
  <a href="README.md">🇺🇸 English</a>
</div>

# AI-Analyze

基于 **AST 分析 + MCP 协议** 的代码分析工具，提供代码质量评估、安全扫描、PR 审查、趋势追踪和 Docker 配置生成。

## 核心特性

- **AST 代码分析** — Python 完整支持、JS/TS 简化实现，确定性输出
- **安全扫描** — 12 条安全规则（SQL 注入、硬编码密钥、命令注入、XSS 等）
- **质量评分** — 4 维度加权评分（复杂度、可维护性、安全性、可读性）
- **PR Diff 分析** — 增量质量评估，风险等级和审查建议
- **趋势追踪** — SQLite 持久化，代码质量变化一目了然
- **MCP Server** — STDIO/SSE 传输，AI Agent 直接调用分析能力
- **SARIF 输出** — GitHub Code Scanning 集成
- **Docker 生成** — 文件扫描 + 模板匹配，确定性输出
- **插件系统** — 自定义分析规则扩展

## 项目结构

```
src/
├── analyzers/           # 分析器
│   ├── ast_analyzer.py      # AST 代码分析（7 种语言）
│   ├── ast_rules.py         # AST 分析规则
│   ├── security_scanner.py  # 安全漏洞扫描（12 条规则）
│   ├── quality_score.py     # 代码质量评分
│   ├── similarity.py        # 代码相似度检测
│   ├── tech_debt.py         # 技术债务追踪
│   ├── dependency_graph.py  # 依赖图构建
│   └── performance_analyzer.py  # 性能分析
├── backends/            # 语言后端
│   ├── language_backend.py  # 插件化后端（TreeSitter / Serena）
│   ├── serena_client.py     # Serena MCP 客户端
│   └── serena_stdio_client.py  # Serena Stdio 客户端
├── infrastructure/      # 基础设施
│   ├── config.py            # 配置管理
│   ├── logger.py            # 结构化日志
│   ├── multi_level_cache.py # 三级缓存（内存→文件→Redis）
│   ├── incremental_analyzer.py  # 增量分析
│   ├── exceptions.py        # 自定义异常
│   ├── retry.py             # 重试与退避
│   ├── progress.py          # 进度追踪
│   ├── memory.py            # 内存管理
│   ├── cache_warmer.py      # 缓存预热
│   └── benchmark.py         # 性能基准
├── reports/             # 报告输出
│   ├── report_system.py     # 报告生成系统
│   ├── sarif_report.py      # SARIF 2.1.0 输出
│   └── ast_visualizer.py    # AST 可视化
├── server/              # 服务端
│   ├── mcp_server.py        # MCP Server（STDIO/SSE）
│   ├── analysis_api.py      # REST API
│   └── analysis_integration.py  # 分析集成层
└── tools/               # 工具和集成
    ├── cli.py               # CLI 入口
    ├── data_store.py        # SQLite 持久化
    ├── pr_diff.py           # PR Diff 分析
    ├── plugin_system.py     # 插件系统
    └── unified_analyzer.py  # 统一分析引擎
```

## 快速开始

### 安装

```bash
pip install -e .
```

### CLI 使用

```bash
# 分析项目
ai-analyze ast /path/to/project

# PR 审查
ai-analyze diff /path/to/project --base main --head feature-branch

# 查看分析历史
ai-analyze history my-project

# 查看趋势
ai-analyze trend my-project --metric summary.total_code_smells

# 启动 MCP Server
ai-analyze serve --transport stdio
ai-analyze serve --transport sse --port 8000

# SARIF 输出
ai-analyze ast /path/to/project --sarif
```

### Docker 生成

```bash
python tools/docker_generator.py /path/to/project
```

自动检测项目类型，生成 Dockerfile、docker-compose.yml、.dockerignore。

## MCP Server

ai-analyze 可作为 MCP Server 运行，供 AI Agent 直接调用分析能力。

### 可用 Tools

| Tool | 说明 |
|------|------|
| `analyze_project` | 全量项目分析（安全、质量、依赖、AST） |
| `scan_security` | 安全漏洞扫描 |
| `analyze_quality` | 代码质量评分（0-100，A-F 等级） |
| `analyze_ast` | 单文件 AST 分析（复杂度、代码坏味道） |
| `detect_similarities` | 重复和相似代码检测 |
| `analyze_dependencies` | 模块依赖图分析 |

### 配置

添加到 MCP 客户端配置（Claude Desktop、Cursor、Trae 等）：

```json
{
  "mcpServers": {
    "ai-analyze": {
      "command": "ai-analyze",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

或使用 uv：

```json
{
  "mcpServers": {
    "ai-analyze": {
      "command": "uv",
      "args": ["run", "ai-analyze", "serve", "--transport", "stdio"],
      "cwd": "/path/to/ai-analyze"
    }
  }
}
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
make test

# 代码检查
make lint

# 格式化
make format
```

## 技术要求

- **Python** 3.10+
- **tree-sitter** >= 0.21.0（AST 分析）
- **litellm** >= 1.0.0（AI 分析，支持 100+ LLM 提供商）
- **Serena**（可选，通过 MCP 协议提供更强的语义分析）
- **Redis**（可选，三级缓存的 L3 层）

## 许可证

MIT License
