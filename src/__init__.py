"""
AI Project Analyzer Package

一套基于 MCP (Model Context Protocol) 和 AI 的代码分析工具。
支持多级缓存、AST 规则引擎、缓存预热、AST 可视化等高级功能。
"""

__version__ = "0.3.0"
__author__ = "AI-Analyze Team"

__all__ = [
    "ASTAnalyzerFactory",
    "detect_language",
    "SecurityScanner",
    "QualityScorer",
    "QualityMetrics",
    "DependencyAnalyzer",
    "SimilarityDetector",
    "CodeBlock",
    "MultiLevelCache",
    "ConfigManager",
    "UnifiedLogger",
]

from .ast_analyzer import ASTAnalyzerFactory, detect_language
from .security_scanner import SecurityScanner
from .quality_score import QualityScorer, QualityMetrics
from .dependency_graph import DependencyAnalyzer
from .similarity import SimilarityDetector, CodeBlock
from .multi_level_cache import MultiLevelCache
from .config import ConfigManager
from .logger import UnifiedLogger
