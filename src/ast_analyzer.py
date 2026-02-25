#!/usr/bin/env python3
"""
AST (Abstract Syntax Tree) 分析模块
支持多语言代码复杂度分析、代码坏味道检测、控制流分析等
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class Language(Enum):
    """支持的编程语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    CPP = "cpp"
    RUST = "rust"


@dataclass
class ComplexityMetrics:
    """代码复杂度指标"""
    cyclomatic_complexity: int  # 圈复杂度
    cognitive_complexity: int  # 认知复杂度
    nesting_depth: int  # 最大嵌套深度
    lines_of_code: int  # 代码行数
    comment_lines: int  # 注释行数
    blank_lines: int  # 空白行数


@dataclass
class CodeSmell:
    """代码坏味道"""
    name: str  # 坏味道名称
    severity: str  # 严重程度: low, medium, high, critical
    location: str  # 位置: 文件:行号
    description: str  # 描述
    suggestion: str  # 改进建议


@dataclass
class FunctionInfo:
    """函数/方法信息"""
    name: str
    language: str
    file_path: str
    line_start: int
    line_end: int
    complexity: ComplexityMetrics
    parameters: List[str]
    return_type: Optional[str]
    is_async: bool
    is_static: bool
    code_smells: List[CodeSmell]


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    language: str
    file_path: str
    line_start: int
    line_end: int
    methods: List[FunctionInfo]
    properties: List[str]
    inheritance_depth: int
    code_smells: List[CodeSmell]


@dataclass
class FileAnalysisResult:
    """文件分析结果"""
    file_path: str
    language: str
    total_lines: int
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    imports: List[str]
    exports: List[str]
    code_smells: List[CodeSmell]
    overall_complexity: ComplexityMetrics


class ASTAnalyzer(ABC):
    """AST 分析器基类"""

    def __init__(self, language: Language):
        self.language = language

    @abstractmethod
    def analyze_file(self, file_path: str) -> FileAnalysisResult:
        """分析单个文件"""
        pass

    @abstractmethod
    def calculate_complexity(self, code: str) -> ComplexityMetrics:
        """计算代码复杂度"""
        pass

    @abstractmethod
    def detect_code_smells(self, code: str, file_path: str) -> List[CodeSmell]:
        """检测代码坏味道"""
        pass


class PythonASTAnalyzer(ASTAnalyzer):
    """Python AST 分析器"""

    def __init__(self):
        super().__init__(Language.PYTHON)
        try:
            import ast
            import astroid
            self.ast = ast
            self.astroid = astroid
        except ImportError:
            logger.warning("astroid not installed, some features will be limited")

    def analyze_file(self, file_path: str) -> FileAnalysisResult:
        """分析 Python 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        lines = code.split('\n')
        total_lines = len(lines)

        try:
            tree = self.ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return FileAnalysisResult(
                file_path=file_path,
                language=self.language.value,
                total_lines=total_lines,
                functions=[],
                classes=[],
                imports=[],
                exports=[],
                code_smells=[],
                overall_complexity=ComplexityMetrics(0, 0, 0, total_lines, 0, 0)
            )

        functions = self._extract_functions(tree, file_path, code)
        classes = self._extract_classes(tree, file_path, code)
        imports = self._extract_imports(tree)
        code_smells = self.detect_code_smells(code, file_path)
        overall_complexity = self.calculate_complexity(code)

        return FileAnalysisResult(
            file_path=file_path,
            language=self.language.value,
            total_lines=total_lines,
            functions=functions,
            classes=classes,
            imports=imports,
            exports=[],
            code_smells=code_smells,
            overall_complexity=overall_complexity
        )

    def _extract_functions(self, tree, file_path: str, code: str) -> List[FunctionInfo]:
        """提取函数信息"""
        functions = []
        lines = code.split('\n')

        for node in self.ast.walk(tree):
            if isinstance(node, self.ast.FunctionDef):
                func_info = FunctionInfo(
                    name=node.name,
                    language=self.language.value,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    complexity=self._calculate_function_complexity(node),
                    parameters=[arg.arg for arg in node.args.args],
                    return_type=self._extract_return_type(node),
                    is_async=isinstance(node, self.ast.AsyncFunctionDef),
                    is_static=self._is_static_method(node),
                    code_smells=[]
                )
                functions.append(func_info)

        return functions

    def _extract_classes(self, tree, file_path: str, code: str) -> List[ClassInfo]:
        """提取类信息"""
        classes = []

        for node in self.ast.walk(tree):
            if isinstance(node, self.ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, (self.ast.FunctionDef, self.ast.AsyncFunctionDef)):
                        methods.append(FunctionInfo(
                            name=item.name,
                            language=self.language.value,
                            file_path=file_path,
                            line_start=item.lineno,
                            line_end=item.end_lineno or item.lineno,
                            complexity=self._calculate_function_complexity(item),
                            parameters=[arg.arg for arg in item.args.args],
                            return_type=self._extract_return_type(item),
                            is_async=isinstance(item, self.ast.AsyncFunctionDef),
                            is_static=self._is_static_method(item),
                            code_smells=[]
                        ))

                class_info = ClassInfo(
                    name=node.name,
                    language=self.language.value,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    methods=methods,
                    properties=[],
                    inheritance_depth=len(node.bases),
                    code_smells=[]
                )
                classes.append(class_info)

        return classes

    def _extract_imports(self, tree) -> List[str]:
        """提取导入语句"""
        imports = []

        for node in self.ast.walk(tree):
            if isinstance(node, self.ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, self.ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)

        return imports

    def _calculate_function_complexity(self, node) -> ComplexityMetrics:
        """计算函数的圈复杂度"""
        cyclomatic = 1
        nesting_depth = 0
        current_depth = 0

        for child in self.ast.walk(node):
            if isinstance(child, (self.ast.If, self.ast.For, self.ast.While, self.ast.ExceptHandler)):
                cyclomatic += 1
            if isinstance(child, (self.ast.If, self.ast.For, self.ast.While, self.ast.With)):
                current_depth += 1
                nesting_depth = max(nesting_depth, current_depth)

        lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 1

        return ComplexityMetrics(
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cyclomatic,  # 简化版本
            nesting_depth=nesting_depth,
            lines_of_code=lines,
            comment_lines=0,
            blank_lines=0
        )

    def _extract_return_type(self, node) -> Optional[str]:
        """提取返回类型"""
        if node.returns:
            if isinstance(node.returns, self.ast.Name):
                return node.returns.id
            elif isinstance(node.returns, self.ast.Constant):
                return str(node.returns.value)
        return None

    def _is_static_method(self, node) -> bool:
        """检查是否为静态方法"""
        for decorator in node.decorator_list:
            if isinstance(decorator, self.ast.Name) and decorator.id == 'staticmethod':
                return True
        return False

    def calculate_complexity(self, code: str) -> ComplexityMetrics:
        """计算整个文件的复杂度"""
        try:
            tree = self.ast.parse(code)
        except SyntaxError:
            return ComplexityMetrics(0, 0, 0, len(code.split('\n')), 0, 0)

        lines = code.split('\n')
        total_lines = len(lines)
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        blank_lines = sum(1 for line in lines if not line.strip())

        cyclomatic = 1
        for node in self.ast.walk(tree):
            if isinstance(node, (self.ast.If, self.ast.For, self.ast.While, self.ast.ExceptHandler)):
                cyclomatic += 1

        return ComplexityMetrics(
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cyclomatic,
            nesting_depth=0,
            lines_of_code=total_lines - blank_lines - comment_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines
        )

    def detect_code_smells(self, code: str, file_path: str) -> List[CodeSmell]:
        """检测代码坏味道"""
        smells = []
        lines = code.split('\n')

        try:
            tree = self.ast.parse(code)
        except SyntaxError:
            return smells

        # 检测长函数
        for node in self.ast.walk(tree):
            if isinstance(node, (self.ast.FunctionDef, self.ast.AsyncFunctionDef)):
                func_lines = (node.end_lineno or node.lineno) - node.lineno + 1
                if func_lines > 50:
                    smells.append(CodeSmell(
                        name="Long Method",
                        severity="medium",
                        location=f"{file_path}:{node.lineno}",
                        description=f"Function '{node.name}' has {func_lines} lines",
                        suggestion="Consider breaking this function into smaller, more focused functions"
                    ))

            # 检测大类
            if isinstance(node, self.ast.ClassDef):
                class_lines = (node.end_lineno or node.lineno) - node.lineno + 1
                if class_lines > 200:
                    smells.append(CodeSmell(
                        name="Large Class",
                        severity="medium",
                        location=f"{file_path}:{node.lineno}",
                        description=f"Class '{node.name}' has {class_lines} lines",
                        suggestion="Consider splitting this class into smaller, more focused classes"
                    ))

        # 检测深层嵌套
        for i, line in enumerate(lines, 1):
            indent = len(line) - len(line.lstrip())
            if indent > 24:  # 超过 6 层嵌套
                smells.append(CodeSmell(
                    name="Deep Nesting",
                    severity="low",
                    location=f"{file_path}:{i}",
                    description=f"Line has excessive indentation ({indent} spaces)",
                    suggestion="Consider refactoring to reduce nesting depth"
                ))

        return smells


class JavaScriptASTAnalyzer(ASTAnalyzer):
    """JavaScript/TypeScript AST 分析器"""

    def __init__(self, language: Language = Language.JAVASCRIPT):
        super().__init__(language)
        self.tree_sitter = None
        try:
            import tree_sitter
            from tree_sitter import Language, Parser
            self.tree_sitter = tree_sitter
            self.Language = Language
            self.Parser = Parser
        except ImportError:
            logger.warning("tree-sitter not installed, JavaScript analysis will be limited")

    def analyze_file(self, file_path: str) -> FileAnalysisResult:
        """分析 JavaScript/TypeScript 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        lines = code.split('\n')
        total_lines = len(lines)

        # 简化版本：基于正则表达式的分析
        functions = self._extract_functions_regex(code, file_path)
        classes = self._extract_classes_regex(code, file_path)
        imports = self._extract_imports_regex(code)
        code_smells = self.detect_code_smells(code, file_path)
        overall_complexity = self.calculate_complexity(code)

        return FileAnalysisResult(
            file_path=file_path,
            language=self.language.value,
            total_lines=total_lines,
            functions=functions,
            classes=classes,
            imports=imports,
            exports=[],
            code_smells=code_smells,
            overall_complexity=overall_complexity
        )

    def _extract_functions_regex(self, code: str, file_path: str) -> List[FunctionInfo]:
        """使用正则表达式提取函数"""
        import re
        functions = []
        lines = code.split('\n')

        # 匹配函数声明
        patterns = [
            r'(?:async\s+)?function\s+(\w+)\s*\(',  # function foo()
            r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*{',  # foo() {
            r'(?:async\s+)?(\w+)\s*:\s*(?:async\s+)?\([^)]*\)\s*=>',  # foo: () =>
        ]

        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    func_name = match.group(1)
                    functions.append(FunctionInfo(
                        name=func_name,
                        language=self.language.value,
                        file_path=file_path,
                        line_start=i,
                        line_end=i,
                        complexity=ComplexityMetrics(1, 1, 0, 1, 0, 0),
                        parameters=[],
                        return_type=None,
                        is_async='async' in line,
                        is_static=False,
                        code_smells=[]
                    ))

        return functions

    def _extract_classes_regex(self, code: str, file_path: str) -> List[ClassInfo]:
        """使用正则表达式提取类"""
        import re
        classes = []
        lines = code.split('\n')

        for i, line in enumerate(lines, 1):
            if re.search(r'class\s+(\w+)', line):
                match = re.search(r'class\s+(\w+)', line)
                if match:
                    class_name = match.group(1)
                    classes.append(ClassInfo(
                        name=class_name,
                        language=self.language.value,
                        file_path=file_path,
                        line_start=i,
                        line_end=i,
                        methods=[],
                        properties=[],
                        inheritance_depth=1 if 'extends' in line else 0,
                        code_smells=[]
                    ))

        return classes

    def _extract_imports_regex(self, code: str) -> List[str]:
        """使用正则表达式提取导入"""
        import re
        imports = []

        patterns = [
            r"import\s+(?:{[^}]+}|[\w*]+)\s+from\s+['\"]([^'\"]+)['\"]",
            r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, code)
            imports.extend(matches)

        return imports

    def calculate_complexity(self, code: str) -> ComplexityMetrics:
        """计算 JavaScript 代码复杂度"""
        import re

        lines = code.split('\n')
        total_lines = len(lines)
        comment_lines = sum(1 for line in lines if re.search(r'^\s*(/|//|\*)', line))
        blank_lines = sum(1 for line in lines if not line.strip())

        # 计算圈复杂度
        cyclomatic = 1
        for line in lines:
            if re.search(r'\b(if|else|case|for|while|catch)\b', line):
                cyclomatic += 1

        return ComplexityMetrics(
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cyclomatic,
            nesting_depth=0,
            lines_of_code=total_lines - blank_lines - comment_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines
        )

    def detect_code_smells(self, code: str, file_path: str) -> List[CodeSmell]:
        """检测 JavaScript 代码坏味道"""
        import re
        smells = []
        lines = code.split('\n')

        # 检测长函数
        in_function = False
        func_start = 0
        brace_count = 0

        for i, line in enumerate(lines, 1):
            if re.search(r'(?:async\s+)?function\s+\w+|(?:async\s+)?\w+\s*\([^)]*\)\s*{', line):
                in_function = True
                func_start = i
                brace_count = line.count('{') - line.count('}')
            elif in_function:
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    func_lines = i - func_start + 1
                    if func_lines > 50:
                        smells.append(CodeSmell(
                            name="Long Function",
                            severity="medium",
                            location=f"{file_path}:{func_start}",
                            description=f"Function has {func_lines} lines",
                            suggestion="Consider breaking this function into smaller functions"
                        ))
                    in_function = False

        return smells


class ASTAnalyzerFactory:
    """AST 分析器工厂"""

    _analyzers = {
        Language.PYTHON: PythonASTAnalyzer,
        Language.JAVASCRIPT: JavaScriptASTAnalyzer,
        Language.TYPESCRIPT: lambda: JavaScriptASTAnalyzer(Language.TYPESCRIPT),
    }

    @classmethod
    def create_analyzer(cls, language: Language) -> ASTAnalyzer:
        """创建指定语言的分析器"""
        if language not in cls._analyzers:
            logger.warning(f"No analyzer for {language.value}, using JavaScript analyzer")
            return JavaScriptASTAnalyzer()

        analyzer_class = cls._analyzers[language]
        if callable(analyzer_class):
            return analyzer_class()
        return analyzer_class()

    @classmethod
    def register_analyzer(cls, language: Language, analyzer_class):
        """注册自定义分析器"""
        cls._analyzers[language] = analyzer_class


def detect_language(file_path: str) -> Optional[Language]:
    """根据文件扩展名检测语言"""
    ext_to_lang = {
        '.py': Language.PYTHON,
        '.js': Language.JAVASCRIPT,
        '.jsx': Language.JAVASCRIPT,
        '.ts': Language.TYPESCRIPT,
        '.tsx': Language.TYPESCRIPT,
        '.go': Language.GO,
        '.java': Language.JAVA,
        '.cpp': Language.CPP,
        '.cc': Language.CPP,
        '.rs': Language.RUST,
    }

    suffix = Path(file_path).suffix.lower()
    return ext_to_lang.get(suffix)
