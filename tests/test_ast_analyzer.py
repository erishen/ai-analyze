#!/usr/bin/env python3
"""
AST 分析器单元测试
"""

import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径，使用包导入
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.analyzers.ast_analyzer import (  # noqa: E402
    PythonASTAnalyzer,
    JavaScriptASTAnalyzer,
    ASTAnalyzerFactory,
    Language,
    detect_language,
)


def test_detect_language():
    """测试语言检测"""
    assert detect_language("test.py") == Language.PYTHON
    assert detect_language("test.js") == Language.JAVASCRIPT
    assert detect_language("test.ts") == Language.TYPESCRIPT
    assert detect_language("test.tsx") == Language.TYPESCRIPT
    assert detect_language("test.go") == Language.GO
    assert detect_language("test.java") == Language.JAVA
    print("✅ 语言检测测试通过")


def test_python_analyzer():
    """测试 Python 分析器"""
    analyzer = PythonASTAnalyzer()

    # 创建临时 Python 文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
def simple_function(x, y):
    return x + y

def complex_function(a, b, c):
    if a > 0:
        if b > 0:
            if c > 0:
                return a + b + c
            else:
                return a + b
        else:
            return a
    else:
        return 0

class MyClass:
    def __init__(self):
        self.value = 0

    def method1(self):
        return self.value

    def method2(self):
        for i in range(10):
            for j in range(10):
                self.value += i * j
        return self.value
"""
        )
        temp_file = f.name

    try:
        result = analyzer.analyze_file(temp_file)

        # 验证基本信息
        assert result.file_path == temp_file
        assert result.language == "python"
        assert len(result.functions) > 0
        assert len(result.classes) > 0

        # 验证函数提取
        func_names = [f.name for f in result.functions]
        assert "simple_function" in func_names
        assert "complex_function" in func_names

        # 验证类提取
        class_names = [c.name for c in result.classes]
        assert "MyClass" in class_names

        # 验证复杂度计算
        assert result.overall_complexity.cyclomatic_complexity > 0
        assert result.overall_complexity.lines_of_code > 0

        print("✅ Python 分析器测试通过")

    finally:
        Path(temp_file).unlink()


def test_javascript_analyzer():
    """测试 JavaScript 分析器"""
    analyzer = JavaScriptASTAnalyzer()

    # 创建临时 JavaScript 文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write(
            """
function simpleFunction(x, y) {
    return x + y;
}

async function asyncFunction() {
    return await Promise.resolve(42);
}

class MyClass {
    constructor() {
        this.value = 0;
    }

    method1() {
        return this.value;
    }
}

const arrowFunction = (a, b) => a + b;
"""
        )
        temp_file = f.name

    try:
        result = analyzer.analyze_file(temp_file)

        # 验证基本信息
        assert result.file_path == temp_file
        assert result.language == "javascript"

        # 验证复杂度计算
        assert result.overall_complexity.cyclomatic_complexity > 0
        assert result.overall_complexity.lines_of_code > 0

        print("✅ JavaScript 分析器测试通过")

    finally:
        Path(temp_file).unlink()


def test_analyzer_factory():
    """测试分析器工厂"""
    # 测试 Python 分析器创建
    python_analyzer = ASTAnalyzerFactory.create_analyzer(Language.PYTHON)
    assert isinstance(python_analyzer, PythonASTAnalyzer)

    # 测试 JavaScript 分析器创建
    js_analyzer = ASTAnalyzerFactory.create_analyzer(Language.JAVASCRIPT)
    assert isinstance(js_analyzer, JavaScriptASTAnalyzer)

    print("✅ 分析器工厂测试通过")


def test_complexity_calculation():
    """测试复杂度计算"""
    analyzer = PythonASTAnalyzer()

    # 简单代码
    simple_code = "def foo(): return 1"
    simple_complexity = analyzer.calculate_complexity(simple_code)
    assert simple_complexity.cyclomatic_complexity == 1

    # 复杂代码
    complex_code = """
def foo(x):
    if x > 0:
        if x > 10:
            return 1
        else:
            return 2
    else:
        return 3
"""
    complex_complexity = analyzer.calculate_complexity(complex_code)
    assert complex_complexity.cyclomatic_complexity > 1

    print("✅ 复杂度计算测试通过")


def test_code_smell_detection():
    """测试代码坏味道检测"""
    analyzer = PythonASTAnalyzer()

    # 长方法代码
    long_method_code = (
        """
def long_function():
    """
        + "\n    ".join([f"x{i} = {i}" for i in range(60)])
        + """
    return x59
"""
    )

    smells = analyzer.detect_code_smells(long_method_code, "test.py")
    smell_names = [s.name for s in smells]

    # 应该检测到长方法
    assert any("Long" in name for name in smell_names)

    print("✅ 代码坏味道检测测试通过")


def run_all_tests():
    """运行所有测试"""
    print("🧪 开始运行 AST 分析器测试...\n")

    try:
        test_detect_language()
        test_python_analyzer()
        test_javascript_analyzer()
        test_analyzer_factory()
        test_complexity_calculation()
        test_code_smell_detection()

        print("\n✅ 所有测试通过！")
        return True

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
