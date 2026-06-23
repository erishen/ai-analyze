#!/usr/bin/env python3
"""
测试文件名格式是否包含项目名和日期
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

from tools.ast_analyzer_tool import ASTAnalysisTool  # noqa: E402
from src.server.analysis_integration import (  # noqa: E402
    AnalysisIntegrator, IntegratedAnalysisResult,
)


def test_ast_filename_format():
    """测试 AST 分析文件名格式"""
    print("=" * 60)
    print("测试 1: AST 分析文件名格式")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建一个测试项目目录
        project_dir = Path(tmpdir) / "test-project"
        project_dir.mkdir()

        # 创建一个测试 Python 文件
        test_file = project_dir / "test.py"
        test_file.write_text("def hello():\n    pass\n")

        # 运行 AST 分析
        tool = ASTAnalysisTool(str(project_dir))

        # 生成报告（不指定输出路径，让它自动生成）
        result_path = tool.generate_report()

        # 检查文件名格式
        filename = Path(result_path).name
        print(f"✅ 生成的文件名: {filename}")

        # 验证文件名包含项目名
        assert "test-project" in filename, f"❌ 文件名不包含项目名: {filename}"
        print("✅ 文件名包含项目名: test-project")

        # 验证文件名包含日期
        assert "_20" in filename, f"❌ 文件名不包含日期: {filename}"
        print("✅ 文件名包含日期")

        # 验证文件名格式
        # 应该是: ast_analysis_test-project_20260216_204007.json
        assert filename.startswith("ast_analysis_"), f"❌ 文件名格式错误: {filename}"
        assert filename.endswith(".json"), f"❌ 文件名后缀错误: {filename}"
        print("✅ 文件名格式正确")

    print()


def test_integrated_filename_format():
    """测试集成分析文件名格式"""
    print("=" * 60)
    print("测试 2: 集成分析文件名格式")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "my-project"
        project_dir.mkdir()

        # 创建集成分析结果
        result = IntegratedAnalysisResult(
            project_path=str(project_dir),
            unified_analysis={"files": []},
            similarity_analysis={"total_blocks": 0},
            quality_scores={"overall_score": 0}
        )

        # 保存结果
        integrator = AnalysisIntegrator(str(project_dir))
        output_file = integrator.save_results(result, Path(tmpdir))

        # 检查文件名格式
        filename = output_file.name
        print(f"✅ 生成的文件名: {filename}")

        # 验证文件名包含项目名
        assert "my-project" in filename, f"❌ 文件名不包含项目名: {filename}"
        print("✅ 文件名包含项目名: my-project")

        # 验证文件名包含日期
        assert "_20" in filename, f"❌ 文件名不包含日期: {filename}"
        print("✅ 文件名包含日期")

        # 验证文件名格式
        # 应该是: integrated_analysis_my-project_20260216_204007.json
        assert filename.startswith("integrated_analysis_"), f"❌ 文件名格式错误: {filename}"
        assert filename.endswith(".json"), f"❌ 文件名后缀错误: {filename}"
        print("✅ 文件名格式正确")

    print()


def test_filename_components():
    """测试文件名各个组件"""
    print("=" * 60)
    print("测试 3: 文件名组件解析")
    print("=" * 60)

    # 示例文件名
    examples = [
        "ast_analysis_nsbp-shop_20260216_204007.json",
        "integrated_analysis_my-project_20260216_204007.json",
        "unified_analysis_test-project_20260216_204007.json",
    ]

    for filename in examples:
        print(f"\n分析文件名: {filename}")

        # 解析文件名
        parts = filename.replace(".json", "").split("_")

        # 提取组件
        analysis_type = parts[0]  # ast, integrated, unified
        project_name = parts[2]   # 项目名
        date_part = parts[3]      # 日期 (YYYYMMDD)
        time_part = parts[4]      # 时间 (HHMMSS)

        print(f"  - 分析类型: {analysis_type}")
        print(f"  - 项目名: {project_name}")
        print(f"  - 日期: {date_part}")
        print(f"  - 时间: {time_part}")

        # 验证日期格式
        try:
            date_obj = datetime.strptime(date_part, "%Y%m%d")
            print(f"  - 日期有效: {date_obj.strftime('%Y-%m-%d')}")
        except ValueError:
            print("  - ❌ 日期格式错误")

    print()


if __name__ == "__main__":
    try:
        test_ast_filename_format()
        test_integrated_filename_format()
        test_filename_components()

        print("=" * 60)
        print("🎉 所有文件名格式测试通过！")
        print("=" * 60)

    except AssertionError as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
