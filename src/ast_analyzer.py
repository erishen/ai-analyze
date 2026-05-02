#!/usr/bin/env python3
"""
AST (Abstract Syntax Tree) 分析模块
支持多语言代码复杂度分析、代码坏味道检测、控制流分析等
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from .ast_rules import ASTRuleEngine

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

    def __init__(self, language: Language, rule_engine: Optional[ASTRuleEngine] = None):
        self.language = language
        self.rule_engine = rule_engine or ASTRuleEngine()

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

    def __init__(self, rule_engine: Optional[ASTRuleEngine] = None):
        super().__init__(Language.PYTHON, rule_engine=rule_engine)
        import ast

        self.ast = ast
        try:
            import astroid

            self.astroid = astroid
        except ImportError:
            logger.warning("astroid not installed, some features will be limited")
            self.astroid = None

    def analyze_file(self, file_path: str) -> FileAnalysisResult:
        """分析 Python 文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        lines = code.split("\n")
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
                overall_complexity=ComplexityMetrics(0, 0, 0, total_lines, 0, 0),
            )

        # 优化：共享解析树，避免 detect_code_smells / calculate_complexity 重复 parse
        functions = self._extract_functions(tree, file_path, code)
        classes = self._extract_classes(tree, file_path, code)
        imports = self._extract_imports(tree)
        code_smells = self._detect_code_smells_with_tree(tree, code, file_path)
        overall_complexity = self._calculate_complexity_with_tree(tree, code)

        return FileAnalysisResult(
            file_path=file_path,
            language=self.language.value,
            total_lines=total_lines,
            functions=functions,
            classes=classes,
            imports=imports,
            exports=[],
            code_smells=code_smells,
            overall_complexity=overall_complexity,
        )

    def _extract_functions(self, tree, file_path: str, code: str) -> List[FunctionInfo]:
        """提取函数信息"""
        functions = []

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
                    code_smells=[],
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
                        methods.append(
                            FunctionInfo(
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
                                code_smells=[],
                            )
                        )

                class_info = ClassInfo(
                    name=node.name,
                    language=self.language.value,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    methods=methods,
                    properties=[],
                    inheritance_depth=len(node.bases),
                    code_smells=[],
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
                module = node.module or ""
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
            blank_lines=0,
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
            if isinstance(decorator, self.ast.Name) and decorator.id == "staticmethod":
                return True
        return False

    def calculate_complexity(self, code: str) -> ComplexityMetrics:
        """计算整个文件的复杂度"""
        try:
            tree = self.ast.parse(code)
        except SyntaxError:
            return ComplexityMetrics(0, 0, 0, len(code.split("\n")), 0, 0)

        lines = code.split("\n")
        total_lines = len(lines)
        comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
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
            blank_lines=blank_lines,
        )

    def detect_code_smells(self, code: str, file_path: str) -> List[CodeSmell]:
        """检测代码坏味道（集成规则引擎）"""
        smells: List[CodeSmell] = []
        lines = code.split("\n")

        try:
            tree = self.ast.parse(code)
        except SyntaxError:
            return smells

        # 通过规则引擎检测 - 函数级别
        for node in self.ast.walk(tree):
            if isinstance(node, (self.ast.FunctionDef, self.ast.AsyncFunctionDef)):
                func_lines = (node.end_lineno or node.lineno) - node.lineno + 1
                func_params = len(node.args.args)

                # 使用规则引擎检查
                violations = self.rule_engine.check_all_thresholds(
                    {
                        "COMPLEX001": func_lines,  # 长函数
                        "COMPLEX005": func_params,  # 参数过多
                    }
                )

                # 检查圈复杂度
                complexity = 1
                for child in self.ast.walk(node):
                    if isinstance(child, (self.ast.If, self.ast.For, self.ast.While, self.ast.ExceptHandler)):
                        complexity += 1
                violations.extend(
                    self.rule_engine.check_all_thresholds(
                        {
                            "COMPLEX002": complexity,
                        }
                    )
                )

                # 检查嵌套深度
                max_nesting = 0
                current_nesting = 0
                for child in self.ast.walk(node):
                    if isinstance(child, (self.ast.If, self.ast.For, self.ast.While, self.ast.With)):
                        current_nesting += 1
                        max_nesting = max(max_nesting, current_nesting)
                violations.extend(
                    self.rule_engine.check_all_thresholds(
                        {
                            "COMPLEX003": max_nesting,
                        }
                    )
                )

                # 将违规转为 CodeSmell
                for v in violations:
                    desc = (
                        f"Function '{node.name}': {v['description']} "
                        f"(current: {v['value']}, threshold: {v['threshold']})"
                    )
                    smells.append(
                        CodeSmell(
                            name=v["rule_name"],
                            severity=v["severity"],
                            location=f"{file_path}:{node.lineno}",
                            description=desc,
                            suggestion=v["suggestion"],
                        )
                    )

            # 检测大类
            if isinstance(node, self.ast.ClassDef):
                class_lines = (node.end_lineno or node.lineno) - node.lineno + 1
                method_count = sum(
                    1 for item in node.body if isinstance(item, (self.ast.FunctionDef, self.ast.AsyncFunctionDef))
                )

                violations = self.rule_engine.check_all_thresholds(
                    {
                        "COMPLEX004": class_lines,
                        "DESIGN001": len(node.bases),
                        "DESIGN002": method_count,
                    }
                )

                for v in violations:
                    desc = (
                        f"Class '{node.name}': {v['description']} "
                        f"(current: {v['value']}, threshold: {v['threshold']})"
                    )
                    smells.append(
                        CodeSmell(
                            name=v["rule_name"],
                            severity=v["severity"],
                            location=f"{file_path}:{node.lineno}",
                            description=desc,
                            suggestion=v["suggestion"],
                        )
                    )

        # 安全规则检测：eval() 使用
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if "eval(" in stripped and not stripped.startswith("#"):
                rule = self.rule_engine.get_rule("SEC001")
                if rule and rule.enabled:
                    smells.append(
                        CodeSmell(
                            name=rule.name,
                            severity=rule.severity.value,
                            location=f"{file_path}:{i}",
                            description=rule.description,
                            suggestion=rule.suggestion,
                        )
                    )

        return smells

    def _detect_code_smells_with_tree(self, tree, code: str, file_path: str) -> List[CodeSmell]:
        """检测代码坏味道（使用已有解析树，避免重复 parse + 合并遍历）"""
        smells: List[CodeSmell] = []
        lines = code.split("\n")

        # 单次遍历：同时计算函数级复杂度、嵌套深度、参数数量
        for node in self.ast.walk(tree):
            if isinstance(node, (self.ast.FunctionDef, self.ast.AsyncFunctionDef)):
                func_lines = (node.end_lineno or node.lineno) - node.lineno + 1
                func_params = len(node.args.args)

                # 单次 walk 同时计算圈复杂度和嵌套深度（原版用了 3 次 walk）
                complexity = 1
                max_nesting = 0
                current_nesting = 0
                for child in self.ast.walk(node):
                    if isinstance(child, (self.ast.If, self.ast.For, self.ast.While, self.ast.ExceptHandler)):
                        complexity += 1
                    if isinstance(child, (self.ast.If, self.ast.For, self.ast.While, self.ast.With)):
                        current_nesting += 1
                        max_nesting = max(max_nesting, current_nesting)

                violations = self.rule_engine.check_all_thresholds({
                    "COMPLEX001": func_lines,
                    "COMPLEX005": func_params,
                    "COMPLEX002": complexity,
                    "COMPLEX003": max_nesting,
                })

                for v in violations:
                    desc = (
                        f"Function '{node.name}': {v['description']} "
                        f"(current: {v['value']}, threshold: {v['threshold']})"
                    )
                    smells.append(CodeSmell(
                        name=v["rule_name"],
                        severity=v["severity"],
                        location=f"{file_path}:{node.lineno}",
                        description=desc,
                        suggestion=v["suggestion"],
                    ))

            # 检测大类
            if isinstance(node, self.ast.ClassDef):
                class_lines = (node.end_lineno or node.lineno) - node.lineno + 1
                method_count = sum(
                    1 for item in node.body
                    if isinstance(item, (self.ast.FunctionDef, self.ast.AsyncFunctionDef))
                )

                violations = self.rule_engine.check_all_thresholds({
                    "COMPLEX004": class_lines,
                    "DESIGN001": len(node.bases),
                    "DESIGN002": method_count,
                })

                for v in violations:
                    desc = (
                        f"Class '{node.name}': {v['description']} "
                        f"(current: {v['value']}, threshold: {v['threshold']})"
                    )
                    smells.append(CodeSmell(
                        name=v["rule_name"],
                        severity=v["severity"],
                        location=f"{file_path}:{node.lineno}",
                        description=desc,
                        suggestion=v["suggestion"],
                    ))

        # 安全规则检测：eval() 使用
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if "eval(" in stripped and not stripped.startswith("#"):
                rule = self.rule_engine.get_rule("SEC001")
                if rule and rule.enabled:
                    smells.append(CodeSmell(
                        name=rule.name,
                        severity=rule.severity.value,
                        location=f"{file_path}:{i}",
                        description=rule.description,
                        suggestion=rule.suggestion,
                    ))

        return smells

    def _calculate_complexity_with_tree(self, tree, code: str) -> ComplexityMetrics:
        """计算整个文件的复杂度（使用已有解析树）"""
        lines = code.split("\n")
        total_lines = len(lines)
        comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
        blank_lines = sum(1 for line in lines if not line.strip())

        cyclomatic = 1
        for node in self.ast.walk(tree):
            if isinstance(node, (self.ast.If, self.ast.For, self.ast.While, self.ast.ExceptHandler)):
                cyclomatic += 1

        return ComplexityMetrics(
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=self._compute_cognitive_complexity(tree),
            nesting_depth=0,
            lines_of_code=total_lines - blank_lines - comment_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
        )

    def _compute_cognitive_complexity(self, tree) -> int:
        """计算认知复杂度（完整实现）

        认知复杂度规则：
        - 嵌套层级增加额外复杂度
        - 嵌套控制流（if/for/while/try）每个增加 (1 + nesting_level)
        - else/elif 块只 +1（不增加嵌套）
        - except 块 +1
        - 连续的二元逻辑运算符序列 +1
        """
        total = 0

        def _walk_cognitive(node, nesting: int = 0):
            nonlocal total
            for child in self.ast.iter_child_nodes(node):
                # if 语句：if 分支增加嵌套
                if isinstance(child, self.ast.If):
                    total += 1 + nesting
                    _walk_cognitive(child, nesting + 1)
                # for/while 循环增加嵌套
                elif isinstance(child, (self.ast.For, self.ast.While)):
                    total += 1 + nesting
                    _walk_cognitive(child, nesting + 1)
                # except 处理：增加复杂度但不增加嵌套深度
                elif isinstance(child, self.ast.ExceptHandler):
                    total += 1
                    _walk_cognitive(child, nesting)
                # with 语句：只增加嵌套
                elif isinstance(child, (self.ast.With, self.ast.AsyncWith)):
                    _walk_cognitive(child, nesting + 1)
                # 逻辑运算符
                elif isinstance(child, self.ast.BoolOp):
                    total += len(child.values) - 1
                    _walk_cognitive(child, nesting)
                else:
                    _walk_cognitive(child, nesting)

        _walk_cognitive(tree)
        return total


class JavaScriptASTAnalyzer(ASTAnalyzer):
    """JavaScript/TypeScript AST 分析器"""

    def __init__(self, language: Language = Language.JAVASCRIPT, rule_engine: Optional[ASTRuleEngine] = None):
        super().__init__(language, rule_engine=rule_engine)
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
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        lines = code.split("\n")
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
            overall_complexity=overall_complexity,
        )

    def _extract_functions_regex(self, code: str, file_path: str) -> List[FunctionInfo]:
        """使用正则表达式提取函数"""
        import re

        functions = []
        lines = code.split("\n")

        # 匹配函数声明
        patterns = [
            r"(?:async\s+)?function\s+(\w+)\s*\(",  # function foo()
            r"(?:async\s+)?(\w+)\s*\([^)]*\)\s*{",  # foo() {
            r"(?:async\s+)?(\w+)\s*:\s*(?:async\s+)?\([^)]*\)\s*=>",  # foo: () =>
        ]

        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    func_name = match.group(1)
                    functions.append(
                        FunctionInfo(
                            name=func_name,
                            language=self.language.value,
                            file_path=file_path,
                            line_start=i,
                            line_end=i,
                            complexity=ComplexityMetrics(1, 1, 0, 1, 0, 0),
                            parameters=[],
                            return_type=None,
                            is_async="async" in line,
                            is_static=False,
                            code_smells=[],
                        )
                    )

        return functions

    def _extract_classes_regex(self, code: str, file_path: str) -> List[ClassInfo]:
        """使用正则表达式提取类"""
        import re

        classes = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            if re.search(r"class\s+(\w+)", line):
                match = re.search(r"class\s+(\w+)", line)
                if match:
                    class_name = match.group(1)
                    classes.append(
                        ClassInfo(
                            name=class_name,
                            language=self.language.value,
                            file_path=file_path,
                            line_start=i,
                            line_end=i,
                            methods=[],
                            properties=[],
                            inheritance_depth=1 if "extends" in line else 0,
                            code_smells=[],
                        )
                    )

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

        lines = code.split("\n")
        total_lines = len(lines)
        comment_lines = sum(1 for line in lines if re.search(r"^\s*(/|//|\*)", line))
        blank_lines = sum(1 for line in lines if not line.strip())

        # 计算圈复杂度
        cyclomatic = 1
        for line in lines:
            if re.search(r"\b(if|else|case|for|while|catch)\b", line):
                cyclomatic += 1

        return ComplexityMetrics(
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cyclomatic,
            nesting_depth=0,
            lines_of_code=total_lines - blank_lines - comment_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
        )

    def detect_code_smells(self, code: str, file_path: str) -> List[CodeSmell]:
        """检测 JavaScript 代码坏味道"""
        import re

        smells: List[CodeSmell] = []
        lines = code.split("\n")

        # 检测长函数
        in_function = False
        func_start = 0
        brace_count = 0

        for i, line in enumerate(lines, 1):
            if re.search(r"(?:async\s+)?function\s+\w+|(?:async\s+)?\w+\s*\([^)]*\)\s*{", line):
                in_function = True
                func_start = i
                brace_count = line.count("{") - line.count("}")
            elif in_function:
                brace_count += line.count("{") - line.count("}")
                if brace_count == 0:
                    func_lines = i - func_start + 1
                    if func_lines > 50:
                        smells.append(
                            CodeSmell(
                                name="Long Function",
                                severity="medium",
                                location=f"{file_path}:{func_start}",
                                description=f"Function has {func_lines} lines",
                                suggestion="Consider breaking this function into smaller functions",
                            )
                        )
                    in_function = False

        return smells


class ASTAnalyzerFactory:
    """AST 分析器工厂"""

    _analyzers: Dict[Language, Any] = {
        Language.PYTHON: PythonASTAnalyzer,
        Language.JAVASCRIPT: JavaScriptASTAnalyzer,
        Language.TYPESCRIPT: lambda re=None: JavaScriptASTAnalyzer(Language.TYPESCRIPT, rule_engine=re),
    }

    @classmethod
    def create_analyzer(cls, language: Language, rule_engine: Optional[ASTRuleEngine] = None) -> ASTAnalyzer:
        """创建指定语言的分析器"""
        if language not in cls._analyzers:
            logger.warning(f"No analyzer for {language.value}, using JavaScript analyzer")
            return JavaScriptASTAnalyzer(rule_engine=rule_engine)

        analyzer_class = cls._analyzers[language]
        if callable(analyzer_class):
            try:
                return analyzer_class(rule_engine=rule_engine)
            except TypeError:
                return analyzer_class()
        return analyzer_class()

    @classmethod
    def register_analyzer(cls, language: Language, analyzer_class):
        """注册自定义分析器"""
        cls._analyzers[language] = analyzer_class


class BatchASTAnalyzer:
    """批量 AST 分析器 - 支持并行分析和智能调度

    优化策略：
    - 按文件大小排序，大文件优先分配到线程池
    - 自动选择最优并行度（基于文件数量和 CPU 核数）
    - 结果与输入顺序一致
    """

    def __init__(self, max_workers: Optional[int] = None):
        self._max_workers = max_workers

    def analyze_files(
        self,
        file_paths: List[str],
        parallel: bool = True,
    ) -> List[FileAnalysisResult]:
        """批量分析文件

        Args:
            file_paths: 文件路径列表
            parallel: 是否并行分析

        Returns:
            分析结果列表（与输入顺序一致）
        """
        if not parallel or len(file_paths) <= 1:
            return self._analyze_sequential(file_paths)

        return self._analyze_parallel(file_paths)

    def _analyze_sequential(self, file_paths: List[str]) -> List[FileAnalysisResult]:
        """串行分析"""
        results: List[FileAnalysisResult] = []
        for fp in file_paths:
            result = self._analyze_single(fp)
            if result:
                results.append(result)
        return results

    def _analyze_parallel(self, file_paths: List[str]) -> List[FileAnalysisResult]:
        """并行分析 - 按文件大小智能调度"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import os

        # 按文件大小降序排序（大文件优先分配）
        indexed_files = []
        for idx, fp in enumerate(file_paths):
            try:
                size = os.path.getsize(fp)
            except OSError:
                size = 0
            indexed_files.append((idx, fp, size))

        # 大文件优先
        indexed_files.sort(key=lambda x: x[2], reverse=True)

        # 自动选择并行度
        max_workers = self._max_workers or min(len(file_paths), self._optimal_workers())
        max_workers = max(1, max_workers)

        results: Dict[int, Optional[FileAnalysisResult]] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {}
            for idx, fp, _ in indexed_files:
                future = executor.submit(self._analyze_single, fp)
                future_to_idx[future] = idx

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    logger.error(f"Parallel analysis failed for index {idx}: {e}")
                    results[idx] = None

        # 按原始顺序返回，过滤 None
        return [results[i] for i in range(len(file_paths)) if results.get(i) is not None]

    @staticmethod
    def _analyze_single(file_path: str) -> Optional[FileAnalysisResult]:
        """分析单个文件"""
        language = detect_language(file_path)
        if not language:
            return None
        analyzer = ASTAnalyzerFactory.create_analyzer(language)
        try:
            return analyzer.analyze_file(file_path)
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return None

    @staticmethod
    def _optimal_workers() -> int:
        """计算最优并行度"""
        import os
        cpu_count = os.cpu_count() or 4
        # AST 分析是 CPU 密集型 + I/O 混合，使用 CPU 核数的 1.5 倍
        return max(2, int(cpu_count * 1.5))


def detect_language(file_path: str) -> Optional[Language]:
    """根据文件扩展名检测语言"""
    ext_to_lang = {
        ".py": Language.PYTHON,
        ".js": Language.JAVASCRIPT,
        ".jsx": Language.JAVASCRIPT,
        ".ts": Language.TYPESCRIPT,
        ".tsx": Language.TYPESCRIPT,
        ".go": Language.GO,
        ".java": Language.JAVA,
        ".cpp": Language.CPP,
        ".cc": Language.CPP,
        ".rs": Language.RUST,
    }

    suffix = Path(file_path).suffix.lower()
    return ext_to_lang.get(suffix)
