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
        
        # 使用普通字符串避免 f-string 替换问题
        if project_type == 'nextjs':
            # Next.js 多阶段构建模板
            template = """# Next.js 生产环境镜像
FROM node:18-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 安装依赖
COPY package*.json ./
# 删除 prepare 脚本以避免 husky 安装错误
RUN sed -i '/"prepare":/d' package.json || true
RUN HUSKY=0 npm ci --omit=dev && npm cache clean --force

# 构建应用
FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY package*.json ./
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
            template = """# 静态网站镜像
FROM node:18-alpine AS builder
WORKDIR /app
COPY . .
RUN npm ci && npm run build

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
        
        # 替换端口占位符
        template = template.replace('{port}', str(port))
        
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
docker build -t ai-chat .
echo "Build completed!"
"""
    
    def generate_docker_run_script(self, port: int = 3000) -> str:
        """生成 docker-run.sh"""
        return f"""#!/bin/bash
set -e

echo "Stopping existing container..."
docker stop ai-chat || true
docker rm ai-chat || true

echo "Starting container..."
docker run -d \\
  --name ai-chat \\
  -p {port}:{port} \\
  -e PORT={port} \\
  ai-chat

echo "Container started!"
echo "Access at: http://localhost:{port}"

# 提示用户可以自定义环境变量
if [[ -f ".env.production" ]]; then
    echo ""
    echo "💡 提示: 检测到 .env.production 文件，如需使用其中的环境变量，请手动修改 docker-run.sh"
    echo "   添加: -e VAR_NAME=${{VAR_NAME}}" 参数"
fi
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
