# 🤖 AI-Powered Code Analysis Tool

An intelligent code analysis toolkit based on **MCP (Model Context Protocol)** and **DeepSeek AI**, providing Serena code structure analysis, AI-driven quality assessment, Docker auto-generation, and end-to-end solutions.

## ✨ Key Features

- 🔍 **Serena Code Structure Analysis** — Multi-language support (20+ languages), intelligent symbol parsing
- 🤖 **AI-Enhanced Analysis** — DeepSeek-powered code quality & architecture evaluation
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
│   ├── __init__.py
│   └── serena_mcp_client.egg-info/  # Package metadata
├── tools/                         # Tool scripts
│   ├── full_analyzer.py           # One-click analysis tool
│   ├── analyze_project_multilang.py  # Multi-language analysis
│   ├── docker_generator.py        # Docker generator
│   ├── ai_enhanced_analyzer.py    # AI-enhanced analyzer (with framework upgrade)
│   ├── analyze_with_ai.py         # AI analysis wrapper
│   └── clean_generated_files.py   # Cleanup tool
├── examples/                      # Example code
│   └── serena_example.py          # Serena usage example
├── reports/                       # Analysis report output
├── tests/                         # Tests
│   └── test_stdio_client.py
├── docs/                          # Documentation
│   ├── FRAMEWORK_UPGRADE.md       # Framework upgrade guide
│   └── UV_GUIDE.md                # uv usage guide
├── pyproject.toml
├── uv.lock
├── setup_uv.sh
├── Makefile
├── README.md                      # This file
└── QUICK_START.md                 # Quick start guide
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

- [Quick Start Guide](QUICK_START.md)
- [AI-Enhanced Analysis](docs/AI_ENHANCED_ANALYSIS.md)
- [Token Usage Analysis](docs/TOKEN_USAGE_ANALYSIS.md)
- [Solution Comparison](docs/IDE_VS_SCRIPT_COMPARISON.md)
- [Makefile Guide](docs/MAKEFILE_USAGE.md)
- [Conda Setup](docs/CONDA_SETUP.md)

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

- **Python**: 3.8+
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
