<div align="right">
  <a href="README.zh-CN.md">🇨🇳 中文</a>
</div>

# AI-Analyze

A code analysis toolkit based on **AST analysis + MCP protocol**, providing code quality assessment, security scanning, PR review, trend tracking, and Docker config generation.

## Key Features

- **AST Code Analysis** — Full Python support, simplified JS/TS, deterministic output
- **Security Scanning** — 12 security rules (SQL injection, hardcoded secrets, command injection, XSS, etc.)
- **Quality Scoring** — 4-dimension weighted scoring (complexity, maintainability, security, readability)
- **PR Diff Analysis** — Incremental quality assessment with risk level and review suggestions
- **Trend Tracking** — SQLite persistence, code quality changes at a glance
- **MCP Server** — STDIO/SSE transport, AI agents can call analysis capabilities directly
- **SARIF Output** — GitHub Code Scanning integration
- **Docker Generation** — File scanning + template matching, deterministic output
- **Plugin System** — Custom analysis rule extensions

## Project Structure

```
src/
├── analyzers/           # Analyzers
│   ├── ast_analyzer.py      # AST code analysis (7 languages)
│   ├── ast_rules.py         # AST analysis rules
│   ├── security_scanner.py  # Security vulnerability scanning (12 rules)
│   ├── quality_score.py     # Code quality scoring
│   ├── similarity.py        # Code similarity detection
│   ├── tech_debt.py         # Technical debt tracking
│   ├── dependency_graph.py  # Dependency graph builder
│   └── performance_analyzer.py  # Performance analysis
├── backends/            # Language backends
│   ├── language_backend.py  # Pluggable backend (TreeSitter / Serena)
│   ├── serena_client.py     # Serena MCP client
│   └── serena_stdio_client.py  # Serena Stdio client
├── infrastructure/      # Infrastructure
│   ├── config.py            # Configuration management
│   ├── logger.py            # Structured logging
│   ├── multi_level_cache.py # 3-level cache (memory→file→Redis)
│   ├── incremental_analyzer.py  # Incremental analysis
│   ├── exceptions.py        # Custom exceptions
│   ├── retry.py             # Retry with backoff
│   ├── progress.py          # Progress tracking
│   ├── memory.py            # Memory management
│   ├── cache_warmer.py      # Cache pre-warming
│   └── benchmark.py         # Performance benchmarking
├── reports/             # Report output
│   ├── report_system.py     # Report generation system
│   ├── sarif_report.py      # SARIF 2.1.0 output
│   └── ast_visualizer.py    # AST visualization
├── server/              # Server
│   ├── mcp_server.py        # MCP Server (STDIO/SSE)
│   ├── analysis_api.py      # REST API
│   └── analysis_integration.py  # Analysis integration layer
└── tools/               # Tools and integration
    ├── cli.py               # CLI entry point
    ├── data_store.py        # SQLite persistence
    ├── pr_diff.py           # PR Diff analysis
    ├── plugin_system.py     # Plugin system
    └── unified_analyzer.py  # Unified analysis engine
```

## Quick Start

### Install

```bash
pip install -e .
```

### CLI Usage

```bash
# Analyze project
ai-analyze ast /path/to/project

# PR review
ai-analyze diff /path/to/project --base main --head feature-branch

# View analysis history
ai-analyze history my-project

# View trends
ai-analyze trend my-project --metric summary.total_code_smells

# Start MCP Server
ai-analyze serve --transport stdio
ai-analyze serve --transport sse --port 8000

# SARIF output
ai-analyze ast /path/to/project --sarif
```

### Docker Generation

```bash
python tools/docker_generator.py /path/to/project
```

Auto-detect project type and generate Dockerfile, docker-compose.yml, .dockerignore.

## MCP Server

ai-analyze can run as an MCP Server, allowing AI agents to call analysis capabilities directly.

### Available Tools

| Tool | Description |
|------|-------------|
| `analyze_project` | Full project analysis (security, quality, dependency, AST) |
| `scan_security` | Security vulnerability scanning |
| `analyze_quality` | Code quality scoring (0-100, A-F grade) |
| `analyze_ast` | Single file AST analysis (complexity, code smells) |
| `detect_similarities` | Duplicate and similar code detection |
| `analyze_dependencies` | Module dependency graph analysis |

### Configuration

Add to your MCP client config (Claude Desktop, Cursor, Trae, etc.):

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

Or with `uv`:

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

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
make test

# Lint
make lint

# Format
make format
```

## Requirements

- **Python** 3.10+
- **tree-sitter** >= 0.21.0 (AST analysis)
- **litellm** >= 1.0.0 (AI analysis, supports 100+ LLM providers)
- **Serena** (optional, provides stronger semantic analysis via MCP protocol)
- **Redis** (optional, L3 cache layer)

## License

MIT
