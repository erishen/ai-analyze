# 功能详解

本指南详细介绍了 ai-analyze 的三大核心功能：AST 分析、增量分析和智能 Docker 配置。

---

## 1. AST 代码分析功能

### 概述

AST（Abstract Syntax Tree，抽象语法树）分析是 ai-analyze 的核心功能之一，用于深度分析代码结构、复杂度和代码质量。

### 核心功能

#### 代码复杂度分析

| 复杂度类型 | 说明 | 推荐值 |
|-------------|------|---------|
| **圈复杂度** | 衡量代码的分支复杂度，每增加一个分支（if、for、while、case 等）加 1 | < 10（低复杂度） |
| **认知复杂度** | 衡量代码的认知难度，考虑嵌套深度、递归等因素 | < 15 |
| **嵌套深度** | 代码最大嵌套层级 | < 4 层 |

#### 代码坏味道检测

| 坏味道 | 阈值 | 严重程度 | 建议 |
|---------|--------|----------|------|
| **长方法 (Long Method)** | > 50 行 | 中等 | 将长方法拆分为多个小方法 |
| **大类 (Large Class)** | > 200 行 | 中等 | 考虑使用单一职责原则拆分类 |
| **深层嵌套 (Deep Nesting)** | > 6 层嵌套 | 低 | 使用提前返回、守卫子句等技巧减少嵌套 |

#### 代码指标收集

- **代码行数（LOC）**：实际代码行数
- **注释行数**：注释占比
- **空白行数**：代码可读性指标
- **函数/方法数**：代码模块化程度
- **类数**：面向对象设计指标

### 支持的语言

| 语言 | 支持度 | 分析器 |
|------|--------|--------|
| Python | ✅ 完全支持 | astroid + ast |
| JavaScript | ✅ 完全支持 | 正则表达式 + tree-sitter |
| TypeScript | ✅ 完全支持 | 正则表达式 + tree-sitter |
| Go | ⚠️ 基础支持 | tree-sitter |
| Java | ⚠️ 基础支持 | tree-sitter |
| C/C++ | ⚠️ 基础支持 | tree-sitter |
| Rust | ⚠️ 基础支持 | tree-sitter |

### 使用方法

#### 独立运行 AST 分析

```bash
# 分析单个项目
python tools/ast_analyzer_tool.py /path/to/project

# 指定输出格式
python tools/ast_analyzer_tool.py /path/to/project --format markdown

# 指定输出文件
python tools/ast_analyzer_tool.py /path/to/project --output my_report.json
```

#### 集成到完整分析流程

```bash
# 运行完整分析（包括 AST）
make analyze-full

# 跳过 AST 分析
make analyze-full-skip-ast

# 只运行 AST 分析
make analyze-ast
```

### 输出格式

#### JSON 格式示例

```json
{
  "project_path": "/path/to/project",
  "files": [
    {
      "file_path": "src/main.py",
      "language": "python",
      "functions": [
        {
          "name": "calculate",
          "complexity": {
            "cyclomatic": 5,
            "cognitive": 6,
            "nesting_depth": 2
          }
        }
      ],
      "code_smells": [
        {
          "name": "Long Method",
          "severity": "medium",
          "suggestion": "Consider breaking this function into smaller functions"
        }
      ]
    }
  ]
}
```

#### Markdown 格式

生成的 Markdown 报告包含：
- 项目概览（文件数、函数数、类数等）
- 语言分布表
- 文件详情（每个文件的复杂度、函数列表、类列表）
- 代码坏味道列表
- 改进建议

### 性能优化

| 优化项 | 说明 |
|---------|------|
| **缓存策略** | 支持文件级别的缓存，避免重复分析相同文件 |
| **并发处理** | 支持多进程并行分析，自动检测 CPU 核心数 |
| **内存优化** | 流式处理大文件，增量更新分析结果 |

### 常见问题

**Q: 为什么某些文件分析失败？**

A: 可能原因：
- 文件编码不是 UTF-8
- 文件包含语法错误
- 文件大小超过限制
- 不支持的语言

**Q: 如何提高分析速度？**

A: 
- 增加 `AST_WORKERS` 并发数
- 启用缓存
- 排除不需要分析的目录

**Q: 代码坏味道的阈值可以自定义吗？**

A: 可以，编辑 `src/ast_analyzer.py` 中的阈值常量。

---

## 2. 增量分析

### 概述

增量分析缓存分析结果，只重新分析变化的文件。这可以显著加速 CI/CD 流程和本地开发工作流。

**性能提升**：CI/CD 环境下性能提升 **+80%**

### 快速开始

#### 默认行为（增量分析已启用）

```bash
python tools/full_analyzer.py
```

- 自动检测文件变化
- 对未变化的文件使用缓存结果
- 只重新分析修改/新增的文件
- 将结果保存到缓存供下次使用

#### 禁用增量分析

```bash
python tools/full_analyzer.py --no-incremental
```

- 强制完整重新分析所有文件
- 适用于基线测量或故障排查

#### 清除缓存

```bash
python tools/full_analyzer.py --clear-cache
```

- 删除所有缓存的分析结果
- 下次运行将执行完整分析

### 工作原理

#### 第一次运行

```
Input: 项目文件
    ↓
完整分析 (Serena + AST)
    ↓
保存结果 + 文件哈希到缓存
    ↓
Output: 分析报告
```

#### 后续运行（无变化）

```
Input: 项目文件
    ↓
对比文件哈希与缓存
    ↓
未检测到变化
    ↓
使用缓存结果
    ↓
Output: 分析报告 (即时)
```

#### 后续运行（有变化）

```
Input: 项目文件
    ↓
对比文件哈希与缓存
    ↓
检测到变化:
  - 修改: 3 个文件
  - 新增: 2 个文件
  - 删除: 1 个文件
    ↓
只重新分析变化的文件
    ↓
与缓存结果合并
    ↓
保存更新的缓存
    ↓
Output: 分析报告
```

### 缓存管理

#### 缓存位置

- 默认目录：`.ai-analyze-cache/`
- 格式：`{project_hash}_cache.json`
- 每个项目有自己的缓存文件

#### 缓存内容

- 项目路径和元数据
- 文件哈希（MD5）
- 缓存的分析结果
- 时间戳（创建、更新）

#### 查看缓存统计

```bash
python -c "
from src.incremental_analyzer import IncrementalAnalyzer
inc = IncrementalAnalyzer()
stats = inc.get_cache_stats()
print(f'缓存文件: {stats[\"cache_files\"]}')
print(f'缓存大小: {stats[\"size_mb\"]:.2f} MB')
"
```

### 性能示例

| 场景 | 无增量分析 | 有增量分析 | 加速 |
|------|-----------|-----------|------|
| **无变化** | 50 秒 | <1 秒 | **50x** |
| **单个文件变化** (共 1000 个文件) | 50 秒 | 5 秒 | **10x** |
| **10% 文件变化** (共 100 个文件) | 50 秒 | 10 秒 | **5x** |

### 使用场景

#### 1. 本地开发

```bash
# 第一次分析
python tools/full_analyzer.py

# 编辑文件后
python tools/full_analyzer.py  # 只重新分析变化的文件
```

#### 2. CI/CD 流水线

```bash
# 在 CI/CD 脚本中
python tools/full_analyzer.py

# 缓存在运行之间持久化
# 只重新分析变化的文件
# 显著加速增量提交
```

#### 3. 基线测量

```bash
# 清除缓存以获得干净的基线
python tools/full_analyzer.py --clear-cache

# 运行完整分析
python tools/full_analyzer.py --no-incremental
```

### CI/CD 集成

#### GitHub Actions 示例

```yaml
- name: 运行 AI 分析
  run: |
    python tools/full_analyzer.py --yes

- name: 缓存分析结果
  uses: actions/cache@v3
  with:
    path: .ai-analyze-cache
    key: ai-analyze-${{ github.sha }}
    restore-keys: ai-analyze-
```

#### GitLab CI 示例

```yaml
analyze:
  script:
    - python tools/full_analyzer.py --yes
  cache:
    paths:
      - .ai-analyze-cache/
```

### 性能优化建议

1. **启用增量分析**（默认）：对迭代开发最快
2. **在 CI/CD 中使用缓存**：在运行之间持久化 `.ai-analyze-cache/`
3. **定期清除缓存**：防止过时结果（每周/每月）
4. **监控缓存大小**：使用 `get_cache_stats()` 跟踪增长

### 常见问题

**Q: 缓存似乎过时了？**

A: 清除缓存并重新运行：
```bash
python tools/full_analyzer.py --clear-cache
python tools/full_analyzer.py
```

**Q: 如何强制完整分析？**

A: 使用 `--no-incremental` 标志：
```bash
python tools/full_analyzer.py --no-incremental
```

**Q: 如何验证缓存是否工作？**

A: 检查输出中的缓存状态消息：
```
📊 增量分析状态: 没有文件变化，可以使用缓存
✅ 使用缓存结果，跳过分析
```

---

## 3. 智能 Docker 配置

### 概述

智能 Docker 配置自动分析代码复杂度，并生成优化的 Docker 配置，配置合适的资源分配。这确保容器拥有适量的资源——不会太少（导致性能问题），也不会太多（浪费资金）。

**效率提升**：容器效率提升 **+10-15%**，成本节省 **20-30%**

### 快速开始

#### 1. 运行完整分析

```bash
python tools/full_analyzer.py
```

这将：
- 分析代码结构（Serena）
- 分析代码复杂度（AST）
- 生成优化的 Docker 配置
- 创建资源分配报告

#### 2. 查看资源报告

```bash
python -c "
from tools.smart_docker_config import SmartDockerConfig
import json

# 加载分析数据
with open('reports/analysis.json') as f:
    data = json.load(f)

# 生成报告
config = SmartDockerConfig('.')
report = config.generate_resource_report(data)
print(report)
"
```

#### 3. 使用生成的 Docker 文件

```bash
# 构建镜像
./docker-build.sh

# 运行容器
./docker-run.sh
```

### 资源配置文件

| 配置级别 | CPU 限制 | 内存限制 | 适用场景 | 成本 |
|-----------|----------|----------|----------|------|
| **Minimal (极小型)** | 0.5 核 | 256 MB | 简单脚本、静态网站、最小服务 | 最低 |
| **Small (小型)** | 1 核 | 512 MB | 低复杂度项目、简单应用 | 低 |
| **Medium (中型)** | 2 核 | 1 GB | 中等复杂度项目、典型应用 | 中等 |
| **Large (大型)** | 4 核 | 2 GB | 高复杂度项目、需求高的应用 | 高 |
| **XLarge (超大型)** | 8 核 | 4 GB | 极高复杂度项目、企业级应用 | 最高 |

### 如何计算复杂度

系统分析四个关键指标（总分 0-100）：

| 指标 | 分数范围 | 评分标准 |
|-------|---------|---------|
| **文件数量** (0-25 分) | 5/10/15/20/25 | <10 / 10-50 / 50-100 / 100-500 / >500 |
| **平均复杂度** (0-25 分) | 5/10/15/20/25 | <5 / 5-10 / 10-20 / 20-50 / >50 |
| **最大复杂度** (0-25 分) | 5/10/15/20/25 | <10 / 10-30 / 30-100 / 100-300 / >300 |
| **代码质量** (0-25 分) | 25/20/15/10/5 | 0 / 1-5 / 5-20 / 20-50 / >50 个代码坏味道 |

**总分**：0-100 → 分类：minimal/small/medium/large/xlarge

### 生成的 Docker Compose

```yaml
version: '3.8'

services:
  myapp:
    image: python:3.12
    container_name: myapp
    ports:
      - "8000:8000"
    
    # 基于复杂度的资源限制
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1g
        reservations:
          cpus: '0.5'
          memory: 512m
    
    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
    
    restart: unless-stopped
```

### 关键特性

- **资源限制**：容器可使用的最大资源
- **资源请求**：保证的最小资源
- **健康检查**：自动容器健康监控
- **重启策略**：失败时自动恢复
- **日志**：带轮转的结构化日志

### 成本优化

#### 节省示例

| 项目类型 | 默认配置 | 智能 Docker | 节省 |
|---------|----------|-------------|------|
| **极小型项目** (静态网站) | 2 CPU, 1 GB | 0.5 CPU, 256 MB | **75%** |
| **小型项目** (简单 API) | 2 CPU, 1 GB | 1 CPU, 512 MB | **50%** |
| **中型项目** (典型应用) | 4 CPU, 2 GB | 2 CPU, 1 GB | **50%** |
| **大型项目** (复杂系统) | 4 CPU, 2 GB | 4 CPU, 2 GB | **0% (已最优)** |

#### 总体成本影响
- 典型节省：基础设施成本的 **20-30%**
- 改善资源利用率
- 更好的自动扩展决策
- 减少云提供商账单

### 高级用法

#### 自定义资源配置文件

```python
from tools.smart_docker_config import SmartDockerConfig, ResourceProfile

config = SmartDockerConfig('.')

# 创建自定义配置文件
custom_profile = ResourceProfile(
    name='custom',
    cpu_limit='3',
    memory_limit='1.5g',
    memory_request='750m',
    cpu_request='0.75',
    description='自定义配置'
)

# 使用自定义配置文件
compose = config.generate_docker_compose(
    'myapp',
    'python:3.12',
    8000,
    analysis_data
)
```

#### 程序化访问

```python
from tools.smart_docker_config import SmartDockerConfig
import json

# 加载分析
with open('reports/analysis.json') as f:
    data = json.load(f)

# 创建配置
config = SmartDockerConfig('.')

# 获取指标
metrics = config.analyze_complexity(data)
print(f"复杂度: {metrics['complexity_level']}")
print(f"文件数: {metrics['file_count']}")
print(f"质量分数: {metrics['quality_score']}")

# 获取配置文件
profile = config.get_resource_profile(data)
print(f"配置文件: {profile.name}")
print(f"CPU: {profile.cpu_limit}")
print(f"内存: {profile.memory_limit}")
```

### 常见问题

**Q: 为什么我的项目被分类为 "large"？**

A: 检查指标：
- 高文件数量（>100）
- 高平均复杂度（>20）
- 多个代码坏味道（>10）
- 低质量分数（<70）

考虑重构以降低复杂度。

**Q: 可以覆盖分类吗？**

A: 可以，创建自定义配置文件或修改生成的 docker-compose.yml：
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 2g
```

**Q: 这适用于所有语言吗？**

A: 是的！系统分析：
- Python
- JavaScript/TypeScript
- Go
- Java
- Rust
- C/C++
- 以及更多...

### 最佳实践

1. **定期运行分析**：保持资源分配是最新的
2. **监控性能**：跟踪实际 vs 分配的资源
3. **按需调整**：根据实际使用情况修改配置文件
4. **使用健康检查**：启用自动恢复
5. **设置重启策略**：确保高可用性
6. **审查建议**：执行优化建议
7. **生产前测试**：先在暂存环境验证

### CI/CD 集成

#### GitHub Actions

```yaml
- name: 生成智能 Docker 配置
  run: python tools/full_analyzer.py

- name: 构建和推送
  run: ./docker-build.sh
```

#### GitLab CI

```yaml
docker_build:
  script:
    - python tools/full_analyzer.py
    - ./docker-build.sh
```

---

## 总结

ai-analyze 提供三大核心功能：

| 功能 | 主要特点 | 性能提升 |
|------|---------|----------|
| **AST 分析** | 深度代码结构分析、复杂度度量、坏味道检测 | 基础分析能力 |
| **增量分析** | 缓存分析结果、只重新分析变化文件 | CI/CD +80% |
| **智能 Docker** | 自动资源分配、成本优化 | 容器效率 +10-15%，成本节省 20-30% |

开始使用这些功能，加速您的代码分析和容器部署！

---

## 更多信息

- [QUICK_START.md](QUICK_START.md) - 快速开始指南
- [OPTIMIZATION_HISTORY.md](OPTIMIZATION_HISTORY.md) - 优化历程和性能提升
- [INDEX.md](INDEX.md) - 完整文档索引
- [README.md](../README.md) - 项目完整文档
