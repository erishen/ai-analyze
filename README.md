<div align="right">
  <a href="README.zh-CN.md">🇨🇳 中文</a>
</div>

# AI-Powered Code Analysis Tool

An intelligent code analysis toolkit based on **MCP (Model Context Protocol)** and **DeepSeek AI**, providing Serena code structure analysis, AI-driven quality assessment, Docker auto-generation, and end-to-end solutions.

## ✨ Key Features

- 🔍 **Serena Code Structure Analysis** — Multi-language support (20+ languages), intelligent symbol parsing
- 🤖 **AI-Enhanced Analysis** — DeepSeek-powered code quality & architecture evaluation
- 🔌 **MCP Server** — Expose analysis capabilities as MCP Tools for AI agents (Claude, Cursor, Trae, etc.)
- 🐳 **Docker Auto-Generation** — AI-driven, intelligent containerization recommendations
- 💰 **Ultra-Low Cost** — ~¥0.01-0.03 per full analysis
- ⚡ **One-Click Automation** — Makefile-driven, 2-3 minutes for complete workflow
- 📊 **Multi-Format Reports** — Markdown + JSON dual output
- 🎯 **Smart Optimization** — 15+ optimization dimensions based on best practices

## 📦 Project Structure

```
.
├── src/                           # Source code
│   ├── serena_client.py           # Serena MCP client
│   ├── serena_stdio_client.py     # Stdio communication client
│   ├── unified_analyzer.py        # Unified analysis engine
│   ├── analysis_api.py            # Analysis REST API
│   ├── analysis_integration.py    # Analysis integration layer
│   ├── ast_analyzer.py            # AST-based code analyzer
│   ├── ast_rules.py               # AST analysis rules
│   ├── ast_visualizer.py          # AST visualization
│   ├── benchmark.py               # Performance benchmarking
│   ├── cache_warmer.py            # Cache pre-warming
│   ├── config.py                  # Configuration management
│   ├── data_store.py              # Data persistence
│   ├── dependency_graph.py        # Dependency graph builder
│   ├── exceptions.py              # Custom exception hierarchy
│   ├── incremental_analyzer.py    # Incremental analysis
│   ├── logger.py                  # Structured logging
│   ├── memory.py                  # Memory management
│   ├── multi_level_cache.py       # Multi-level cache system
│   ├── performance_analyzer.py    # Performance analysis
│   ├── plugin_system.py           # Plugin architecture
│   ├── progress.py                # Progress tracking
│   ├── quality_score.py           # Code quality scoring
│   ├── report_system.py           # Report generation
│   ├── retry.py                   # Retry with backoff
│   ├── security_scanner.py        # Security vulnerability scanner
│   ├── similarity.py              # Code similarity detection
│   ├── tech_debt.py               # Technical debt tracker
│   └── __init__.py
├── tools/                         # Tool scripts
│   ├── full_analyzer.py           # One-click analysis tool
│   ├── analyze_project_multilang.py  # Multi-language analysis
│   ├── docker_generator.py        # Docker generator
│   ├── smart_docker_config.py     # Smart Docker configuration
│   ├── ai_enhanced_analyzer.py    # AI-enhanced analyzer (with framework upgrade)
│   ├── analyze_with_ai.py         # AI analysis wrapper
│   ├── ast_analyzer_tool.py       # AST analyzer CLI tool
│   └── clean_generated_files.py   # Cleanup tool
├── tests/                         # Test suite (30+ test files)
│   ├── test_serena_client.py
│   ├── test_unified_analyzer.py
│   ├── test_ast_analyzer.py
│   ├── test_security_scanner.py
│   ├── test_quality_score.py
│   ├── test_dependency_graph.py
│   └── ...
├── examples/                      # Example code
│   └── serena_example.py          # Serena usage example
├── docs/                          # Documentation
│   ├── FEATURES.md                # Feature overview
│   ├── INDEX.md                   # Documentation index
│   ├── OPTIMIZATION_HISTORY.md    # Optimization history
│   └── QUICK_START.md             # Quick start guide
├── scripts/                       # CI/CD scripts
│   └── ci-verify.sh               # CI verification
├── .github/workflows/             # GitHub Actions
│   ├── ci.yml                     # CI pipeline
│   └── publish.yml                # Publish pipeline
├── reports/                       # Analysis report output
├── pyproject.toml                 # Project config
├── Makefile                       # Build commands (35+)
├── .env.example                   # Environment template
└── README.md                      # This file
```

## 🚀 Quick Start

### Prerequisites

⚠️ **Two steps required before use**:

1. **Download Serena MCP**
   ```bash
   git clone git@github.com:oraios/serena.git
   cd serena
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -e .
   python -m serena --version
   ```

2. **Configure DeepSeek API Key**
   ```bash
   cp .env.example .env
   # Edit .env:
   OPENAI_API_KEY=sk-your-deepseek-api-key-here
   OPENAI_BASE_URL=https://api.deepseek.com
   OPENAI_MODEL=deepseek-chat
   PROJECT_PATH=/path/to/your/project
   ```

### 1. Install Dependencies

#### Option 1: uv (recommended)

```bash
make uv-install
# Or manually:
uv sync
uv sync --extra dev
uv shell
```

#### Option 2: pip

```bash
make install
# Or:
pip install -e .
```

**uv vs pip performance**:
| Operation | pip | uv | Improvement |
|-----------|-----|-----|-------------|
| Install | ~30s | ~2s | 15x |
| Resolve | ~10s | ~0.2s | 50x |
| Venv create | ~5s | ~0.1s | 50x |

### 2. Configure Environment

```bash
cp .env.example .env
# Configure:
# - PROJECT_PATH: target project path
# - OPENAI_API_KEY: DeepSeek API key
# - OPENAI_BASE_URL: https://api.deepseek.com
# - OPENAI_MODEL: deepseek-chat
```

### 3. One-Click Full Analysis

```bash
# Full: Serena + AI + Docker
make analyze-full

# Serena only
make analyze-full-serena

# Skip AI, run Serena + Docker
make analyze-full-skip-ai

# Skip Docker, run Serena + AI
make analyze-full-skip-docker

# Force overwrite existing Docker config
make analyze-full-force
```

### 4. Individual Features

```bash
# AI enhancement only (with existing Serena report)
make analyze-ai-only REPORT=reports/your_report.json

# Docker config only
make docker-generate

# Build and run Docker
make docker-build
make docker-run
```

## 📋 Available Commands (35+)

Run `make help` to see all commands.

### 🔍 One-Click Analysis

| Command | Description | AI Cost |
|---------|-------------|---------|
| `make analyze-full` | Full: Serena + AI + Docker | ~¥0.017 |
| `make analyze-full-serena` | Serena only | ¥0 |
| `make analyze-full-skip-ai` | Serena + Docker | ¥0 |
| `make analyze-full-skip-docker` | Serena + AI | ~¥0.017 |
| `make analyze-full-force` | Force overwrite Docker config | ~¥0.017 |

### 🔍 Core Analysis

| Command | Description | AI Cost |
|---------|-------------|---------|
| `make analyze-ai` | AI-enhanced analysis (full flow) | ~¥0.017 |
| `make analyze-skip-ai` | Serena only | ¥0 |
| `make analyze-ai-only` | AI enhancement on existing report | ~¥0.017 |
| `make analyze` | Markdown report (multi-language) | ¥0 |
| `make analyze-json` | JSON report (multi-language) | ¥0 |

### 🐳 Docker Commands

| Command | Description |
|---------|-------------|
| `make docker-check` | Check Docker config |
| `make docker-generate` | Generate Docker config (AI) |
| `make docker-build` | Build Docker image |
| `make docker-run` | Run Docker container |
| `make docker-compose-up` | Start docker-compose |
| `make docker-compose-down` | Stop docker-compose |

### 🧹 Cleanup

| Command | Description |
|---------|-------------|
| `make clean` | Clean cache and temp files |
| `make clean-reports` | Clean old reports |
| `make clean-all` | Clean all generated files |

### 🛠️ Development

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies |
| `make test` | Run tests |
| `make lint` | Lint code |
| `make format` | Format code |
| `make debug` | Show debug info |

## 📖 Documentation

- [Quick Start Guide](docs/QUICK_START.md)
- [Feature Overview](docs/FEATURES.md)
- [Optimization History](docs/OPTIMIZATION_HISTORY.md)
- [Documentation Index](docs/INDEX.md)

## 🔌 MCP Server

ai-analyze can run as an MCP Server, exposing analysis capabilities as tools for AI agents (Claude, Cursor, Trae, etc.).

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `analyze_project` | Full project analysis (security, quality, dependency, AST) |
| `scan_security` | Security vulnerability scanning |
| `analyze_quality` | Code quality scoring (0-100, A-F grade) |
| `analyze_ast` | Single file AST analysis (complexity, code smells) |
| `detect_similarities` | Duplicate and similar code detection |
| `analyze_dependencies` | Module dependency graph analysis |

### Start MCP Server

```bash
# Via CLI entry point
ai-analyze-mcp

# Or directly
python -m src.mcp_server
```

### Configure in AI Agents

Add to your MCP client configuration (e.g., Claude Desktop, Cursor, Trae):

```json
{
  "mcpServers": {
    "ai-analyze": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "/path/to/ai-analyze"
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
      "args": ["run", "python", "-m", "src.mcp_server"],
      "cwd": "/path/to/ai-analyze"
    }
  }
}
```

## 🎯 Feature Details

### 1. Serena Multi-Language Code Analysis

- **Supported Languages**: Python, JavaScript, TypeScript, Java, Go, Rust, C/C++, PHP, Ruby, Swift, and 20+ more
- **Analysis Scope**:
  - Directory structure and file distribution
  - Code symbols (classes, functions, variables)
  - Language usage ratios
  - Project size statistics
- **Output**: Markdown + JSON dual-format reports

### 2. AI-Enhanced Deep Analysis (DeepSeek)

- **Cost**: ~¥0.01-0.03 per analysis
- **Dimensions**:
  - Project architecture evaluation
  - Tech stack modernization
  - Code quality score (1-10)
  - Potential issue identification
  - Improvement suggestions (8-15 items)
  - Scalability and maintainability analysis
  - **Docker strategy recommendations**
  - **Framework upgrade suggestions**
- **Output**: AI-enhanced Markdown reports

### 3. AI-Driven Docker Auto-Generation

- **Smart Detection**:
  - Project type (Next.js, FastAPI, Django, React, Vue, Go, Java, etc.)
  - Database requirements (PostgreSQL, MySQL, MongoDB, Redis)
  - Dependencies and config files
  - Smart npm/pnpm choice based on lockfile
- **AI Optimization**:
  - Base image selection (alpine, slim, distroless)
  - Multi-stage build strategy
  - Port and security optimization
  - Health check configuration
  - CI/CD integration
- **Generated Files**:
  - `Dockerfile`, `docker-compose.yml`, `.dockerignore`
  - `docker-build.sh`, `docker-run.sh`, `DOCKER_USAGE.md`

### 4. Report Management

```
reports/
├── project_analysis_20260125.json      # Serena raw data
├── project_analysis_20260125.md        # Serena Markdown report
└── project_analysis_20260125-ai.md     # AI-enhanced report
```

## 💰 Cost Analysis

### Token Usage

| Analysis Type | Tokens | Cost |
|--------------|--------|------|
| Serena Structure | 0 | ¥0 |
| AI Code Quality | ~2,500 | ~¥0.005 |
| AI Docker Strategy | ~5,100 | ~¥0.007 |
| AI Framework Upgrade | ~2,500 | ~¥0.005 |
| **Full Analysis** | **~10,100** | **~¥0.017** |

### Cost Comparison

| Approach | Cost | Time | Quality |
|----------|------|------|---------|
| Python Script | **¥0.018/run** | 2-3 min | Professional |
| IDE + AI | Free (limited) | 15-30 min | Prompt-dependent |
| Manual | ¥50-200 | 30-60 min | Inconsistent |

## 🎬 Use Cases

### Quick Project Onboarding
```bash
export PROJECT_PATH=/path/to/new/project
make analyze-full
```

### Batch Analysis
```bash
for dir in services/*/; do
    PROJECT_PATH="$dir" make analyze-full
done
```

### CI/CD Integration
```yaml
- name: Analyze code
  run: make analyze-full
- name: Build and test
  run: |
    make docker-build
    make docker-run
```

### Code Review Assistant
```bash
make analyze-full-skip-docker
# Review AI suggestions
```

### Containerize Legacy Projects
```bash
export PROJECT_PATH=/path/to/legacy/project
make analyze-full-skip-ai
make docker-build && make docker-run
```

## 🔧 Requirements

- **Python**: 3.9+
- **Serena MCP**: Latest
- **AI API**: DeepSeek API Key (or OpenAI-compatible)
- **OS**: macOS, Linux, Windows (WSL)

## 🤝 Contributing

Issues and pull requests are welcome!

## 📄 License

MIT

---

**💡 Tip**: Detailed documentation is available in the `docs/` directory.

**💰 Cost Reminder**: AI analysis requires an API key — each run costs only ~¥0.01-0.03.
