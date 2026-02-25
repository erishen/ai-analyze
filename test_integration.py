#!/usr/bin/env python3
"""
测试集成分析功能
"""

import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.analysis_integration import AnalysisIntegrator
from src.similarity import SimilarityDetector, CodeBlock
from src.quality_score import QualityScorer, QualityMetrics


def test_similarity_detector():
    """测试相似性检测"""
    print("=" * 60)
    print("测试 1: 相似性检测")
    print("=" * 60)
    
    # 创建测试代码块
    code1 = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
"""
    
    code2 = """
def calculate_sum(items):
    result = 0
    for item in items:
        result += item
    return result
"""
    
    block1 = CodeBlock("file1.py", 1, 5, code1)
    block2 = CodeBlock("file2.py", 1, 5, code2)
    
    detector = SimilarityDetector()
    detector.add_code_blocks([block1, block2])
    
    similar = detector.detect_similar(threshold=0.5)
    
    print(f"✅ 检测到 {len(similar)} 个相似代码对")
    if similar:
        for s in similar:
            print(f"   - 相似度: {s.similarity:.1%}")
    
    print()


def test_quality_scorer():
    """测试质量评分"""
    print("=" * 60)
    print("测试 2: 质量评分")
    print("=" * 60)
    
    metrics = QualityMetrics(
        cyclomatic_complexity=8.5,
        cognitive_complexity=15.2,
        code_smells=3,
        duplication_ratio=0.08,
        test_coverage=0.75,
        documentation_ratio=0.6,
        lines_of_code=500,
        comment_lines=50,
        blank_lines=30,
        maintainability_index=75.0,
        technical_debt=0.3
    )
    
    scorer = QualityScorer()
    score = scorer.calculate_score(metrics)
    
    print(f"✅ 质量评分: {score.overall_score:.1f}/100 [{score.grade}]")
    print(f"   - 复杂度评分: {score.complexity_score:.1f}/100")
    print(f"   - 可维护性评分: {score.maintainability_score:.1f}/100")
    print(f"   - 可靠性评分: {score.reliability_score:.1f}/100")
    print(f"   - 安全性评分: {score.security_score:.1f}/100")
    
    if score.recommendations:
        print(f"\n   建议:")
        for rec in score.recommendations[:3]:
            print(f"   - {rec}")
    
    print()


async def test_analysis_integrator():
    """测试分析集成器"""
    print("=" * 60)
    print("测试 3: 分析集成器")
    print("=" * 60)
    
    # 创建测试统一分析结果
    unified_analysis = {
        "project_path": "/test/project",
        "files": [
            {
                "file_path": "test.py",
                "language": "python",
                "lines_of_code": 100,
                "functions": [
                    {
                        "name": "test_func",
                        "start_line": 1,
                        "end_line": 10,
                        "content": "def test_func():\n    pass",
                        "cyclomatic_complexity": 1
                    }
                ],
                "classes": [],
                "code_smells": 0
            }
        ],
        "duplication_ratio": 0.05,
        "test_coverage": 0.8,
        "documentation_ratio": 0.7,
        "maintainability_index": 80,
        "technical_debt": 0.2
    }
    
    integrator = AnalysisIntegrator("/test/project")
    
    # 测试相似性分析
    similarity = await integrator._analyze_similarity(unified_analysis)
    print(f"✅ 相似性分析: {similarity.get('total_blocks', 0)} 个代码块")
    
    # 测试质量分析
    quality = await integrator._analyze_quality(unified_analysis)
    print(f"✅ 质量分析: {quality.get('overall_score', 0):.1f}/100 [{quality.get('grade', 'F')}]")
    
    print()


if __name__ == "__main__":
    import asyncio
    
    try:
        test_similarity_detector()
        test_quality_scorer()
        asyncio.run(test_analysis_integrator())
        
        print("=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
