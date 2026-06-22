#!/usr/bin/env python3
"""
LanguageBackend 系统测试
"""

import pytest
from pathlib import Path

from src.language_backend import (
    LanguageBackend,
    TreeSitterBackend,
    SerenaBackend,
    BackendFactory,
)
from src.ast_analyzer import Language


class TestTreeSitterBackend:
    """TreeSitterBackend 测试"""

    def test_name(self):
        backend = TreeSitterBackend()
        assert backend.name == "treesitter"

    def test_is_available(self):
        backend = TreeSitterBackend()
        assert backend.is_available() is True

    def test_supported_languages(self):
        backend = TreeSitterBackend()
        langs = backend.supported_languages()
        assert Language.PYTHON in langs
        assert Language.JAVASCRIPT in langs
        assert Language.TYPESCRIPT in langs

    def test_analyze_file_python(self, tmp_path):
        backend = TreeSitterBackend()
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    print('hello')\n")

        result = backend.analyze_file(str(py_file))
        assert result.file_path == str(py_file)
        assert result.language == "python"
        assert len(result.functions) >= 1

    def test_analyze_file_unsupported(self, tmp_path):
        backend = TreeSitterBackend()
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("hello world")

        with pytest.raises(ValueError, match="Unsupported file type"):
            backend.analyze_file(str(txt_file))

    def test_analyze_project(self, tmp_path):
        backend = TreeSitterBackend()

        # 创建测试项目
        (tmp_path / "main.py").write_text("def main():\n    pass\n")
        (tmp_path / "utils.js").write_text("function foo() {}\n")
        (tmp_path / "readme.md").write_text("# Test")

        results = backend.analyze_project(str(tmp_path))
        # 应该只分析 .py 和 .js 文件
        assert len(results) == 2
        languages = {r.language for r in results}
        assert "python" in languages
        assert "javascript" in languages


class TestSerenaBackend:
    """SerenaBackend 测试"""

    def test_name(self):
        backend = SerenaBackend("/tmp/test")
        assert backend.name == "serena"

    def test_is_available_no_env(self):
        """SERENA_DIR 未设置时不可用"""
        import os
        original = os.environ.get("SERENA_DIR")
        try:
            os.environ.pop("SERENA_DIR", None)
            backend = SerenaBackend("/tmp/test")
            assert backend.is_available() is False
        finally:
            if original is not None:
                os.environ["SERENA_DIR"] = original

    def test_is_available_with_env(self):
        """SERENA_DIR 指向不存在的路径时不可用"""
        import os
        original = os.environ.get("SERENA_DIR")
        try:
            os.environ["SERENA_DIR"] = "/nonexistent/path"
            backend = SerenaBackend("/tmp/test")
            assert backend.is_available() is False
        finally:
            if original is not None:
                os.environ["SERENA_DIR"] = original
            else:
                os.environ.pop("SERENA_DIR", None)

    def test_analyze_file_falls_back_to_treesitter(self, tmp_path):
        """SerenaBackend.analyze_file 回退到 TreeSitterBackend"""
        backend = SerenaBackend(str(tmp_path))
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    pass\n")

        result = backend.analyze_file(str(py_file))
        assert result.file_path == str(py_file)
        assert result.language == "python"

    def test_supported_languages(self):
        backend = SerenaBackend("/tmp/test")
        langs = backend.supported_languages()
        assert len(langs) > 0


class TestBackendFactory:
    """BackendFactory 测试"""

    def test_create_default(self):
        backend = BackendFactory.create()
        assert isinstance(backend, TreeSitterBackend)

    def test_create_treesitter(self):
        backend = BackendFactory.create(backend_name="treesitter")
        assert isinstance(backend, TreeSitterBackend)

    def test_create_serena_fallback(self):
        """Serena 不可用时回退到 TreeSitter"""
        import os
        original = os.environ.get("SERENA_DIR")
        try:
            os.environ.pop("SERENA_DIR", None)
            backend = BackendFactory.create(project_path="/tmp/test", backend_name="serena")
            assert isinstance(backend, TreeSitterBackend)
        finally:
            if original is not None:
                os.environ["SERENA_DIR"] = original

    def test_create_serena_without_project_raises(self):
        with pytest.raises(ValueError, match="SerenaBackend requires project_path"):
            BackendFactory.create(backend_name="serena")

    def test_available_backends(self):
        backends = BackendFactory.available_backends()
        assert "treesitter" in backends

    def test_auto_select_without_serena(self):
        import os
        original = os.environ.get("SERENA_DIR")
        try:
            os.environ.pop("SERENA_DIR", None)
            backend = BackendFactory.create(project_path="/tmp/test")
            assert isinstance(backend, TreeSitterBackend)
        finally:
            if original is not None:
                os.environ["SERENA_DIR"] = original
