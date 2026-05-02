#!/usr/bin/env python3
"""
一键完整分析工具
整合 Serena 结构分析 + AI 深度分析 + Docker 自动生成
"""

import os
import sys
import subprocess
import argparse
import asyncio
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

# 加载 .env 环境变量
from dotenv import load_dotenv

# 将 ai-analyze 根目录添加到 Python 路径
script_dir = Path(__file__).parent
ai_analyze_root = script_dir.parent
if str(ai_analyze_root) not in sys.path:
    sys.path.insert(0, str(ai_analyze_root))

# 加载环境变量
load_dotenv(ai_analyze_root / '.env')

# 导入统一分析器
from src.unified_analyzer import UnifiedAnalyzer
from src.incremental_analyzer import IncrementalAnalyzer


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


def run_serena_analysis_sync(format_type="json"):
    """运行 Serena 分析 (同步版本)"""
    print("🔍 运行 Serena 代码结构分析...")

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


def run_ast_analysis_sync(project_path: str):
    """运行 AST 分析 (同步版本)"""
    print("🌳 运行 AST 代码分析...")

    cmd = [
        sys.executable,
        str(script_dir / "ast_analyzer_tool.py"),
        project_path,
        "--format", "json",
        "--output", str(ai_analyze_root / "reports" / "ast_analysis.json")
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ai_analyze_root))

    if result.returncode != 0:
        print(f"⚠️  AST 分析失败: {result.stderr}")
        return None

    print(result.stdout)

    ast_report = ai_analyze_root / "reports" / "ast_analysis.json"
    if ast_report.exists():
        print(f"✅ AST 分析完成: {ast_report.name}")
        return str(ast_report)

    return None


def run_ai_enhancement(serena_report_path, replace_original=False, use_cache=True, cache_ttl=3600):
    """运行 AI 增强分析"""
    print("\n🤖 步骤 3/4: 运行 AI 深度分析...")

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


def run_docker_generation(serena_report_path, force=False, analysis_data=None):
    """运行 Docker 生成（基于规则和代码复杂度分析）"""
    print("\n🐳 步骤 4/4: 生成 Docker 配置...")

    # 读取 Serena 报告获取项目路径
    import json
    with open(serena_report_path, 'r') as f:
        if not analysis_data:
            analysis_data = json.load(f)

    project_path = analysis_data.get('project_path', '')
    if not project_path:
        print("❌ 无法从报告中获取项目路径")
        return False

    # 运行 Docker 生成（现在完全基于规则，自动检测端口和基础镜像）
    cmd = [
        sys.executable,
        str(script_dir / "docker_generator.py"),
        project_path,
        "--analysis", serena_report_path
    ]

    if force:
        cmd.append("--force")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ai_analyze_root))

    if result.returncode != 0:
        print(f"❌ Docker 生成失败: {result.stderr}")
        return False

    print(result.stdout)
    return True


async def run_integrated_analysis(
    unified_report_path: str,
    project_path: str
) -> Optional[str]:
    """运行集成分析（相似性检测 + 质量评分）"""
    print("\n🔗 步骤 2.6: 运行集成分析（相似性检测 + 质量评分）...")

    try:
        # 加载统一分析结果
        with open(unified_report_path, 'r', encoding='utf-8') as f:
            unified_analysis = json.load(f)

        # 创建集成分析器
        from src.analysis_integration import AnalysisIntegrator
        integrator = AnalysisIntegrator(project_path)

        # 运行集成分析
        result = await integrator.integrate_analysis(unified_analysis)

        # 保存结果
        output_file = integrator.save_results(result, Path(unified_report_path).parent)

        print(f"✅ 集成分析完成: {output_file.name}")
        print(f"   - 重复代码对: {result.similarity_analysis.get('duplicate_pairs', 0)}")
        print(f"   - 相似代码对: {result.similarity_analysis.get('similar_pairs', 0)}")
        print(f"   - 质量评分: {result.quality_scores.get('overall_score', 0):.1f}/100 [{result.quality_scores.get('grade', 'F')}]")

        return str(output_file)

    except Exception as e:
        print(f"❌ 集成分析失败: {e}")
        return None


async def run_analyses_parallel(project_path: str):
    """并行运行 Serena 和 AST 分析"""
    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=2) as executor:
        print("\n🔄 并行运行 Serena 和 AST 分析...")

        # 提交两个任务
        serena_task = loop.run_in_executor(
            executor,
            run_serena_analysis_sync
        )
        ast_task = loop.run_in_executor(
            executor,
            run_ast_analysis_sync,
            project_path
        )

        # 等待两个任务完成
        serena_report, ast_report = await asyncio.gather(
            serena_task,
            ast_task,
            return_exceptions=True
        )

        # 处理异常
        if isinstance(serena_report, Exception):
            print(f"❌ Serena 分析失败: {serena_report}")
            serena_report = None

        if isinstance(ast_report, Exception):
            print(f"⚠️  AST 分析失败: {ast_report}")
            ast_report = None

    return serena_report, ast_report


async def merge_analyses_unified(
    serena_report_path: str,
    ast_report_path: str,
    project_path: str,
    incremental: Optional[IncrementalAnalyzer] = None
):
    """融合 Serena 和 AST 分析结果"""
    print("\n🔗 融合 Serena 和 AST 分析结果...")

    try:
        # 加载报告
        with open(serena_report_path, 'r', encoding='utf-8') as f:
            serena_report = json.load(f)

        with open(ast_report_path, 'r', encoding='utf-8') as f:
            ast_report = json.load(f)

        # 创建统一分析器
        analyzer = UnifiedAnalyzer(project_path)

        # 融合分析
        unified = await analyzer.analyze_project(serena_report, ast_report)

        # 保存融合结果
        # 从项目路径提取项目名
        from datetime import datetime
        project_name = Path(project_path).name or "project"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unified_report_path = Path(serena_report_path).parent / f"unified_analysis_{project_name}_{timestamp}.json"
        unified_dict = analyzer.to_dict(unified)

        with open(unified_report_path, 'w', encoding='utf-8') as f:
            f.write(analyzer.to_json(unified))

        print(f"✅ 融合完成: {unified_report_path.name}")
        print(f"   - 文件数: {len(unified.files)}")
        print(f"   - 总复杂度: {unified.total_complexity:.1f}")
        print(f"   - 代码坏味道: {unified.total_code_smells}")
        print(f"   - 质量分数: {unified.quality_score:.1f}/100")

        # 保存增量分析缓存
        if incremental:
            try:
                # 计算所有文件的哈希
                file_hashes = {}
                for file_data in unified.files:
                    file_path = file_data.file_path
                    if Path(file_path).exists():
                        file_hashes[file_path] = incremental.get_file_hash(file_path)

                # 保存缓存
                incremental.save_cache(project_path, unified_dict, file_hashes)
                print(f"💾 已缓存分析结果 ({len(file_hashes)} 个文件)")
            except Exception as e:
                print(f"⚠️  缓存保存失败: {e}")

        return str(unified_report_path)

    except Exception as e:
        print(f"❌ 融合失败: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="一键完整分析（Serena + AST + AI + Docker）")
    parser.add_argument(
        "--skip-ast",
        action="store_true",
        help="跳过 AST 分析"
    )
    parser.add_argument(
        "--skip-ai",
        action="store_true",
        help="跳过 AI 分析，只运行 Serena + AST + Docker"
    )
    parser.add_argument(
        "--skip-docker",
        action="store_true",
        help="跳过 Docker 生成，只运行 Serena + AST + AI"
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
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="清除所有缓存"
    )
    parser.add_argument(
        "--no-incremental",
        action="store_true",
        help="禁用增量分析，强制完整分析"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 一键完整分析工具 (Serena + AST + AI + Docker)")
    print("=" * 60)

    start_time = datetime.now()

    # 处理清除缓存命令
    if args.clear_cache:
        incremental = IncrementalAnalyzer()
        count = incremental.clear_cache()
        print(f"✅ 已清除 {count} 个缓存文件")
        sys.exit(0)

    # 检查 API Key
    if not args.serena_only and not args.skip_ai:
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  警告: 未设置 OPENAI_API_KEY")
            print("   AI 分析将不可用，请配置 .env 文件")
            if not confirm("   是否继续？", args.yes):
                sys.exit(1)

    # 步骤 1-2: 并行运行 Serena 和 AST 分析
    if args.report:
        # 使用已有的报告
        if not Path(args.report).exists():
            print(f"❌ 报告文件不存在: {args.report}")
            sys.exit(1)
        serena_report = args.report
        ast_report = None
        print(f"📄 使用已有报告: {serena_report}")
    else:
        # 并行执行 Serena 和 AST 分析
        if args.serena_only or args.skip_ast:
            # 只运行 Serena
            serena_report = run_serena_analysis_sync()
            ast_report = None
            if not serena_report:
                sys.exit(1)
        else:
            # 并行运行
            serena_report, ast_report = asyncio.run(
                run_analyses_parallel(os.getcwd())
            )
            if not serena_report:
                sys.exit(1)

    # 读取 Serena 报告获取项目信息
    import json
    with open(serena_report, 'r') as f:
        analysis_data = json.load(f)
    project_path = analysis_data.get('project_path', '')

    # 步骤 2.3: 检查增量分析（如果启用）
    incremental = IncrementalAnalyzer()
    use_incremental = not args.no_incremental and not args.serena_only

    if use_incremental and ast_report:
        # ast_report 是文件路径，需要加载 JSON
        try:
            with open(ast_report, 'r', encoding='utf-8') as f:
                ast_report_data = json.load(f)

            # 获取当前文件列表
            current_files = []
            for file_data in ast_report_data.get("files", []):
                current_files.append(file_data.get("file_path", ""))

            # 加载缓存
            cached_data = incremental.load_cache(project_path)

            # 获取分析状态
            status = incremental.get_analysis_status(project_path, current_files, cached_data)

            print(f"\n📊 增量分析状态: {status['message']}")
            if status['status'] == 'no_changes':
                print("✅ 使用缓存结果，跳过分析")
                # 使用缓存的统一报告
                unified_report = incremental.get_cache_path(project_path).parent / "unified_analysis.json"
                if unified_report.exists():
                    print(f"📄 加载缓存报告: {unified_report.name}")
            else:
                print(f"   - 修改文件: {len(status.get('modified_files', []))}")
                print(f"   - 新增文件: {len(status.get('new_files', []))}")
                print(f"   - 删除文件: {len(status.get('deleted_files', []))}")
        except Exception as e:
            print(f"⚠️  增量分析检查失败: {e}")

    # 步骤 2.5: 融合 Serena 和 AST 分析（如果都运行了）
    unified_report = None
    if ast_report and not args.skip_ast and not args.serena_only:
        unified_report = asyncio.run(
            merge_analyses_unified(serena_report, ast_report, project_path, incremental)
        )

        # 步骤 2.6: 运行集成分析（相似性检测 + 质量评分）
        if unified_report:
            integrated_report = asyncio.run(
                run_integrated_analysis(unified_report, project_path)
            )

    # 步骤 3: AI 分析（可选）
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

    # 步骤 4: Docker 生成（可选）
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

        # 显示 AST 报告
        if ast_report and Path(ast_report).exists():
            print(f"   - {Path(ast_report).name}")
            ast_md = ast_report.replace('.json', '.md')
            if Path(ast_md).exists():
                print(f"   - {Path(ast_md).name}")

        # 显示融合报告
        if unified_report and Path(unified_report).exists():
            print(f"   - {Path(unified_report).name} (融合分析)")

        # 显示集成分析报告
        integrated_report_path = reports_dir / "integrated_analysis.json"
        if integrated_report_path.exists():
            print(f"   - {integrated_report_path.name} (相似性 + 质量评分)")

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
