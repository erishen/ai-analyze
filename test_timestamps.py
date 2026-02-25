#!/usr/bin/env python3
"""
测试时间戳和日期字段是否被正确添加到分析报告中
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from tools.ast_analyzer_tool import ASTAnalysisTool
from src.analysis_integration import AnalysisIntegrator, IntegratedAnalysisResult


def test_ast_timestamps():
    """测试 AST 分析中的时间戳"""
    print("=" * 60)
    print("测试 1: AST 分析时间戳")
    print("=" * 60)
    
    tool = ASTAnalysisTool(".")
    results = tool.analyze_project(file_patterns=['src/*.py'])
    
    # 检查时间戳字段
    assert 'timestamp' in results, "❌ 缺少 timestamp 字段"
    assert 'analysis_date' in results, "❌ 缺少 analysis_date 字段"
    assert 'project_path' in results, "❌ 缺少 project_path 字段"
    
    print(f"✅ 项目路径: {results['project_path']}")
    print(f"✅ 时间戳: {results['timestamp']}")
    print(f"✅ 分析日期: {results['analysis_date']}")
    
    # 验证时间戳格式
    try:
        datetime.fromisoformat(results['timestamp'])
        print(f"✅ 时间戳格式正确 (ISO 8601)")
    except ValueError:
        print(f"❌ 时间戳格式错误: {results['timestamp']}")
    
    print()


def test_integrated_timestamps():
    """测试集成分析中的时间戳"""
    print("=" * 60)
    print("测试 2: 集成分析时间戳")
    print("=" * 60)
    
    # 创建测试数据
    unified_analysis = {
        "project_path": "/test/project",
        "files": [],
        "summary": {}
    }
    
    result = IntegratedAnalysisResult(
        project_path="/test/project",
        unified_analysis=unified_analysis,
        similarity_analysis={"total_blocks": 0},
        quality_scores={"overall_score": 0}
    )
    
    # 转换为字典
    result_dict = result.to_dict()
    
    # 检查时间戳字段
    assert 'timestamp' in result_dict, "❌ 缺少 timestamp 字段"
    assert 'analysis_date' in result_dict, "❌ 缺少 analysis_date 字段"
    assert 'project_path' in result_dict, "❌ 缺少 project_path 字段"
    
    print(f"✅ 项目路径: {result_dict['project_path']}")
    print(f"✅ 时间戳: {result_dict['timestamp']}")
    print(f"✅ 分析日期: {result_dict['analysis_date']}")
    
    # 验证时间戳格式
    try:
        datetime.fromisoformat(result_dict['timestamp'])
        print(f"✅ 时间戳格式正确 (ISO 8601)")
    except ValueError:
        print(f"❌ 时间戳格式错误: {result_dict['timestamp']}")
    
    # 验证 JSON 序列化
    json_str = result.to_json()
    json_data = json.loads(json_str)
    assert 'timestamp' in json_data, "❌ JSON 中缺少 timestamp 字段"
    assert 'analysis_date' in json_data, "❌ JSON 中缺少 analysis_date 字段"
    print(f"✅ JSON 序列化正确")
    
    print()


if __name__ == "__main__":
    try:
        test_ast_timestamps()
        test_integrated_timestamps()
        
        print("=" * 60)
        print("🎉 所有时间戳测试通过！")
        print("=" * 60)
    
    except AssertionError as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
