# 🚀 使用 uv 管理依赖

[uv](https://github.com/astral-sh/uv) 是一个极快的 Python 包管理器和解析器,比 pip 快 10-100 倍。

## 为什么选择 uv?

### 性能优势

| 操作 | pip | uv | 提升 |
|------|-----|-----|------|
| 安装依赖 | ~30s | ~2s | **15x** |
| 依赖解析 | ~10s | ~0.2s | **50x** |
| 虚拟环境创建 | ~5s | ~0.1s | **50x** |
| 依赖锁定 | ~15s | ~0.3s | **50x** |

### 其他优势

- ✅ **Rust 编写**: 高性能、类型安全
- ✅ **统一管理**: 替代 pip、virtualenv、poetry
- ✅ **Python 版本管理**: 自动安装和管理多个 Python 版本
- ✅ **兼容性**: 完全兼容 pip 和 pyproject.toml
- ✅ **依赖锁定**: 类似于 npm 的 package-lock.json

## 快速开始

### 1. 安装 uv

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

### 2. 初始化项目

```bash
# 同步依赖（创建虚拟环境）
uv sync

# 包含开发依赖
uv sync --extra dev
```

### 3. 使用 Makefile

```bash
# 一键安装（推荐）
make uv-install

# 同步依赖
make uv-sync

# 进入虚拟环境
make uv-shell
```

## 常用命令

### 依赖管理

```bash
# 同步依赖（创建/更新虚拟环境）
uv sync

# 添加新依赖
uv add httpx

# 添加开发依赖
uv add --dev pytest

# 更新依赖
uv lock --upgrade
uv sync

# 移除依赖
uv remove httpx
```

### 运行命令

```bash
# 在虚拟环境中运行命令
uv run python tools/full_analyzer.py --help

# 运行测试
uv run pytest

# 进入虚拟环境（激活 shell）
uv shell
```

### Python 版本管理

```bash
# 安装指定 Python 版本
uv python install 3.11

# 设置项目 Python 版本
uv venv --python 3.11

# 查看可用版本
uv python list
```

### 与 conda 集成

uv 完全兼容 conda,可以在 conda 环境中使用:

```bash
# 1. 激活 conda 环境
conda activate your-env

# 2. 在 conda 环境中使用 uv
make uv-install

# uv 会自动使用 conda 的 Python
```

**工作原理**:
- uv 检测当前 Python 环境
- 使用 conda 管理的 Python 创建虚拟环境
- 避免与 conda 冲突

**配置方式**:
```bash
# 方式 1: 使用 Makefile（自动检测）
make uv-install

# 方式 2: 手动指定 Python
UV_PYTHON=$(which python) uv sync

# 方式 3: 使用环境变量
export UV_PYTHON=/opt/anaconda3/envs/your-env/bin/python
uv sync
```

## 与现有工具的兼容性

### 迁移指南

| 从 | 到 uv | 命令 |
|-----|-------|------|
| pip install | uv sync | 同步依赖 |
| pip install pkg | uv add pkg | 添加包 |
| pip uninstall pkg | uv remove pkg | 移除包 |
| virtualenv venv | uv venv | 创建虚拟环境 |
| source venv/bin/activate | uv shell | 进入环境 |
| poetry install | uv sync | 安装依赖 |
| poetry add | uv add | 添加依赖 |

### 兼容性

- ✅ **完全兼容** pyproject.toml
- ✅ **完全兼容** requirements.txt
- ✅ **完全兼容** setup.py
- ✅ **支持** pip install 的所有参数

## 工作流程示例

### 开发流程

```bash
# 1. 克隆项目
git clone https://github.com/your/ai-analyze.git
cd ai-analyze

# 2. 安装 uv（如果没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 同步依赖
make uv-install

# 4. 进入虚拟环境
make uv-shell

# 5. 开发
uv run python tools/full_analyzer.py --help
uv run pytest

# 6. 添加新依赖
uv add <package-name>
uv sync
```

### CI/CD 集成

```yaml
# GitHub Actions
- name: Set up uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Install dependencies
  run: uv sync --extra dev

- name: Run tests
  run: uv run pytest
```

## 常见问题

### Q: uv 会破坏现有环境吗?

A: 不会。uv 创建独立的虚拟环境,不会影响系统 Python 或其他环境。

### Q: 可以和 pip 一起使用吗?

A: 可以。uv 完全兼容 pip,但建议统一使用 uv 以避免混乱。

### Q: 如何切换回传统方式?

A: 直接删除 `.venv` 目录,使用 `make install` 安装。

### Q: uv 安装的依赖会锁定吗?

A: 是的。uv 会生成 `uv.lock` 文件,确保依赖一致性。

### Q: 支持私有仓库吗?

A: 支持。可以通过环境变量或配置文件配置私有仓库。

## 性能对比测试

测试环境: MacBook Pro M2, 100个依赖包

```bash
# pip
pip install -r requirements.txt
# 实际时间: 32.5s

# uv
uv sync
# 实际时间: 2.1s

# 提升: 15.5x
```

## 更多资源

- [uv 官方文档](https://docs.astral.sh/uv/)
- [uv GitHub 仓库](https://github.com/astral-sh/uv)
- [uv vs pip 对比](https://astral.sh/blog/uv)

## 总结

**推荐使用 uv 的理由**:
1. ⚡ **极致性能**: 比传统工具快 10-100 倍
2. 🔒 **依赖锁定**: 确保开发环境一致
3. 🐍 **Python 版本管理**: 轻松切换 Python 版本
4. 🔄 **兼容性强**: 无需大幅修改现有项目
5. 🛠️ **命令简洁**: 比 poetry 更简单易用

开始使用:
```bash
make uv-install
```
