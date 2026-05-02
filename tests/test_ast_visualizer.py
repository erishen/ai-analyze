#!/usr/bin/env python3
"""AST 可视化模块测试"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ast_analyzer import (  # noqa: E402
    ClassInfo,
    CodeSmell,
    ComplexityMetrics,
    FileAnalysisResult,
    FunctionInfo,
)
from src.ast_visualizer import ASTVisualizer  # noqa: E402


class TestASTVisualizer(unittest.TestCase):
    """AST 可视化器测试"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.visualizer = ASTVisualizer(output_dir=self.temp_dir)

        # 创建测试用的分析结果
        self.sample_result = FileAnalysisResult(
            file_path="test_sample.py",
            language="python",
            total_lines=50,
            functions=[
                FunctionInfo(
                    name="simple_func",
                    language="python",
                    file_path="test_sample.py",
                    line_start=1,
                    line_end=5,
                    complexity=ComplexityMetrics(2, 2, 1, 5, 0, 0),
                    parameters=["x"],
                    return_type="int",
                    is_async=False,
                    is_static=False,
                    code_smells=[],
                ),
                FunctionInfo(
                    name="complex_func",
                    language="python",
                    file_path="test_sample.py",
                    line_start=10,
                    line_end=40,
                    complexity=ComplexityMetrics(15, 15, 5, 30, 2, 3),
                    parameters=["a", "b", "c", "d", "e", "f"],
                    return_type=None,
                    is_async=False,
                    is_static=False,
                    code_smells=[
                        CodeSmell(
                            name="COMPLEX001",
                            severity="high",
                            location="test_sample.py:10",
                            description="Function too long",
                            suggestion="Break into smaller functions",
                        )
                    ],
                ),
            ],
            classes=[
                ClassInfo(
                    name="MyClass",
                    language="python",
                    file_path="test_sample.py",
                    line_start=42,
                    line_end=50,
                    methods=[
                        FunctionInfo(
                            name="__init__",
                            language="python",
                            file_path="test_sample.py",
                            line_start=43,
                            line_end=45,
                            complexity=ComplexityMetrics(1, 1, 0, 3, 0, 0),
                            parameters=["self"],
                            return_type=None,
                            is_async=False,
                            is_static=False,
                            code_smells=[],
                        ),
                    ],
                    properties=["value"],
                    inheritance_depth=1,
                    code_smells=[],
                ),
            ],
            imports=["os", "sys", "json"],
            exports=[],
            code_smells=[
                CodeSmell(
                    name="SEC001",
                    severity="critical",
                    location="test_sample.py:5",
                    description="Use of eval()",
                    suggestion="Avoid eval(), use ast.literal_eval()",
                ),
            ],
            overall_complexity=ComplexityMetrics(18, 18, 5, 45, 5, 5),
        )

    def test_visualize_tree_html(self):
        """测试 AST 树形 HTML 可视化"""
        filepath = self.visualizer.visualize_tree(self.sample_result, output_format="html")

        self.assertTrue(Path(filepath).exists())
        content = Path(filepath).read_text(encoding="utf-8")
        self.assertIn("AST Tree Visualization", content)
        self.assertIn("test_sample.py", content)
        self.assertIn("class MyClass", content)
        self.assertIn("simple_func", content)
        self.assertIn("complex_func", content)
        self.assertIn("Imports", content)

    def test_visualize_tree_json(self):
        """测试 AST 树形 JSON 可视化"""
        filepath = self.visualizer.visualize_tree(self.sample_result, output_format="json")

        self.assertTrue(Path(filepath).exists())
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["name"], "test_sample.py")
        self.assertEqual(data["type"], "file")
        self.assertIn("children", data)
        self.assertIn("metrics", data)

    def test_visualize_complexity_heatmap_html(self):
        """测试复杂度热力图 HTML"""
        filepath = self.visualizer.visualize_complexity_heatmap(
            [self.sample_result], output_format="html"
        )

        self.assertTrue(Path(filepath).exists())
        content = Path(filepath).read_text(encoding="utf-8")
        self.assertIn("AST Complexity Heatmap", content)
        self.assertIn("test_sample.py", content)

    def test_visualize_complexity_heatmap_json(self):
        """测试复杂度热力图 JSON"""
        filepath = self.visualizer.visualize_complexity_heatmap(
            [self.sample_result], output_format="json"
        )

        self.assertTrue(Path(filepath).exists())
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["file"], "test_sample.py")
        self.assertEqual(data[0]["cyclomatic_complexity"], 18)
        self.assertEqual(data[0]["function_count"], 2)
        self.assertEqual(data[0]["class_count"], 1)

    def test_severity_color(self):
        """测试严重程度颜色映射"""
        self.assertEqual(ASTVisualizer._severity_color("critical"), "#dc3545")
        self.assertEqual(ASTVisualizer._severity_color("high"), "#fd7e14")
        self.assertEqual(ASTVisualizer._severity_color("medium"), "#ffc107")
        self.assertEqual(ASTVisualizer._severity_color("low"), "#20c997")
        self.assertEqual(ASTVisualizer._severity_color("info"), "#0d6efd")

    def test_type_icon(self):
        """测试节点类型图标"""
        self.assertEqual(ASTVisualizer._type_icon("file"), "📄")
        self.assertEqual(ASTVisualizer._type_icon("class"), "🏗️")
        self.assertEqual(ASTVisualizer._type_icon("function"), "⚡")

    def test_worst_severity(self):
        """测试最严重程度计算"""
        smells = [
            CodeSmell("a", "low", "f:1", "d", "s"),
            CodeSmell("b", "critical", "f:2", "d", "s"),
            CodeSmell("c", "medium", "f:3", "d", "s"),
        ]
        self.assertEqual(ASTVisualizer._worst_severity(smells), "critical")

    def test_compute_file_severity(self):
        """测试文件严重程度计算"""
        self.assertEqual(ASTVisualizer._compute_file_severity(self.sample_result), "high")

    def test_empty_result(self):
        """测试空分析结果"""
        empty_result = FileAnalysisResult(
            file_path="empty.py",
            language="python",
            total_lines=0,
            functions=[],
            classes=[],
            imports=[],
            exports=[],
            code_smells=[],
            overall_complexity=ComplexityMetrics(0, 0, 0, 0, 0, 0),
        )

        filepath = self.visualizer.visualize_tree(empty_result, output_format="html")
        self.assertTrue(Path(filepath).exists())

        filepath = self.visualizer.visualize_tree(empty_result, output_format="json")
        self.assertTrue(Path(filepath).exists())


if __name__ == "__main__":
    unittest.main()
