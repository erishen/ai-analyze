#!/usr/bin/env python3
"""
一键完整分析工具
整合 Serena 结构分析 + AI 深度分析 + Docker 自动生成
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# 加载 .env 环境变量
from dotenv import load_dotenv

# 将 ai-analyze 根目录添加到 Python 路径
script_dir = Path(__file__).parent
ai_analyze_root = script_dir.parent
if str(ai_analyze_root) not in sys.path:
    sys.path.insert(0, str(ai_analyze_root))

# 加载环境变量
load_dotenv(ai_analyze_root / '.env')


def confirm(prompt: str, yes_mode: bool = False) -> bool:
    """
    获取用户确认，支持非交互模式

    Args:
        prompt: 提示信息
        yes_mode: 是否在非交互模式下自动选择 'y'

    Returns:
        True 如果用户确认，否则 False
    """
    if yes_mode:
        return True
    try:
        response = input(f"{prompt} (y/n): ")
        return response.lower() == 'y'
    except EOFError:
        # 非交互模式，默认为 False
        return False


def run_serena_analysis(format_type="json"):
    """运行 Serena 分析"""
    print("🔍 步骤 1/3: 运行 Serena 代码结构分析...")
    
    cmd = [
        sys.executable,
        str(script_dir / "analyze_project_multilang.py"),
        f"--format={format_type}"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ai_analyze_root))
    
    if result.returncode != 0:
        print(f"❌ Serena 分析失败: {result.stderr}")
        return None
    
    # 获取最新生成的报告
    reports_dir = ai_analyze_root / "reports"
    if not reports_dir.exists():
        print("❌ 未找到 reports 目录")
        return None
    
    # 查找最新的 JSON 报告
    json_files = sorted(reports_dir.glob("*_analysis_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not json_files:
        print("❌ 未找到 JSON 报告文件")
        return None
    
    latest_report = json_files[0]
    print(f"✅ Serena 分析完成: {latest_report.name}")
    
    return str(latest_report)


def run_ai_enhancement(serena_report_path, replace_original=False, use_cache=True, cache_ttl=3600):
    """运行 AI 增强分析"""
    print("\n🤖 步骤 2/3: 运行 AI 深度分析...")

    # 准备命令
    cmd = [
        sys.executable,
        str(script_dir / "ai_enhanced_analyzer.py"),
        serena_report_path
    ]

    # 添加 --replace 参数以替换原始报告
    if replace_original:
        cmd.append("--replace")

    # 添加缓存相关参数
    if not use_cache:
        cmd.append("--no-cache")

    cmd.extend(["--cache-ttl", str(cache_ttl)])

    print(f"📝 运行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ai_analyze_root))

    # 打印 stdout（如果有）
    if result.stdout:
        print(result.stdout)

    # 打印 stderr（如果有）
    if result.stderr:
        print(f"⚠️  标准错误输出:\n{result.stderr}")

    if result.returncode != 0:
        print(f"\n❌ AI 分析失败 (退出码: {result.returncode})")
        print(f"标准输出: {result.stdout if result.stdout else '(空)'}")
        print(f"错误输出: {result.stderr if result.stderr else '(空)'}")
        return False

    # 获取 AI 增强报告路径
    if replace_original:
        ai_report = serena_report_path.replace('.json', '.md')
    else:
        ai_report = serena_report_path.replace('.json', '-ai.md')

    if Path(ai_report).exists():
        print(f"✅ AI 增强报告: {Path(ai_report).name}")
    else:
        print("⚠️  未找到 AI 增强报告文件")

    return True


def run_docker_generation(serena_report_path, force=False):
    """运行 Docker 生成"""
    print("\n🐳 步骤 3/3: 生成 Docker 配置...")
    
    # 初始化变量
    base_image = None
    
    # 读取 Serena 报告获取项目路径
    import json
    with open(serena_report_path, 'r') as f:
        analysis_data = json.load(f)
    
    project_path = analysis_data.get('project_path', '')
    if not project_path:
        print("❌ 无法从报告中获取项目路径")
        return False
    
    # 查找对应的 Docker 策略缓存文件
    import re
    cache_dir = ai_analyze_root / '.cache'
    
    # 读取报告获取生成时间戳来匹配缓存
    docker_strategy_arg = None
    try:
        with open(serena_report_path, 'r') as f:
            report_data = json.load(f)
        report_timestamp = report_data.get('generated_at')
        
        if report_timestamp:
            # 转换 ISO 时间戳为数字格式来匹配缓存文件名
            # 例如: 2026-01-25T15:45:39.448266 -> 提取日期部分 20260125
            dt = datetime.fromisoformat(report_timestamp.replace('Z', '+00:00'))
            date_part = dt.strftime('%Y%m%d')
            
            # 查找同一天生成的所有缓存文件
            cache_pattern = f"*_{date_part}_docker_strategy.json"
            cache_files = list(cache_dir.glob(cache_pattern))
            
            # 如果没有按日期找到，尝试查找任何 docker_strategy 文件
            if not cache_files:
                cache_files = list(cache_dir.glob("*_docker_strategy.json"))
            
            if cache_files:
                # 使用找到的第一个缓存文件（通常是最新的）
                docker_strategy_path = cache_files[0]
                docker_strategy_arg = str(docker_strategy_path)
                print(f"📊 找到 Docker 策略缓存: {docker_strategy_path.name}")
                
                # 读取缓存文件获取 base_image
                with open(docker_strategy_path, 'r') as f:
                    strategy_data = json.load(f)
                base_image = strategy_data.get('data', {}).get('base_image')
                if base_image:
                    print(f"🐳 使用 AI 推荐的基础镜像: {base_image}")
                    # 将 base_image 作为环境变量传递给 docker_generator
                    os.environ['AI_RECOMMENDED_BASE_IMAGE'] = base_image
                recommended_port = strategy_data.get('data', {}).get('recommended_port', 3000)
                if recommended_port != 3000:
                    os.environ['AI_RECOMMENDED_PORT'] = str(recommended_port)
    except Exception as e:
        print(f"⚠️  查找 Docker 策略缓存失败: {e}")
        # 如果按时间戳匹配失败，尝试查找任何 docker_strategy 文件作为备用
        try:
            cache_files = list(cache_dir.glob("*_docker_strategy.json"))
            if cache_files:
                docker_strategy_path = cache_files[0]
                docker_strategy_arg = str(docker_strategy_path)
                print(f"📊 使用备用缓存文件: {docker_strategy_path.name}")
                
                with open(docker_strategy_path, 'r') as f:
                    strategy_data = json.load(f)
                base_image = strategy_data.get('data', {}).get('base_image')
                if base_image:
                    print(f"🐳 使用 AI 推荐的基础镜像: {base_image}")
                    os.environ['AI_RECOMMENDED_BASE_IMAGE'] = base_image
        except Exception as e2:
            print(f"⚠️  备用缓存查找也失败: {e2}")
    
    # 运行 Docker 生成
    cmd = [
        sys.executable,
        str(script_dir / "docker_generator.py"),
        project_path,
        "--analysis", serena_report_path
    ]
    
    # 优先使用策略文件参数（更可靠）而不是环境变量
    if docker_strategy_arg:
        # 使用 --strategy 参数直接传递，避免环境变量传递问题
        cmd.extend(["--strategy", docker_strategy_arg])
        print(f"🐳 使用策略文件传递基础镜像: {base_image}")
    else:
        # 备用：使用环境变量（可能在某些环境下不可靠）
        if base_image:
            os.environ['AI_RECOMMENDED_BASE_IMAGE'] = base_image
            print(f"🐳 使用环境变量传递基础镜像: {base_image}")
    
    if force:
        cmd.append("--force")
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ai_analyze_root))
    
    # 清理临时环境变量
    os.environ.pop('AI_RECOMMENDED_BASE_IMAGE', None)
    os.environ.pop('AI_RECOMMENDED_PORT', None)
    
    if result.returncode != 0:
        print(f"❌ Docker 生成失败: {result.stderr}")
        return False
    
    print(result.stdout)
    return True


def main():
    parser = argparse.ArgumentParser(description="一键完整分析（Serena + AI + Docker）")
    parser.add_argument(
        "--skip-ai",
        action="store_true",
        help="跳过 AI 分析，只运行 Serena + Docker"
    )
    parser.add_argument(
        "--skip-docker",
        action="store_true",
        help="跳过 Docker 生成，只运行 Serena + AI"
    )
    parser.add_argument(
        "--serena-only",
        action="store_true",
        help="只运行 Serena 分析"
    )
    parser.add_argument(
        "--force-docker",
        action="store_true",
        help="强制覆盖已有的 Docker 配置"
    )
    parser.add_argument(
        "--report",
        help="指定已有的 Serena JSON 报告路径（跳过 Serena 分析）"
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="自动回答所有提示（非交互模式）"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="禁用缓存，强制调用 AI API"
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=3600,
        help="缓存有效期（秒），默认 3600 秒（1 小时）"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 一键完整分析工具 (Serena + AI + Docker)")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # 检查 API Key
    if not args.serena_only and not args.skip_ai:
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  警告: 未设置 OPENAI_API_KEY")
            print("   AI 分析将不可用，请配置 .env 文件")
            if not confirm("   是否继续？", args.yes):
                sys.exit(1)
    
    # 步骤 1: Serena 分析
    if args.report:
        # 使用已有的报告
        if not Path(args.report).exists():
            print(f"❌ 报告文件不存在: {args.report}")
            sys.exit(1)
        serena_report = args.report
        print(f"📄 使用已有报告: {serena_report}")
    else:
        # 运行 Serena 分析
        serena_report = run_serena_analysis()
        if not serena_report:
            sys.exit(1)
    
    # 读取 Serena 报告获取项目信息
    import json
    with open(serena_report, 'r') as f:
        analysis_data = json.load(f)
    project_path = analysis_data.get('project_path', '')
    
    # 步骤 2: AI 分析（可选）
    ai_ran = False
    if not args.serena_only and not args.skip_ai:
        # 使用 --replace 选项替换原始报告
        ai_ran = True
        success = run_ai_enhancement(
            serena_report,
            replace_original=True,
            use_cache=not args.no_cache,
            cache_ttl=args.cache_ttl
        )
        if not success:
            # AI 失败，询问是否继续 Docker
            if not confirm("⚠️  AI 分析失败，是否继续 Docker 生成？", args.yes):
                sys.exit(1)
    
    # 步骤 3: Docker 生成（可选）
    if not args.skip_docker and not args.serena_only:
        # 检查是否已有 Docker 配置
        from docker_generator import DockerGenerator
        docker_gen = DockerGenerator(project_path)
        has_docker, existing_files = docker_gen.has_docker_config()
        
        if has_docker and not args.force_docker:
            print(f"\n⚠️  项目已存在 Docker 配置: {', '.join(existing_files)}")
            if confirm("   是否覆盖？", args.yes):
                skip_docker = False
            else:
                print("ℹ️  跳过 Docker 生成")
                skip_docker = True
        else:
            skip_docker = False
        
        if not skip_docker:
            success = run_docker_generation(serena_report, force=args.force_docker)
            if not success:
                print("⚠️  Docker 生成失败，但分析已完成")
    
    # 完成
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("🎉 分析完成！")
    print(f"⏱️  耗时: {duration:.1f} 秒")
    print("=" * 60)
    
    # 显示生成的文件
    if serena_report:
        reports_dir = Path(serena_report).parent

        print("\n📄 生成的报告:")
        json_report = Path(serena_report)
        md_report = json_report.parent / json_report.name.replace('.json', '.md')

        if json_report.exists():
            print(f"   - {json_report.name}")
        if md_report.exists():
            # 根据是否运行了 AI 分析来显示不同的标签
            md_label = " (AI 增强版)" if ai_ran else ""
            print(f"   - {md_report.name}{md_label}")
        
        # 显示 Docker 文件（如果生成了）
        if not args.skip_docker:
            project_path = analysis_data.get('project_path', '')
            if project_path:
                project_root = Path(project_path)
                docker_files = ['Dockerfile', 'docker-compose.yml', '.dockerignore', 'docker-build.sh', 'docker-run.sh']
                
                existing_docker = []
                for f in docker_files:
                    if (project_root / f).exists():
                        existing_docker.append(f)
                
                if existing_docker:
                    print("\n🐳 生成的 Docker 配置:")
                    for f in existing_docker:
                        print(f"   - {f}")
    
    print("\n💡 提示:")
    print("   - 查看报告: cat reports/*.md")
    if not args.skip_docker and project_path:
        print(f"   - 进入项目: cd {project_path}")
        print("   - 构建镜像: ./docker-build.sh")
        print("   - 运行容器: ./docker-run.sh")


if __name__ == "__main__":
    main()
