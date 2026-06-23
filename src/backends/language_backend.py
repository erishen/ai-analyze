#!/usr/bin/env python3
"""
Language Backend 系统
提供统一的代码分析后端接口，支持多种实现：
- TreeSitterBackend: 基于 tree-sitter，零外部依赖（默认）
- SerenaBackend: 通过 MCP 协议调用 serena，增强语义分析
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from ..analyzers.ast_analyzer import (
    ASTAnalyzerFactory,
    FileAnalysisResult,
    Language,
    detect_language,
)

logger = logging.getLogger(__name__)


class LanguageBackend(ABC):
    """语言后端抽象基类"""

    name: str = "base"

    @abstractmethod
    def analyze_file(self, file_path: str) -> FileAnalysisResult:
        """分析单个文件"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查后端是否可用"""
        pass

    @abstractmethod
    def supported_languages(self) -> list[Language]:
        """支持的语言列表"""
        pass

    def analyze_project(self, project_path: str, max_files: int = 500) -> list[FileAnalysisResult]:
        """分析项目中的所有文件"""
        results: list[FileAnalysisResult] = []
        supported_ext = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java",
            ".cpp", ".cc", ".c", ".h", ".rs", ".rb", ".php",
        }
        skip_dirs = {
            ".git", "node_modules", "__pycache__", ".venv", "venv",
            ".mypy_cache", ".ruff_cache", ".tox", "dist", "build",
            ".eggs", "*.egg-info",
        }

        for root, dirs, filenames in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for filename in filenames:
                ext = os.path.splitext(filename)[1]
                if ext not in supported_ext:
                    continue
                filepath = os.path.join(root, filename)
                try:
                    result = self.analyze_file(filepath)
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to analyze {filepath}: {e}")
                if len(results) >= max_files:
                    return results

        return results


class TreeSitterBackend(LanguageBackend):
    """Tree-sitter 后端 — 基于 tree-sitter 和 Python ast 模块

    零外部依赖（tree-sitter 已在 dependencies 中）。
    Python 使用 ast 模块（更精确），其他语言使用 tree-sitter。
    """

    name = "treesitter"

    def is_available(self) -> bool:
        """tree-sitter 是默认依赖，始终可用"""
        return True

    def supported_languages(self) -> list[Language]:
        return list(Language)

    def analyze_file(self, file_path: str) -> FileAnalysisResult:
        """分析单个文件"""
        language = detect_language(file_path)
        if not language:
            raise ValueError(f"Unsupported file type: {file_path}")

        analyzer = ASTAnalyzerFactory.create_analyzer(language)
        return analyzer.analyze_file(file_path)


class SerenaBackend(LanguageBackend):
    """Serena 后端 — 通过 MCP 协议调用 serena

    需要配置 SERENA_DIR 环境变量。
    提供增强的语义分析能力（符号查找、引用分析、重命名等）。
    """

    name = "serena"

    def __init__(self, project_path: str):
        self.project_path = project_path
        self._fallback = TreeSitterBackend()

    def is_available(self) -> bool:
        """检查 serena 是否配置且可用"""
        serena_dir = os.getenv("SERENA_DIR", "")
        if not serena_dir:
            return False
        return Path(serena_dir).exists()

    def supported_languages(self) -> list[Language]:
        """Serena 支持 40+ 语言，返回所有已知语言"""
        return list(Language)

    def analyze_file(self, file_path: str) -> FileAnalysisResult:
        """分析单个文件

        使用 tree-sitter 后端进行基础分析，
        Serena 增强的语义分析通过独立的导航接口提供。
        """
        return self._fallback.analyze_file(file_path)

    async def find_symbol(
        self,
        name_pattern: str,
        relative_path: Optional[str] = None,
        depth: int = 0,
        include_body: bool = False,
    ) -> dict[str, Any]:
        """查找符号（类、方法、函数等）"""
        from .serena_stdio_client import SerenaStdioClient

        async with SerenaStdioClient(project_path=self.project_path) as client:
            return await client.find_symbol(
                name_pattern,
                relative_path=relative_path,
                depth=depth,
                include_body=include_body,
            )

    async def find_references(
        self,
        name_path: str,
        relative_path: str,
    ) -> list[dict[str, Any]]:
        """查找引用特定符号的代码"""
        from .serena_stdio_client import SerenaStdioClient

        async with SerenaStdioClient(project_path=self.project_path) as client:
            return await client.find_referencing_symbols(name_path, relative_path)

    async def get_symbols_overview(
        self,
        relative_path: str,
        depth: int = 0,
    ) -> dict[str, Any]:
        """获取文件的符号概览"""
        from .serena_stdio_client import SerenaStdioClient

        async with SerenaStdioClient(project_path=self.project_path) as client:
            return await client.get_symbols_overview(relative_path, depth=depth)

    async def search_pattern(
        self,
        pattern: str,
        relative_path: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """搜索代码模式"""
        from .serena_stdio_client import SerenaStdioClient

        async with SerenaStdioClient(project_path=self.project_path) as client:
            return await client.search_for_pattern(pattern, relative_path=relative_path, **kwargs)


class BackendFactory:
    """后端工厂 — 根据配置创建合适的 LanguageBackend"""

    @staticmethod
    def create(project_path: Optional[str] = None, backend_name: Optional[str] = None) -> LanguageBackend:
        """创建语言后端

        Args:
            project_path: 项目路径（Serena 后端需要）
            backend_name: 指定后端名称，None 则自动选择

        Returns:
            LanguageBackend 实例
        """
        if backend_name == "serena":
            if not project_path:
                raise ValueError("SerenaBackend requires project_path")
            backend = SerenaBackend(project_path)
            if backend.is_available():
                logger.info("Using Serena backend (MCP protocol)")
                return backend
            logger.warning("Serena backend requested but not available, falling back to TreeSitter")

        if backend_name == "treesitter":
            return TreeSitterBackend()

        # 自动选择：优先 Serena，回退 TreeSitter
        if project_path:
            serena = SerenaBackend(project_path)
            if serena.is_available():
                logger.info("Auto-selected Serena backend")
                return serena

        logger.info("Using TreeSitter backend (default)")
        return TreeSitterBackend()

    @staticmethod
    def available_backends() -> list[str]:
        """列出可用的后端"""
        backends = ["treesitter"]
        serena_dir = os.getenv("SERENA_DIR", "")
        if serena_dir and Path(serena_dir).exists():
            backends.append("serena")
        return backends
