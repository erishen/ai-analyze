#!/usr/bin/env python3
"""Docker 配置生成器 - 基于规则的智能生成"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class DockerGenerator:
    """Docker 配置生成器 - 基于项目文件智能检测配置"""

    # 项目类型到基础镜像的映射
    BASE_IMAGES = {
        'nextjs': 'node:20-alpine',
        'nextjs-bun': 'oven/bun:1-alpine',
        'react': 'node:20-alpine',
        'vue': 'node:20-alpine',
        'angular': 'node:20-alpine',
        'express': 'node:20-alpine',
        'nuxt': 'node:20-alpine',
        'node': 'node:20-alpine',
        'static': 'nginx:alpine',
        'fastapi': 'python:3.12-slim',
        'python': 'python:3.12-slim',
        'gin': 'golang:1.22-alpine',
        'go': 'golang:1.22-alpine',
        'rust': 'rust:1.75-alpine',
        'java': 'eclipse-temurin:21-jre-alpine',
    }

    # 项目类型到默认端口的映射
    DEFAULT_PORTS = {
        'nextjs': 3000,
        'react': 3000,
        'vue': 3000,
        'angular': 4200,
        'express': 3000,
        'nuxt': 3000,
        'node': 3000,
        'static': 80,
        'fastapi': 8000,
        'python': 8000,
        'gin': 8080,
        'go': 8080,
        'rust': 8080,
        'java': 8080,
    }

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.generated_files = []
        self._package_json_cache: Optional[Dict] = None
        self._env_cache: Optional[Dict[str, str]] = None

    def has_docker_config(self) -> Tuple[bool, List[str]]:
        """检查是否已有 Docker 配置"""
        docker_files = [
            'Dockerfile',
            'docker-compose.yml',
            'docker-compose.yaml',
            '.dockerignore'
        ]

        existing_files = []
        for file in docker_files:
            if (self.project_path / file).exists():
                existing_files.append(file)

        return len(existing_files) > 0, existing_files

    # ==================== 配置检测方法 ====================

    def _load_package_json(self) -> Optional[Dict]:
        """加载并缓存 package.json"""
        if self._package_json_cache is not None:
            return self._package_json_cache

        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    self._package_json_cache = json.load(f)
                return self._package_json_cache
            except Exception:
                pass
        return None

    def _load_env_file(self, filename: str = '.env') -> Dict[str, str]:
        """加载环境变量文件"""
        if self._env_cache is None:
            self._env_cache = {}

        env_file = self.project_path / filename
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            # 移除引号
                            value = value.strip().strip('"').strip("'")
                            self._env_cache[key.strip()] = value
            except Exception:
                pass
        return self._env_cache

    def detect_port(self) -> int:
        """从项目配置中检测端口

        优先级：
        1. .env 文件中的 PORT
        2. package.json scripts 中的端口
        3. 项目类型默认端口
        """
        # 优先级1: 从 .env 文件读取
        env_vars = self._load_env_file()
        if 'PORT' in env_vars:
            try:
                return int(env_vars['PORT'])
            except Exception:
                pass

        # 尝试其他环境变量文件
        for env_file in ['.env.local', '.env.production', '.env.development']:
            env_vars = self._load_env_file(env_file)
            if 'PORT' in env_vars:
                try:
                    return int(env_vars['PORT'])
                except Exception:
                    pass

        # 优先级2: 从 package.json scripts 解析端口
        pkg = self._load_package_json()
        if pkg:
            scripts = pkg.get('scripts', {})
            for script_name in ['dev', 'start', 'serve']:
                if script_name in scripts:
                    script = scripts[script_name]
                    # 匹配 --port 3000 或 -p 3000
                    port_match = re.search(r'--port\s+(\d+)', script)
                    if port_match:
                        return int(port_match.group(1))
                    port_match = re.search(r'-p\s+(\d+)', script)
                    if port_match:
                        return int(port_match.group(1))

        # 优先级3: 根据项目类型返回默认端口
        project_type = self.detect_project_type({})
        return self.DEFAULT_PORTS.get(project_type, 3000)

    def detect_base_image(self, project_type: str) -> str:
        """根据项目类型和配置选择最优基础镜像"""
        pkg = self._load_package_json()

        # 检测是否使用 Bun
        if pkg and 'bun' in pkg.get('packageManager', '').lower():
            return self.BASE_IMAGES.get(f'{project_type}-bun', self.BASE_IMAGES.get(project_type, 'node:20-alpine'))

        # 检测 Bun 锁文件
        if (self.project_path / 'bun.lock').exists() or (self.project_path / 'bun.lockb').exists():
            return self.BASE_IMAGES.get(f'{project_type}-bun', self.BASE_IMAGES.get(project_type, 'node:20-alpine'))

        # 检测 Python 版本
        if project_type in ('fastapi', 'python'):
            pyproject = self.project_path / 'pyproject.toml'
            if pyproject.exists():
                try:
                    content = pyproject.read_text()
                    version_match = re.search(r'python\s*=\s*["\']>=?(\d+)\.(\d+)', content)
                    if version_match:
                        major, minor = version_match.groups()
                        return f'python:{major}.{minor}-slim'
                except Exception:
                    pass

        # 检测 Node.js 版本要求
        if project_type in ('nextjs', 'react', 'vue', 'angular', 'express', 'nuxt', 'node'):
            if pkg:
                engines = pkg.get('engines', {})
                node_version = engines.get('node', '')
                if node_version:
                    # 解析版本号
                    version_match = re.search(r'(\d+)', node_version)
                    if version_match:
                        major = version_match.group(1)
                        return f'node:{major}-alpine'

        return self.BASE_IMAGES.get(project_type, 'node:20-alpine')

    def detect_project_type(self, analysis_data: Dict[str, Any]) -> str:
        """根据项目文件检测项目类型"""
        languages = analysis_data.get('languages', {})
        detected_type = 'unknown'

        # JavaScript/TypeScript 项目检测
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    pkg_data = json.load(f)

                deps = str(pkg_data.get('dependencies', {}))
                dev_deps = str(pkg_data.get('devDependencies', {}))
                all_deps = deps + dev_deps

                # Next.js 检测
                if 'next' in deps or '"next"' in deps:
                    detected_type = 'nextjs'
                # Nuxt.js 检测
                elif 'nuxt' in all_deps:
                    detected_type = 'nuxt'
                # React/Vite 检测
                elif 'react' in deps or 'vite' in all_deps:
                    detected_type = 'react'
                # Vue 检测
                elif 'vue' in deps:
                    detected_type = 'vue'
                # Angular 检测
                elif '@angular/core' in deps:
                    detected_type = 'angular'
                # Express.js 检测
                elif 'express' in deps:
                    detected_type = 'express'
                else:
                    detected_type = 'node'
            except Exception:
                detected_type = 'node'

        # Python 项目检测
        elif 'python' in languages or (self.project_path / 'requirements.txt').exists() or (self.project_path / 'pyproject.toml').exists():
            detected_type = 'python'

            # FastAPI 检测
            requirements_txt = self.project_path / 'requirements.txt'
            if requirements_txt.exists():
                try:
                    req_content = requirements_txt.read_text().lower()
                    if 'fastapi' in req_content:
                        detected_type = 'fastapi'
                except Exception:
                    pass

            # pyproject.toml 检测
            pyproject = self.project_path / 'pyproject.toml'
            if pyproject.exists():
                try:
                    content = pyproject.read_text().lower()
                    if 'fastapi' in content:
                        detected_type = 'fastapi'
                except Exception:
                    pass

        # Go 项目检测
        elif 'go' in languages or (self.project_path / 'go.mod').exists():
            go_mod = self.project_path / 'go.mod'
            if go_mod.exists():
                try:
                    content = go_mod.read_text().lower()
                    if 'gin' in content:
                        detected_type = 'gin'
                    else:
                        detected_type = 'go'
                except Exception:
                    detected_type = 'go'

        # Rust 项目检测
        elif 'rust' in languages or (self.project_path / 'Cargo.toml').exists():
            detected_type = 'rust'

        # Java 项目检测
        elif 'java' in languages or (self.project_path / 'pom.xml').exists() or (self.project_path / 'build.gradle').exists():
            detected_type = 'java'

        # 静态网站检测
        if detected_type == 'unknown':
            html_files = list(self.project_path.glob('*.html'))
            if html_files:
                detected_type = 'static'

        return detected_type

    # ==================== Dockerfile 生成方法 ====================

    def generate_dockerfile(self, project_type: str, port: Optional[int] = None, base_image: Optional[str] = None) -> str:
        """生成 Dockerfile"""

        # 自动检测配置
        if port is None:
            port = self.detect_port()
        if base_image is None:
            base_image = self.detect_base_image(project_type)

        # 检测包管理器和锁文件
        package_json = self.project_path / 'package.json'
        has_bun = False
        has_package_lock = False
        is_static_export = False

        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    pkg_data = json.load(f)

                # 检测是否使用 Bun
                if 'bun' in pkg_data.get('packageManager', '').lower():
                    has_bun = True
                has_package_lock = (self.project_path / 'bun.lock').exists() or (self.project_path / 'bun.lockb').exists()

            except Exception:
                pass

        # 如果不是 Bun，检测 npm/pnpm 锁文件
        if not has_bun:
            has_package_lock = (
                (self.project_path / 'package-lock.json').exists() or
                (self.project_path / 'pnpm-lock.yaml').exists()
            )

        # 检测 Next.js 是否使用静态导出模式
        if project_type == 'nextjs':
            next_config_file = self.project_path / 'next.config.js'
            if next_config_file.exists():
                try:
                    config_content = next_config_file.read_text()
                    is_static_export = bool(re.search(r'output\s*:\s*["\']export["\']', config_content))
                except Exception:
                    pass

        # 根据包管理器设置安装命令
        if has_bun:
            install_cmd = 'bun install --frozen-lockfile && bun pm cache rm'
            copy_cmd = 'COPY package.json bun.lock* ./'
            npm_install_cmd = ''
        else:
            npm_install_cmd = 'npm ci --omit=dev' if has_package_lock else 'npm install --omit=dev'
            install_cmd = f'HUSKY=0 {npm_install_cmd} && npm cache clean --force'
            copy_cmd = 'COPY package*.json ./'

        # 生成模板
        template = self._get_dockerfile_template(project_type, has_bun, is_static_export, port, base_image, copy_cmd, install_cmd)

        return template

    def _get_dockerfile_template(self, project_type: str, has_bun: bool, is_static_export: bool,
                                  port: int, base_image: str, copy_cmd: str, install_cmd: str) -> str:
        """获取 Dockerfile 模板"""

        if project_type == 'nextjs':
            return self._get_nextjs_template(has_bun, is_static_export, port, base_image, copy_cmd, install_cmd)
        elif project_type == 'static':
            return self._get_static_template(port, base_image, install_cmd)
        elif project_type == 'fastapi':
            return self._get_fastapi_template(port, base_image)
        elif project_type == 'python':
            return self._get_python_template(port, base_image)
        elif project_type in ('gin', 'go'):
            return self._get_go_template(port, base_image)
        elif project_type == 'rust':
            return self._get_rust_template(port)
        elif project_type == 'java':
            return self._get_java_template(port)
        else:
            return self._get_node_template(port, base_image, copy_cmd, install_cmd)

    def _get_nextjs_template(self, has_bun: bool, is_static_export: bool,
                              port: int, base_image: str, copy_cmd: str, install_cmd: str) -> str:
        """获取 Next.js Dockerfile 模板"""

        if has_bun:
            if is_static_export:
                return """# Next.js 生产环境镜像（静态导出 - Bun）
FROM oven/bun:1-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 安装依赖
COPY package.json bun.lock* ./
RUN sed -i '/"prepare":/d' package.json || true
RUN bun install --frozen-lockfile && bun pm cache rm

# 构建应用
FROM oven/bun:1-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY package.json ./
COPY tsconfig.json ./
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
RUN bun install autoprefixer postcss tailwindcss --dev
RUN apk add --no-cache python3 make g++
RUN bun run build

# 生产环境 - 静态文件服务器
FROM nginx:alpine AS runner
WORKDIR /app
COPY --from=builder /app/out /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf 2>/dev/null || true
EXPOSE {port}
CMD ["nginx", "-g", "daemon off;"]
"""
            else:
                return """# Next.js 生产环境镜像（Bun）
FROM oven/bun:1-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 安装依赖
COPY package.json bun.lock* ./
RUN sed -i '/"prepare":/d' package.json || true
RUN bun install --frozen-lockfile && bun pm cache rm

# 构建应用
FROM oven/bun:1-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY package.json ./
COPY tsconfig.json ./
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
RUN bun install autoprefixer postcss tailwindcss --dev
RUN apk add --no-cache python3 make g++
RUN bun run build

# 生产环境
FROM oven/bun:1-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE {port}

CMD ["bun", "run", "server.js"]
"""
        else:
            node_version = base_image.split(':')[1].split('-')[0] if ':' in base_image else '20'

            if is_static_export:
                return """# Next.js 生产环境镜像（静态导出）
FROM node:{node_version}-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 安装依赖
{copy_cmd}
RUN sed -i '/"prepare":/d' package.json || true
RUN {install_cmd}

# 构建应用
FROM node:{node_version}-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
{copy_cmd}
COPY tsconfig.json ./
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
RUN npm install autoprefixer postcss tailwindcss --save-dev
RUN apk add --no-cache python3 make g++
RUN npm run build

# 生产环境 - 静态文件服务器
FROM nginx:alpine AS runner
WORKDIR /app
COPY --from=builder /app/out /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf 2>/dev/null || true
EXPOSE {port}
CMD ["nginx", "-g", "daemon off;"]
"""
            else:
                return """# Next.js 生产环境镜像
FROM node:{node_version}-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 安装依赖
{copy_cmd}
RUN sed -i '/"prepare":/d' package.json || true
RUN {install_cmd}

# 构建应用
FROM node:{node_version}-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
{copy_cmd}
COPY tsconfig.json ./
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
RUN npm install autoprefixer postcss tailwindcss --save-dev
RUN apk add --no-cache python3 make g++
RUN npm run build

# 生产环境
FROM node:{node_version}-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE {port}

CMD ["node", "server.js"]
"""

    def _get_static_template(self, port: int, base_image: str, install_cmd: str) -> str:
        """获取静态网站 Dockerfile 模板"""
        return """# 静态网站镜像
FROM node:20-alpine AS builder
WORKDIR /app
COPY . .
RUN {install_cmd} && npm run build

FROM nginx:alpine AS runner
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf 2>/dev/null || true
EXPOSE {port}
CMD ["nginx", "-g", "daemon off;"]
"""

    def _get_fastapi_template(self, port: int, base_image: str) -> str:
        """获取 FastAPI Dockerfile 模板"""
        python_version = base_image.split(':')[1].split('-')[0] if ':' in base_image else '3.12'
        return """# FastAPI 生产环境
FROM python:{python_version}-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:{python_version}-slim AS runner
WORKDIR /app
COPY --from=builder /usr/local/lib/python{python_version}/site-packages /usr/local/lib/python{python_version}/site-packages
COPY . .
EXPOSE {port}
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{port}"]
"""

    def _get_python_template(self, port: int, base_image: str) -> str:
        """获取 Python Dockerfile 模板"""
        python_version = base_image.split(':')[1].split('-')[0] if ':' in base_image else '3.12'
        return """# Python 应用
FROM python:{python_version}-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:{python_version}-slim AS runner
WORKDIR /app
COPY --from=builder /usr/local/lib/python{python_version}/site-packages /usr/local/lib/python{python_version}/site-packages
COPY . .
EXPOSE {port}
CMD ["python", "app.py"]
"""

    def _get_go_template(self, port: int, base_image: str) -> str:
        """获取 Go Dockerfile 模板"""
        go_version = base_image.split(':')[1].split('-')[0] if ':' in base_image else '1.22'
        return """# Go 应用
FROM golang:{go_version}-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

FROM alpine:latest AS runner
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/main .
EXPOSE {port}
CMD ["./main"]
"""

    def _get_rust_template(self, port: int) -> str:
        """获取 Rust Dockerfile 模板"""
        return """# Rust 应用
FROM rust:1.75-alpine AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {{}}" > src/main.rs
RUN cargo build --release && rm -rf src
COPY src ./src
RUN cargo build --release

FROM alpine:latest AS runner
RUN apk --no-cache add ca-certificates
WORKDIR /app
COPY --from=builder /app/target/release/app .
EXPOSE {port}
CMD ["./app"]
"""

    def _get_java_template(self, port: int) -> str:
        """获取 Java Dockerfile 模板"""
        return """# Java 应用
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -DskipTests

FROM eclipse-temurin:21-jre-alpine AS runner
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
EXPOSE {port}
CMD ["java", "-jar", "app.jar"]
"""

    def _get_node_template(self, port: int, base_image: str, copy_cmd: str, install_cmd: str) -> str:
        """获取 Node.js Dockerfile 模板"""
        node_version = base_image.split(':')[1].split('-')[0] if ':' in base_image else '20'
        return """# Node.js 应用
FROM node:{node_version}-alpine AS builder
WORKDIR /app
{copy_cmd}
RUN sed -i '/"prepare":/d' package.json || true
RUN {install_cmd}
COPY . .

FROM node:{node_version}-alpine AS runner
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
COPY --from=builder /app/dist ./dist
EXPOSE {port}
CMD ["node", "dist/index.js"]
"""

    # ==================== 其他文件生成方法 ====================

    def generate_dockerignore(self) -> str:
        """生成 .dockerignore"""
        return """node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.env.local
.env.development
.env.production
.next
.DS_Store
*.log
npm-debug.log*
bun-debug.log*
bun-error.log*
yarn-debug.log*
yarn-error.log*
pids
*.pid
*.seed
*.pid.lock
.vscode
.idea
*.swp
*.swo
*~
__pycache__
*.pyc
.pytest_cache
.mypy_cache
coverage
.nyc_output
dist
build
target
"""

    def generate_docker_build_script(self) -> str:
        """生成 docker-build.sh"""
        return """#!/bin/bash
set -e

echo "Building Docker image..."

# Get the directory where this script is located
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Extract project name from directory name
PROJECT_NAME=$(basename "$PROJECT_DIR" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')

# Use project name as image name
IMAGE_NAME="${IMAGE_NAME:-${PROJECT_NAME}:latest}"

# Enable BuildKit for better performance
export DOCKER_BUILDKIT=1

echo "Project: $PROJECT_NAME"
echo "Image: $IMAGE_NAME"

# Build the image
docker build --network=host -t "$IMAGE_NAME" .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo "Image: $IMAGE_NAME"
else
    echo "❌ Docker build failed!"
    exit 1
fi
"""

    def generate_docker_run_script(self, port: int) -> str:
        """生成 docker-run.sh"""
        return """#!/bin/bash
set -e

# 颜色输出
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

# 加载环境变量
load_env_file() {{
    local env_file="$1"
    if [[ -f "$env_file" ]]; then
        echo -e "${{GREEN}}✅ 加载环境变量: $env_file${{NC}}"
        while IFS='=' read -r key value || [[ -n "$key" ]]; do
            [[ $key =~ ^#.*$ ]] && continue
            [[ -z $key ]] && continue
            value="${{value%\\"}}"
            value="${{value#\\"}}"
            value="${{value%\\'}}"
            value="${{value#\\'}}"
            key="${{key# }}"
            key="${{key% }}"
            value="${{value# }}"
            value="${{value% }}"
            if [[ -n $key && -n $value ]]; then
                export "$key=$value"
            fi
        done < "$env_file"
    fi
}}

# 获取项目目录
PROJECT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PROJECT_NAME=$(basename "$PROJECT_DIR" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')

CONTAINER_NAME="${{CONTAINER_NAME:-$PROJECT_NAME}}"
IMAGE_NAME="${{IMAGE_NAME:-${{PROJECT_NAME}}:latest}}"

echo "Project: $PROJECT_NAME"
echo "Container: $CONTAINER_NAME"
echo "Image: $IMAGE_NAME"
echo ""
echo "Stopping existing container..."
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true

# 加载环境变量文件
load_env_file ".env.production"

echo "Starting container..."

# 构建 docker run 命令
DOCKER_CMD=("docker" "run" "-d")
DOCKER_CMD+=("--name" "$CONTAINER_NAME")
DOCKER_CMD+=("-p" "{port}:{port}")
DOCKER_CMD+=("-e" "PORT={port}")

# 添加环境变量
if [[ -f ".env.production" ]]; then
    while IFS='=' read -r line || [[ -n "$line" ]]; do
        [[ $line =~ ^#.*$ ]] && continue
        [[ -z $line ]] && continue
        key="${{line%%=*}}"
        key="${{key# }}"
        key="${{key% }}"
        [[ -z $key ]] && continue
        if [[ -n "${{!key}}" ]]; then
            DOCKER_CMD+=("-e" "$key=${{!key}}")
        fi
    done < ".env.production"
fi

DOCKER_CMD+=("$IMAGE_NAME")

# 执行
"${{DOCKER_CMD[@]}}"

echo ""
echo -e "${{GREEN}}✅ Container started successfully!${{NC}}"
echo "Access at: http://localhost:{port}"
echo ""
echo "Useful commands:"
echo "  View logs:    docker logs -f $CONTAINER_NAME"
echo "  Stop:         docker stop $CONTAINER_NAME"
echo "  Shell access: docker exec -it $CONTAINER_NAME sh"
"""

    def generate_docker_compose_optimized(
        self,
        service_name: str,
        image: str,
        port: int,
        analysis_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成优化的 docker-compose.yml (基于代码复杂度)

        Args:
            service_name: 服务名称
            image: Docker 镜像
            port: 服务端口
            analysis_data: 分析数据

        Returns:
            docker-compose.yml 内容
        """
        from smart_docker_config import SmartDockerConfig

        smart_config = SmartDockerConfig(str(self.project_path))
        return smart_config.generate_docker_compose(
            service_name=service_name,
            image=image,
            port=port,
            analysis_data=analysis_data
        )

    def generate_kubernetes_deployment_optimized(
        self,
        app_name: str,
        image: str,
        port: int,
        analysis_data: Optional[Dict[str, Any]] = None,
        replicas: int = 1
    ) -> str:
        """
        生成优化的 Kubernetes Deployment (基于代码复杂度)

        Args:
            app_name: 应用名称
            image: Docker 镜像
            port: 服务端口
            analysis_data: 分析数据
            replicas: 副本数

        Returns:
            Kubernetes Deployment YAML
        """
        from smart_docker_config import SmartDockerConfig

        smart_config = SmartDockerConfig(str(self.project_path))
        return smart_config.generate_kubernetes_deployment(
            app_name=app_name,
            image=image,
            port=port,
            replicas=replicas,
            analysis_data=analysis_data
        )

    def generate_resource_report(self, analysis_data: Optional[Dict[str, Any]] = None) -> str:
        """
        生成资源配置报告

        Args:
            analysis_data: 分析数据

        Returns:
            格式化的报告文本
        """
        from smart_docker_config import SmartDockerConfig

        smart_config = SmartDockerConfig(str(self.project_path))
        return smart_config.generate_resource_report(analysis_data)

    def save_files(self, dockerfile_content: str, port: int = 3000):
        """保存所有生成的文件"""
        # 保存 Dockerfile
        dockerfile_path = self.project_path / 'Dockerfile'
        dockerfile_path.write_text(dockerfile_content)
        self.generated_files.append('Dockerfile')

        # 保存 .dockerignore
        dockerignore_path = self.project_path / '.dockerignore'
        dockerignore_path.write_text(self.generate_dockerignore())
        self.generated_files.append('.dockerignore')

        # 保存构建脚本
        build_script_path = self.project_path / 'docker-build.sh'
        build_script_path.write_text(self.generate_docker_build_script())
        build_script_path.chmod(0o755)
        self.generated_files.append('docker-build.sh')

        # 保存运行脚本
        run_script_path = self.project_path / 'docker-run.sh'
        run_script_path.write_text(self.generate_docker_run_script(port))
        run_script_path.chmod(0o755)
        self.generated_files.append('docker-run.sh')

        return self.generated_files


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='Docker 配置生成器（基于规则）')
    parser.add_argument('project_path', help='项目路径')
    parser.add_argument('--analysis', help='分析报告路径（可选）')
    parser.add_argument('--force', action='store_true', help='强制覆盖')

    args = parser.parse_args()

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"❌ 项目路径不存在: {project_path}")
        return 1

    generator = DockerGenerator(str(project_path))

    # 检查是否已有配置
    has_config, existing_files = generator.has_docker_config()
    if has_config and not args.force:
        print(f"⚠️  项目已存在 Docker 配置: {', '.join(existing_files)}")
        print("使用 --force 参数强制覆盖")
        return 1

    # 自动检测项目类型、端口和基础镜像
    project_type = generator.detect_project_type({})
    port = generator.detect_port()
    base_image = generator.detect_base_image(project_type)

    print("🔍 检测结果:")
    print(f"   项目类型: {project_type}")
    print(f"   端口: {port}")
    print(f"   基础镜像: {base_image}")

    # 生成 Dockerfile
    print(f"\n🐳 生成 {project_type} 项目的 Dockerfile...")
    dockerfile_content = generator.generate_dockerfile(project_type, port, base_image)

    # 保存文件
    generated = generator.save_files(dockerfile_content, port)

    print(f"\n✅ 生成完成: {', '.join(generated)}")
    return 0


if __name__ == "__main__":
    exit(main())
