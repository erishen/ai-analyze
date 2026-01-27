#!/usr/bin/env python3
"""Docker 配置生成器 - 支持 AI 增强分析"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import re


class DockerGenerator:
    """Docker 配置生成器"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.generated_files = []
    
    def has_docker_config(self) -> tuple[bool, List[str]]:
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
    
    def generate_dockerfile(self, project_type: str, port: int = 3000, base_image: Optional[str] = None) -> str:
        """生成 Dockerfile - 使用安全的替换策略"""

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
                has_package_lock = (self.project_path / 'bun.lock').exists()

            except:
                pass

        # 如果不是 Bun，检测 npm 锁文件
        if not has_bun:
            has_package_lock = (self.project_path / 'package-lock.json').exists()

        # 检测 Next.js 是否使用静态导出模式
        if project_type == 'nextjs':
            next_config_file = self.project_path / 'next.config.js'
            if next_config_file.exists():
                try:
                    with open(next_config_file, 'r') as f:
                        config_content = f.read()
                        # 检测 output: "export" 或 output: 'export'
                        is_static_export = bool(re.search(r'output\s*:\s*["\']export["\']', config_content))
                except:
                    pass

        # 根据包管理器设置安装命令
        if has_bun:
            install_cmd = 'bun install --frozen-lockfile && bun pm cache rm'
            copy_cmd = 'COPY package.json bun.lock ./'
            npm_install_cmd = ''  # Bun 不使用 npm 命令
        else:
            npm_install_cmd = 'npm ci --omit=dev' if has_package_lock else 'npm install --omit=dev'
            install_cmd = f'HUSKY=0 {npm_install_cmd} && npm cache clean --force'
            copy_cmd = 'COPY package*.json ./' if has_package_lock else 'COPY package.json ./'

        # 使用普通字符串避免 f-string 替换问题
        if project_type == 'nextjs':
            # Next.js 多阶段构建模板
            if has_bun:
                if is_static_export:
                    template = """# Next.js 生产环境镜像（静态导出 - Bun）
FROM oven/bun:1-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 安装依赖
COPY package.json bun.lock ./
# 删除 prepare 脚本以避免 husky 安装错误
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
RUN bun run prod

# 生产环境 - 静态文件服务器
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/out ./out
COPY --from=builder /app/public ./public

# 创建自定义服务器以支持子路径和静态资源
RUN printf '%s\\n' 'const express = require("express");' \\
  'const path = require("path");' \\
  'const fs = require("fs");' \\
  'const app = express();' \\
  'const PORT = process.env.PORT || {port};' \\
  'const basePath = "/shadcn-registry";' \\
  '' \\
  '// 设置静态文件服务' \\
  'const outDir = path.join(__dirname, "out");' \\
  '' \\
  '// 服务 basePath 下的静态文件' \\
  'app.use(basePath, express.static(outDir));' \\
  '' \\
  '// SPA 路由：返回 index.html 对于 basePath 下的非静态文件请求' \\
  'app.use(basePath, (req, res, next) => {' \\
  '    if (req.method === "GET" && !req.path.includes(".")) {' \\
  '        const indexPath = path.join(outDir, "index.html");' \\
  '        if (fs.existsSync(indexPath)) {' \\
  '            res.sendFile(indexPath);' \\
  '        } else {' \\
  '            next();' \\
  '        }' \\
  '    } else {' \\
  '        next();' \\
  '    }' \\
  '});' \\
  '' \\
  '// 根路径重定向到 basePath' \\
  'app.use((req, res) => {' \\
  '    if (req.path === "/") {' \\
  '        res.redirect(basePath);' \\
  '    } else {' \\
  '        res.status(404).send("Not Found");' \\
  '    }' \\
  '});' \\
  '' \\
  'app.listen(PORT, () => {' \\
  '    console.log(`Server running on port ${PORT}`);' \\
  '});' > server.js

RUN npm install express --production

EXPOSE {port}

CMD ["node", "server.js"]

"""
                else:
                    template = """# Next.js 生产环境镜像（Bun）
FROM oven/bun:1-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 安装依赖
COPY package.json bun.lock ./
# 删除 prepare 脚本以避免 husky 安装错误
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
RUN bun run prod

# 生产环境
FROM oven/bun:1-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

EXPOSE {port}

CMD ["bun", "start"]

"""
            else:
                if is_static_export:
                    template = """# Next.js 生产环境镜像（静态导出）
FROM node:18-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 安装依赖
{copy_cmd}
# 删除 prepare 脚本以避免 husky 安装错误
RUN sed -i '/"prepare":/d' package.json || true
RUN {install_cmd}

# 构建应用
FROM node:18-alpine AS builder
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
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/out ./out
COPY --from=builder /app/public ./public

# 创建自定义服务器
RUN printf '%s\\n' 'const express = require("express");' \\
  'const path = require("path");' \\
  'const fs = require("fs");' \\
  'const app = express();' \\
  'const PORT = process.env.PORT || {port};' \\
  'const basePath = "/shadcn-registry";' \\
  '' \\
  '// 设置静态文件服务' \\
  'const outDir = path.join(__dirname, "out");' \\
  '' \\
  '// 服务 basePath 下的静态文件' \\
  'app.use(basePath, express.static(outDir));' \\
  '' \\
  '// SPA 路由：返回 index.html 对于 basePath 下的非静态文件请求' \\
  'app.use(basePath, (req, res, next) => {' \\
  '    if (req.method === "GET" && !req.path.includes(".")) {' \\
  '        const indexPath = path.join(outDir, "index.html");' \\
  '        if (fs.existsSync(indexPath)) {' \\
  '            res.sendFile(indexPath);' \\
  '        } else {' \\
  '            next();' \\
  '        }' \\
  '    } else {' \\
  '        next();' \\
  '    }' \\
  '}});' \\
  '' \\
  '// 根路径重定向到 basePath' \\
  'app.use((req, res) => {' \\
  '    if (req.path === "/") {' \\
  '        res.redirect(basePath);' \\
  '    } else {' \\
  '        res.status(404).send("Not Found");' \\
  '    }' \\
  '});' \\
  '' \\
  'app.listen(PORT, () => {' \\
  '    console.log(`Server running on port ${PORT}`);' \\
  '}});' > server.js

RUN npm install express --production

EXPOSE {port}

CMD ["node", "server.js"]

"""
                else:
                    template = """# Next.js 生产环境镜像
FROM node:18-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 安装依赖
{copy_cmd}
# 删除 prepare 脚本以避免 husky 安装错误
RUN sed -i '/"prepare":/d' package.json || true
RUN {install_cmd}

# 构建应用
FROM node:18-alpine AS builder
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
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

EXPOSE {port}

CMD ["node", "server.js"]

"""
            # 安全的镜像替换 - 只替换 FROM 指令的行首
            if base_image and base_image.startswith('node:'):
                template = re.sub(
                    r'^FROM node:18-alpine',
                    f'FROM {base_image}',
                    template,
                    flags=re.MULTILINE
                )
                print(f"✅ 应用 AI 推荐的基础镜像: {base_image}")
        
        elif project_type == 'static':
            # 静态网站模板
            npm_install_cmd_static = 'npm ci' if has_package_lock else 'npm install'
            template = """# 静态网站镜像
FROM node:18-alpine AS builder
WORKDIR /app
COPY . .
RUN {npm_install_cmd} && npm run build

FROM nginx:alpine AS runner
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE {port}
CMD ["nginx", "-g", "daemon off;"]

"""
            # 安全的镜像替换
            if base_image and base_image.startswith('node:'):
                template = re.sub(
                    r'^FROM node:18-alpine',
                    f'FROM {base_image}',
                    template,
                    flags=re.MULTILINE
                )
                print(f"✅ 应用 AI 推荐的基础镜像: {base_image}")
            elif base_image and base_image.startswith('oven/bun:'):
                template = re.sub(
                    r'^FROM oven/bun:1-alpine',
                    f'FROM {base_image}',
                    template,
                    flags=re.MULTILINE
                )
                print(f"✅ 应用 AI 推荐的 Bun 基础镜像: {base_image}")
        
        elif project_type == 'fastapi':
            # FastAPI 模板
            template = """# FastAPI 生产环境
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runner
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
EXPOSE {port}
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{port}"]

"""
            # Python 镜像替换
            if base_image and base_image.startswith('python:'):
                template = re.sub(
                    r'^FROM python:3.11-slim',
                    f'FROM {base_image}',
                    template,
                    flags=re.MULTILINE
                )
                print(f"✅ 应用 AI 推荐的 Python 基础镜像: {base_image}")
        
        elif project_type == 'python':
            # 通用 Python 模板
            template = """# Python 应用
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runner
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
EXPOSE {port}
CMD ["python", "app.py"]

"""
            # Python 镜像替换
            if base_image and base_image.startswith('python:'):
                template = re.sub(
                    r'^FROM python:3.11-slim',
                    f'FROM {base_image}',
                    template,
                    flags=re.MULTILINE
                )
                print(f"✅ 应用 AI 推荐的 Python 基础镜像: {base_image}")
        
        elif project_type == 'gin':
            # Gin Go 模板
            template = """# Gin Go 应用
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go mod download
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

FROM alpine:latest AS runner
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/main .
EXPOSE {port}
CMD ["./main"]

"""
            # Go 镜像替换
            if base_image and base_image.startswith('golang:'):
                template = re.sub(
                    r'^FROM golang:1.21-alpine',
                    f'FROM {base_image}',
                    template,
                    flags=re.MULTILINE
                )
                print(f"✅ 应用 AI 推荐的 Go 基础镜像: {base_image}")
        
        else:
            # 默认模板
            template = """# 默认 Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY . .
EXPOSE {port}
CMD ["npm", "start"]

"""
            if base_image and base_image.startswith('node:'):
                template = re.sub(
                    r'^FROM node:18-alpine',
                    f'FROM {base_image}',
                    template,
                    flags=re.MULTILINE
                )
                print(f"✅ 应用 AI 推荐的基础镜像: {base_image}")

        # 替换占位符
        template = template.replace('{port}', str(port))
        template = template.replace('{copy_cmd}', copy_cmd)
        # 只在模板中使用 npm_install_cmd 时才替换
        if '{npm_install_cmd}' in template:
            template = template.replace('{npm_install_cmd}', npm_install_cmd)
        # 静态网站使用单独的命令
        if project_type == 'static' and '{npm_install_cmd}' in template:
            template = template.replace('{npm_install_cmd}', npm_install_cmd_static)

        return template
    
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
ls -la
.vscode
.idea
*.swp
*.swo
*~\n"""
    
    def generate_docker_build_script(self) -> str:
        """生成 docker-build.sh"""
        return """#!/bin/bash
set -e

echo "Building Docker image..."

# Get the directory where this script is located (this is the project directory)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Extract project name from directory name (replace spaces and special chars)
PROJECT_NAME=$(basename "$PROJECT_DIR" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')

# Use project name as image name, or allow override via IMAGE_NAME env var
IMAGE_NAME="${IMAGE_NAME:-${PROJECT_NAME}:latest}"

# Change to project directory
cd "$PROJECT_DIR"

# Build with network=host to avoid DNS resolution issues with mirror
# Also enable BuildKit for better performance
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
    
    def generate_docker_run_script(self, port: int = 3000) -> str:
        """生成 docker-run.sh"""
        return f"""#!/bin/bash
set -e

# 颜色输出
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

# 加载环境变量的函数
load_env_file() {{
    local env_file="$1"
    if [[ -f "$env_file" ]]; then
        echo -e "${{GREEN}}✅ 加载环境变量: $env_file${{NC}}"
        
        # 读取文件并导出变量
        while IFS='=' read -r key value || [[ -n "$key" ]]; do
            # 跳过注释和空行
            [[ $key =~ ^#.*$ ]] && continue
            [[ -z $key ]] && continue
            
            # 移除值中的引号（如果有）
            value="${{value%\\"}}"
            value="${{value#\\"}}"
            value="${{value%\\'}}"
            value="${{value#\\'}}"
            
            # 移除前后的空格
            key="${{key# }}"
            key="${{key% }}"
            value="${{value# }}"
            value="${{value% }}"
            
            # 导出变量
            if [[ -n $key && -n $value ]]; then
                export "$key=$value"
                echo "  - $key=${{value:0:20}}..."  # 只显示前20个字符（安全性）
            fi
        done < "$env_file"
    fi
}}

# 获取项目所在目录
PROJECT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"

# 提取项目名称（转为小写，移除特殊字符）
PROJECT_NAME=$(basename "$PROJECT_DIR" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')

# 容器名称和镜像名称
CONTAINER_NAME="${{CONTAINER_NAME:-$PROJECT_NAME}}"
IMAGE_NAME="${{IMAGE_NAME:-${{PROJECT_NAME}}:latest}}"

echo "Project: $PROJECT_NAME"
echo "Container: $CONTAINER_NAME"
echo "Image: $IMAGE_NAME"
echo ""
echo "Stopping existing container..."
docker stop "$CONTAINER_NAME" || true
docker rm "$CONTAINER_NAME" || true

# 加载 .env.production 文件
load_env_file ".env.production"

echo "Starting container..."

# 构建 docker run 命令的数组
DOCKER_CMD=("docker" "run" "-d")
DOCKER_CMD+=("--name" "$CONTAINER_NAME")
DOCKER_CMD+=("-p" "{port}:{port}")
DOCKER_CMD+=("-e" "PORT={port}")

# 从已加载的环境变量中添加到容器（从 .env.production 加载的变量）
if [[ -f ".env.production" ]]; then
    # 读取 .env.production 文件获取变量名,然后从已导出的环境变量中获取值
    while IFS='=' read -r line || [[ -n "$line" ]]; do
        # 跳过注释和空行
        [[ $line =~ ^#.*$ ]] && continue
        [[ -z $line ]] && continue

        # 提取变量名（=号之前的部分）
        key="${{line%%=*}}"

        # 移除变量名前后的空格
        key="${{key# }}"
        key="${{key% }}"
        [[ -z $key ]] && continue

        # 从已导出的环境变量中获取值
        if [[ -n "${{!key}}" ]]; then
            DOCKER_CMD+=("-e" "$key=${{!key}}")
        fi
    done < ".env.production"
fi

DOCKER_CMD+=("$IMAGE_NAME")

# 执行 docker run
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
    
    def detect_project_type(self, analysis_data: Dict[str, Any]) -> str:
        """根据分析结果检测项目类型"""
        languages = analysis_data.get('languages', {})
        detected_type = 'unknown'
        
        # 基于编程语言检测
        if 'typescript' in languages or 'javascript' in languages:
            # 检查包管理器文件
            package_json = self.project_path / 'package.json'
            if package_json.exists():
                try:
                    with open(package_json, 'r') as f:
                        pkg_data = json.load(f)
                    
                    # Next.js 检测
                    if 'next' in str(pkg_data.get('dependencies', {})) or 'next' in str(pkg_data.get('devDependencies', {})):
                        detected_type = 'nextjs'
                    # React/Vite 检测
                    elif 'react' in str(pkg_data.get('dependencies', {})) or 'vite' in str(pkg_data.get('dependencies', {})):
                        detected_type = 'react'
                    # Vue 检测
                    elif 'vue' in str(pkg_data.get('dependencies', {})):
                        detected_type = 'vue'
                    # Angular 检测
                    elif '@angular/core' in str(pkg_data.get('dependencies', {})):
                        detected_type = 'angular'
                    # Express.js 检测
                    elif 'express' in str(pkg_data.get('dependencies', {})):
                        detected_type = 'express'
                    # Nuxt.js 检测
                    elif 'nuxt' in str(pkg_data.get('dependencies', {})):
                        detected_type = 'nuxt'
                    else:
                        detected_type = 'node'
                except:
                    detected_type = 'node'
        
        # Python 项目检测
        elif 'python' in languages:
            requirements_txt = self.project_path / 'requirements.txt'
            pyproject_toml = self.project_path / 'pyproject.toml'
            
            if requirements_txt.exists() or pyproject_toml.exists():
                detected_type = 'python'
                
                # FastAPI 检测
                if requirements_txt.exists():
                    try:
                        with open(requirements_txt, 'r') as f:
                            req_content = f.read().lower()
                        if 'fastapi' in req_content:
                            detected_type = 'fastapi'
                    except:
                        pass
        
        # Go 项目检测
        elif 'go' in languages:
            go_mod = self.project_path / 'go.mod'
            if go_mod.exists():
                detected_type = 'gin'
        
        # Rust 项目检测
        elif 'rust' in languages:
            cargo_toml = self.project_path / 'Cargo.toml'
            if cargo_toml.exists():
                detected_type = 'rust'
        
        # Java 项目检测
        elif 'java' in languages:
            pom_xml = self.project_path / 'pom.xml'
            build_gradle = self.project_path / 'build.gradle'
            
            if pom_xml.exists() or build_gradle.exists():
                detected_type = 'java'
        
        # 静态网站检测
        if detected_type == 'unknown':
            html_files = list(self.project_path.glob('*.html'))
            if html_files:
                detected_type = 'static'
        
        return detected_type


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Docker 配置生成器')
    parser.add_argument('project_path', help='项目路径')
    parser.add_argument('--analysis', help='AI 分析报告路径')
    parser.add_argument('--strategy', help='AI Docker 策略文件路径')
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
    
    # 确定项目类型和基础镜像
    project_type = 'nextjs'  # 默认
    base_image = None
    port = 3000
    
    # 优先级1: 从环境变量获取（由 full_analyzer 传递）
    if 'AI_RECOMMENDED_BASE_IMAGE' in os.environ:
        base_image = os.environ['AI_RECOMMENDED_BASE_IMAGE']
        print(f"🤖 使用 AI 推荐的基础镜像: {base_image}")
    
    if 'AI_RECOMMENDED_PORT' in os.environ:
        try:
            port = int(os.environ['AI_RECOMMENDED_PORT'])
        except:
            pass
    
    # 优先级2: 从策略文件读取
    if args.strategy and not base_image:
        try:
            with open(args.strategy, 'r') as f:
                strategy_data = json.load(f)
            strategy_info = strategy_data.get('data', {})
            if not base_image:
                base_image = strategy_info.get('base_image')
                if base_image:
                    print(f"📊 从策略文件读取基础镜像: {base_image}")
            if port == 3000 and strategy_info.get('recommended_port'):
                port = strategy_info.get('recommended_port')
            project_type = strategy_info.get('project_type', project_type)
        except Exception as e:
            print(f"⚠️  读取策略文件失败: {e}")
    
    # 优先级3: 从分析报告读取
    if args.analysis and not base_image:
        try:
            with open(args.analysis, 'r') as f:
                analysis = json.load(f)
            project_type = analysis.get('project_type', project_type)
            if not base_image:
                base_image = analysis.get('base_image')
            if port == 3000:
                port = analysis.get('port', port)
            print(f"📊 从分析报告读取: 类型={project_type}, 镜像={base_image}, 端口={port}")
        except Exception as e:
            print(f"⚠️  读取分析报告失败: {e}")
    
    # 生成 Dockerfile
    print(f"🐳 生成 {project_type} 项目的 Dockerfile...")
    dockerfile_content = generator.generate_dockerfile(project_type, port, base_image)
    
    # 保存文件
    generated = generator.save_files(dockerfile_content, port)
    
    print(f"✅ 生成完成: {', '.join(generated)}")
    return 0


if __name__ == "__main__":
    exit(main())
