#!/usr/bin/env python3
"""
统一分析器 - 融合 Serena 和 AST 分析
消除重复解析，提供统一的数据模型
"""

import json
import asyncio
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class UnifiedSymbol:
    """统一的符号表示"""
    name: str
    kind: str  # "class", "function", "variable", "import"
    file_path: str
    language: str
    line_start: int
    line_end: int
    
    # 来自 Serena
    serena_data: Optional[Dict[str, Any]] = None
    
    # 来自 AST
    complexity: Optional[Dict[str, Any]] = None
    code_smells: List[Dict[str, Any]] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    is_async: bool = False
    is_static: bool = False
    
    # 派生数据
    quality_score: float = 0.0


@dataclass
class UnifiedFileAnalysis:
    """统一的文件分析结果"""
    file_path: str
    language: str
    total_lines: int
    
    # 符号
    symbols: List[UnifiedSymbol] = field(default_factory=list)
    classes: List[UnifiedSymbol] = field(default_factory=list)
    functions: List[UnifiedSymbol] = field(default_factory=list)
    variables: List[UnifiedSymbol] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    
    # 指标
    overall_complexity: Optional[Dict[str, Any]] = None
    code_smells: List[Dict[str, Any]] = field(default_factory=list)
    
    # 元数据
    serena_metadata: Dict[str, Any] = field(default_factory=dict)
    ast_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedProjectAnalysis:
    """统一的项目分析"""
    project_path: str
    generated_at: str
    
    # 文件
    files: List[UnifiedFileAnalysis] = field(default_factory=list)
    
    # 摘要
    language_stats: Dict[str, int] = field(default_factory=dict)
    total_complexity: float = 0.0
    total_code_smells: int = 0
    quality_score: float = 0.0
    
    # 原始数据（用于参考）
    serena_report: Dict[str, Any] = field(default_factory=dict)
    ast_report: Dict[str, Any] = field(default_factory=dict)


class UnifiedAnalyzer:
    """统一分析器 - 融合 Serena 和 AST 分析"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
    
    async def analyze_project(
        self,
        serena_report: Dict[str, Any],
        ast_report: Dict[str, Any]
    ) -> UnifiedProjectAnalysis:
        """
        融合 Serena 和 AST 分析结果
        
        Args:
            serena_report: Serena 分析报告
            ast_report: AST 分析报告
        
        Returns:
            统一的项目分析结果
        """
        logger.info("开始融合 Serena 和 AST 分析结果...")
        
        # 创建统一分析结果
        unified = UnifiedProjectAnalysis(
            project_path=str(self.project_path),
            generated_at=datetime.now().isoformat(),
            serena_report=serena_report,
            ast_report=ast_report
        )
        
        # 构建 AST 数据索引（按文件路径）
        ast_by_file = self._build_ast_index(ast_report)
        
        # 处理每个文件
        for file_analysis in ast_report.get("files", []):
            file_path = file_analysis.get("file_path", "")
            
            # 融合该文件的数据
            unified_file = self._merge_file_data(
                file_analysis,
                serena_report
            )
            
            if unified_file:
                unified.files.append(unified_file)
        
        # 计算摘要统计
        self._calculate_summary(unified)
        
        logger.info(f"✅ 融合完成: {len(unified.files)} 个文件")
        
        return unified
    
    def _build_ast_index(self, ast_report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """构建 AST 数据索引"""
        index = {}
        for file_analysis in ast_report.get("files", []):
            file_path = file_analysis.get("file_path", "")
            index[file_path] = file_analysis
        return index
    
    def _merge_file_data(
        self,
        ast_file: Dict[str, Any],
        serena_report: Dict[str, Any]
    ) -> Optional[UnifiedFileAnalysis]:
        """融合单个文件的数据"""
        file_path = ast_file.get("file_path", "")
        language = ast_file.get("language", "unknown")
        total_lines = ast_file.get("total_lines", 0)
        
        # 创建统一文件分析
        unified_file = UnifiedFileAnalysis(
            file_path=file_path,
            language=language,
            total_lines=total_lines
        )
        
        # 处理函数
        for func in ast_file.get("functions", []):
            symbol = UnifiedSymbol(
                name=func.get("name", "unknown"),
                kind="function",
                file_path=file_path,
                language=language,
                line_start=func.get("line_start", 0),
                line_end=func.get("line_end", 0),
                complexity=func.get("complexity"),
                code_smells=func.get("code_smells", []),
                parameters=func.get("parameters", []),
                return_type=func.get("return_type"),
                is_async=func.get("is_async", False),
                is_static=func.get("is_static", False)
            )
            
            # 计算质量分数
            symbol.quality_score = self._calculate_quality_score(symbol)
            
            unified_file.functions.append(symbol)
            unified_file.symbols.append(symbol)
        
        # 处理类
        for cls in ast_file.get("classes", []):
            symbol = UnifiedSymbol(
                name=cls.get("name", "unknown"),
                kind="class",
                file_path=file_path,
                language=language,
                line_start=cls.get("line_start", 0),
                line_end=cls.get("line_end", 0),
                code_smells=cls.get("code_smells", [])
            )
            
            # 计算质量分数
            symbol.quality_score = self._calculate_quality_score(symbol)
            
            unified_file.classes.append(symbol)
            unified_file.symbols.append(symbol)
        
        # 处理导入
        unified_file.imports = ast_file.get("imports", [])
        
        # 处理代码坏味道
        unified_file.code_smells = ast_file.get("code_smells", [])
        
        # 处理复杂度
        unified_file.overall_complexity = ast_file.get("overall_complexity")
        
        # 存储元数据
        unified_file.ast_metadata = {
            "total_functions": len(unified_file.functions),
            "total_classes": len(unified_file.classes),
            "total_code_smells": len(unified_file.code_smells)
        }
        
        return unified_file
    
    def _calculate_quality_score(self, symbol: UnifiedSymbol) -> float:
        """计算符号的质量分数 (0-100)"""
        score = 100.0
        
        # 根据复杂度降分
        if symbol.complexity:
            cc = symbol.complexity.get("cyclomatic_complexity", 0)
            if cc > 10:
                score -= min(20, (cc - 10) * 2)
            elif cc > 5:
                score -= (cc - 5) * 2
        
        # 根据代码坏味道降分
        for smell in symbol.code_smells:
            severity = smell.get("severity", "low")
            if severity == "critical":
                score -= 20
            elif severity == "high":
                score -= 15
            elif severity == "medium":
                score -= 10
            elif severity == "low":
                score -= 5
        
        return max(0, min(100, score))
    
    def _calculate_summary(self, unified: UnifiedProjectAnalysis) -> None:
        """计算摘要统计"""
        # 语言统计
        language_counts = {}
        total_complexity = 0.0
        total_smells = 0
        total_quality = 0.0
        
        for file_analysis in unified.files:
            language = file_analysis.language
            language_counts[language] = language_counts.get(language, 0) + 1
            
            # 累计复杂度
            if file_analysis.overall_complexity:
                cc = file_analysis.overall_complexity.get("cyclomatic_complexity", 0)
                total_complexity += cc
            
            # 累计代码坏味道
            total_smells += len(file_analysis.code_smells)
            
            # 累计质量分数
            for symbol in file_analysis.symbols:
                total_quality += symbol.quality_score
        
        unified.language_stats = language_counts
        unified.total_complexity = total_complexity
        unified.total_code_smells = total_smells
        
        # 计算平均质量分数
        total_symbols = sum(len(f.symbols) for f in unified.files)
        if total_symbols > 0:
            unified.quality_score = total_quality / total_symbols
        else:
            unified.quality_score = 100.0
    
    def to_dict(self, unified: UnifiedProjectAnalysis) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "project_path": unified.project_path,
            "generated_at": unified.generated_at,
            "files": [
                {
                    "file_path": f.file_path,
                    "language": f.language,
                    "total_lines": f.total_lines,
                    "symbols": [asdict(s) for s in f.symbols],
                    "classes": [asdict(c) for c in f.classes],
                    "functions": [asdict(fn) for fn in f.functions],
                    "imports": f.imports,
                    "code_smells": f.code_smells,
                    "overall_complexity": f.overall_complexity,
                    "ast_metadata": f.ast_metadata
                }
                for f in unified.files
            ],
            "summary": {
                "language_stats": unified.language_stats,
                "total_complexity": unified.total_complexity,
                "total_code_smells": unified.total_code_smells,
                "quality_score": unified.quality_score
            }
        }
    
    def to_json(self, unified: UnifiedProjectAnalysis) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(unified), ensure_ascii=False, indent=2)


async def merge_analyses(
    serena_report_path: str,
    ast_report_path: str,
    project_path: str
) -> UnifiedProjectAnalysis:
    """
    融合 Serena 和 AST 分析结果
    
    Args:
        serena_report_path: Serena 报告路径
        ast_report_path: AST 报告路径
        project_path: 项目路径
    
    Returns:
        统一的项目分析结果
    """
    # 加载报告
    with open(serena_report_path, 'r', encoding='utf-8') as f:
        serena_report = json.load(f)
    
    with open(ast_report_path, 'r', encoding='utf-8') as f:
        ast_report = json.load(f)
    
    # 创建分析器
    analyzer = UnifiedAnalyzer(project_path)
    
    # 融合分析
    unified = await analyzer.analyze_project(serena_report, ast_report)
    
    return unified
