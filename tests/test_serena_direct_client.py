#!/usr/bin/env python3
"""
SerenaClient (src/serena_client.py) Mock 单元测试
SerenaClient 现在通过 MCP 协议通信，不再直接 import serena
"""

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.serena_client import SerenaClient, _check_serena_available


# ==================== _check_serena_available 测试 ====================


class TestCheckSerenaAvailable:
    """_check_serena_available 测试"""

    def test_no_serena_dir(self):
        """SERENA_DIR 未设置时抛出 ImportError"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SERENA_DIR", None)
            with pytest.raises(ImportError, match="serena 未安装"):
                _check_serena_available()

    def test_invalid_serena_dir(self):
        """SERENA_DIR 指向不存在的路径时抛出 ImportError"""
        with patch.dict(os.environ, {"SERENA_DIR": "/nonexistent"}):
            with pytest.raises(ImportError, match="serena 未安装"):
                _check_serena_available()

    def test_valid_serena_dir(self, tmp_path):
        """SERENA_DIR 指向有效路径时不抛出异常"""
        with patch.dict(os.environ, {"SERENA_DIR": str(tmp_path)}):
            _check_serena_available()  # 不应抛出异常


# ==================== SerenaClient 初始化测试 ====================


class TestSerenaClientInit:
    """SerenaClient 初始化测试"""

    def test_init_without_serena_dir_raises(self):
        """SERENA_DIR 未设置时初始化抛出 ImportError"""
        with patch("src.serena_client._check_serena_available", side_effect=ImportError("serena 未安装")):
            with pytest.raises(ImportError, match="serena 未安装"):
                SerenaClient(project_path="/test")

    def test_init_with_valid_serena_dir(self):
        """有效 SERENA_DIR 时初始化成功"""
        with patch("src.serena_client._check_serena_available"):
            client = SerenaClient(project_path="/test")
            assert client.project_path == "/test"

    def test_init_default_project_path(self):
        """测试默认项目路径"""
        with patch("src.serena_client._check_serena_available"):
            with patch.object(Path, "cwd", return_value=Path("/my/project")):
                client = SerenaClient()
                assert client.project_path == "/my/project"


# ==================== SerenaClient MCP 协议测试 ====================


class TestSerenaClientMCPProtocol:
    """SerenaClient 通过 MCP 协议通信的测试"""

    @pytest.fixture
    def client(self):
        """创建测试用客户端"""
        with patch("src.serena_client._check_serena_available"):
            return SerenaClient(project_path="/test")

    def test_find_symbol(self, client):
        """测试符号查找"""
        mock_result = {"name": "MyClass", "kind": 5}

        with patch.object(client, "_run_async", return_value=mock_result):
            result = client.find_symbol("MyClass")
            assert result == mock_result

    def test_find_symbol_with_options(self, client):
        """测试带选项的符号查找"""
        mock_result = {"name": "MyClass", "kind": 5}

        with patch.object(client, "_run_async", return_value=mock_result):
            result = client.find_symbol(
                "MyClass",
                relative_path="src/main.py",
                depth=2,
                include_body=True,
            )
            assert result == mock_result

    def test_find_referencing_symbols(self, client):
        """测试引用查找"""
        mock_result = [{"name": "ref1"}, {"name": "ref2"}]

        with patch.object(client, "_run_async", return_value=mock_result):
            result = client.find_referencing_symbols("MyClass", "src/main.py")
            assert len(result) == 2

    def test_get_symbols_overview(self, client):
        """测试符号概览"""
        mock_result = {"symbols": [{"name": "MyClass"}]}

        with patch.object(client, "_run_async", return_value=mock_result):
            result = client.get_symbols_overview("src/main.py")
            assert "symbols" in result

    def test_search_for_pattern(self, client):
        """测试模式搜索"""
        mock_result = {"test.py": [["line 1"]]}

        with patch.object(client, "_run_async", return_value=mock_result):
            result = client.search_for_pattern(r"def\s+\w+")
            assert "test.py" in result

    def test_find_file(self, client):
        """测试文件查找"""
        mock_result = {"files": ["main.py", "utils.py"]}

        with patch.object(client, "_run_async", return_value=mock_result):
            result = client.find_file("*.py")
            assert "files" in result

    def test_rename_symbol_not_implemented(self, client):
        """测试重命名符号抛出 NotImplementedError"""
        with pytest.raises(NotImplementedError, match="rename_symbol"):
            client.rename_symbol("old_name", "new_name", "src/main.py")

    def test_replace_symbol_body_not_implemented(self, client):
        """测试替换符号体抛出 NotImplementedError"""
        with pytest.raises(NotImplementedError, match="replace_symbol_body"):
            client.replace_symbol_body("MyClass.method", "pass", "src/main.py")


# ==================== SerenaClient _run_async 测试 ====================


class TestSerenaClientRunAsync:
    """SerenaClient._run_async 测试"""

    @pytest.fixture
    def client(self):
        with patch("src.serena_client._check_serena_available"):
            return SerenaClient(project_path="/test")

    def test_run_async_in_sync_context(self, client):
        """在同步上下文中运行异步函数"""
        async def mock_coro():
            return 42

        result = client._run_async(mock_coro())
        assert result == 42

    def test_run_async_with_exception(self, client):
        """异步函数抛出异常时正确传播"""
        async def mock_coro():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            client._run_async(mock_coro())
