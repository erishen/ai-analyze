#!/usr/bin/env python3
"""
Serena + AI 增强分析集成脚本
一键完成代码结构分析和 AI 深度分析
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

def run_serena_analysis(format_type="json"):
    """运行 Serena 分析"""
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
    print(f"✅ Serena 分析完成，报告: {latest_report.name}")
    
    return str(latest_report)


def run_ai_enhancement(serena_report_path):
    """运行 AI 增强分析"""
    print("🤖 运行 AI 深度分析...")
    
    cmd = [
        sys.executable,
        str(script_dir / "ai_enhanced_analyzer.py"),
        serena_report_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ai_analyze_root))
    
    if result.returncode != 0:
        print(f"❌ AI 分析失败: {result.stderr}")
        return False
    
    print(result.stdout)
    return True


def main():
    parser = argparse.ArgumentParser(description="Serena + AI 增强代码分析")
    parser.add_argument(
        "--skip-ai", 
        action="store_true",
        help="跳过 AI 分析，只运行 Serena 分析"
    )
    parser.add_argument(
        "--ai-only",
        action="store_true", 
        help="只运行 AI 增强分析（需要已有 Serena 报告）"
    )
    parser.add_argument(
        "--report",
        help="指定已有的 Serena JSON 报告路径（用于 ai-only 模式）"
    )
    
    args = parser.parse_args()
    
    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  警告: 未设置 OPENAI_API_KEY，AI 分析将不可用")
        print("   请在 ai-analyze/.env 文件中添加:")
        print("   OPENAI_API_KEY=your_deepseek_api_key")
        print("   OPENAI_BASE_URL=https://api.deepseek.com")
        print("   OPENAI_MODEL=deepseek-chat")
    
    if args.ai_only:
        # 仅 AI 模式
        if not args.report:
            print("❌ ai-only 模式需要指定 --report 参数")
            sys.exit(1)
        
        if not os.path.exists(args.report):
            print(f"❌ 报告文件不存在: {args.report}")
            sys.exit(1)
        
        success = run_ai_enhancement(args.report)
        sys.exit(0 if success else 1)
    
    else:
        # 完整分析流程
        serena_report = run_serena_analysis()
        
        if not serena_report:
            sys.exit(1)
        
        if args.skip_ai or not os.getenv("OPENAI_API_KEY"):
            print("\n✅ Serena 分析完成（跳过 AI 增强）")
            sys.exit(0)
        
        success = run_ai_enhancement(serena_report)
        
        if success:
            print("\n🎉 完整分析完成！")
            # 获取增强后的报告路径
            enhanced_md = serena_report.replace('.json', '-ai.md')
            if os.path.exists(enhanced_md):
                print(f"📄 增强报告: {enhanced_md}")
        
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
