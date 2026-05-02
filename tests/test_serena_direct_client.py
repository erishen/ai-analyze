#!/usr/bin/env python3
"""
SerenaClient (src/serena_client.py) Mock 单元测试
使用 unittest.mock 替代真实 serena 包导入
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Mock serena 模块在 import 之前
mock_serena_agent = MagicMock()
mock_serena_tools = MagicMock()

# 创建 mock tool 类
mock_tool_classes = {
    "FindSymbolTool": MagicMock(),
    "FindFileTool": MagicMock(),
    "FindReferencingSymbolsTool": MagicMock(),
    "GetSymbolsOverviewTool": MagicMock(),
    "RenameSymbolTool": MagicMock(),
    "ReplaceSymbolBodyTool": MagicMock(),
    "SearchForPatternTool": MagicMock(),
    "Tool": MagicMock(),
}

# 设置 serena.agent 模块
sys.modules["serena"] = MagicMock()
sys.modules["serena.agent"] = MagicMock()
sys.modules["serena.agent"].SerenaAgent = mock_serena_agent

# 设置 serena.tools 模块
sys.modules["serena.tools"] = mock_serena_tools
for name, cls in mock_tool_classes.items():
    setattr(mock_serena_tools, name, cls)

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.serena_client import SerenaClient  # noqa: E402


# ==================== SerenaClient 初始化测试 ====================


class TestSerenaClientInit:
    """SerenaClient 初始化测试"""

    def test_init_default_project_path(self):
        """测试默认项目路径（当前工作目录）"""
        with patch.object(Path, "cwd", return_value=Path("/my/project")):
            client = SerenaClient()
            assert client.project_path == "/my/project"
            mock_serena_agent.assert_called_once_with(project="/my/project")

    def test_init_custom_project_path(self):
        """测试自定义项目路径"""
        client = SerenaClient(project_path="/custom/project")
        assert client.project_path == "/custom/project"

    def test_init_creates_agent(self):
        """测试初始化创建 SerenaAgent"""
        mock_serena_agent.reset_mock()
        client = SerenaClient(project_path="/test/project")
        mock_serena_agent.assert_called_with(project="/test/project")
        assert client.agent is not None


# ==================== SerenaClient get_tool 测试 ====================


class TestSerenaClientGetTool:
    """SerenaClient get_tool 测试"""

    def test_get_tool_calls_agent_get_tool(self):
        """测试 get_tool 调用 agent.get_tool"""
        client = SerenaClient(project_path="/test")
        mock_tool_instance = MagicMock()
        client.agent.get_tool = MagicMock(return_value=mock_tool_instance)

        result = client.get_tool(mock_tool_classes["FindSymbolTool"])
        client.agent.get_tool.assert_called_once_with(mock_tool_classes["FindSymbolTool"])
        assert result is mock_tool_instance


# ==================== SerenaClient find_symbol 测试 ====================


class TestSerenaClientFindSymbol:
    """SerenaClient find_symbol 测试"""

    def setup_method(self):
        self.client = SerenaClient(project_path="/test")
        self.mock_tool = MagicMock()
        self.client.agent.get_tool = MagicMock(return_value=self.mock_tool)
        # execute_task 调用传入的 lambda 函数并返回结果
        self.client.agent.execute_task = MagicMock(
            side_effect=lambda fn: fn()
        )
        self.mock_tool.apply = MagicMock(
            return_value=json.dumps({"name": "MyClass", "kind": 5})
        )

    def test_find_symbol_basic(self):
        """测试基本符号查找"""
        result = self.client.find_symbol("MyClass")
        assert result == {"name": "MyClass", "kind": 5}
        self.client.agent.get_tool.assert_called_once_with(
            mock_tool_classes["FindSymbolTool"]
        )

    def test_find_symbol_with_relative_path(self):
        """测试带相对路径的符号查找"""
        self.client.find_symbol("MyClass", relative_path="src/main.py")
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["name_path_pattern"] == "MyClass"
        assert call_args[1]["relative_path"] == "src/main.py"

    def test_find_symbol_with_depth(self):
        """测试带深度的符号查找"""
        self.client.find_symbol("MyClass", depth=2)
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["depth"] == 2

    def test_find_symbol_with_include_body(self):
        """测试包含符号体的查找"""
        self.client.find_symbol("MyClass", include_body=True)
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["include_body"] is True

    def test_find_symbol_without_optional_args(self):
        """测试不带可选参数的查找"""
        self.client.find_symbol("MyClass")
        call_args = self.mock_tool.apply.call_args
        assert "relative_path" not in call_args[1]
        assert "depth" not in call_args[1]
        assert "include_body" not in call_args[1]

    def test_find_symbol_zero_depth_excluded(self):
        """测试 depth=0 时不传递 depth 参数"""
        self.client.find_symbol("MyClass", depth=0)
        call_args = self.mock_tool.apply.call_args
        assert "depth" not in call_args[1]


# ==================== SerenaClient find_referencing_symbols 测试 ====================


class TestSerenaClientFindReferences:
    """SerenaClient find_referencing_symbols 测试"""

    def setup_method(self):
        self.client = SerenaClient(project_path="/test")
        self.mock_tool = MagicMock()
        self.client.agent.get_tool = MagicMock(return_value=self.mock_tool)
        self.client.agent.execute_task = MagicMock(side_effect=lambda fn: fn())
        self.mock_tool.apply = MagicMock(
            return_value=json.dumps([{"name": "ref1"}, {"name": "ref2"}])
        )

    def test_find_references_basic(self):
        """测试基本引用查找"""
        result = self.client.find_referencing_symbols("MyClass", "src/main.py")
        assert len(result) == 2
        self.client.agent.get_tool.assert_called_once_with(
            mock_tool_classes["FindReferencingSymbolsTool"]
        )

    def test_find_references_with_include_kinds(self):
        """测试带 include_kinds 的引用查找"""
        self.client.find_referencing_symbols(
            "MyClass", "src/main.py", include_kinds=[5, 12]
        )
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["include_kinds"] == [5, 12]

    def test_find_references_with_exclude_kinds(self):
        """测试带 exclude_kinds 的引用查找"""
        self.client.find_referencing_symbols(
            "MyClass", "src/main.py", exclude_kinds=[3]
        )
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["exclude_kinds"] == [3]

    def test_find_references_without_optional_args(self):
        """测试不带可选参数的引用查找"""
        self.client.find_referencing_symbols("MyClass", "src/main.py")
        call_args = self.mock_tool.apply.call_args
        assert "include_kinds" not in call_args[1]
        assert "exclude_kinds" not in call_args[1]


# ==================== SerenaClient get_symbols_overview 测试 ====================


class TestSerenaClientSymbolsOverview:
    """SerenaClient get_symbols_overview 测试"""

    def setup_method(self):
        self.client = SerenaClient(project_path="/test")
        self.mock_tool = MagicMock()
        self.client.agent.get_tool = MagicMock(return_value=self.mock_tool)
        self.client.agent.execute_task = MagicMock(side_effect=lambda fn: fn())
        self.mock_tool.apply = MagicMock(
            return_value=json.dumps({"symbols": [{"name": "MyClass"}]})
        )

    def test_symbols_overview_basic(self):
        """测试基本符号概览"""
        result = self.client.get_symbols_overview("src/main.py")
        assert "symbols" in result
        self.client.agent.get_tool.assert_called_once_with(
            mock_tool_classes["GetSymbolsOverviewTool"]
        )

    def test_symbols_overview_with_depth(self):
        """测试带深度的符号概览"""
        self.client.get_symbols_overview("src/main.py", depth=1)
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["depth"] == 1

    def test_symbols_overview_zero_depth_excluded(self):
        """测试 depth=0 时不传递 depth 参数"""
        self.client.get_symbols_overview("src/main.py", depth=0)
        call_args = self.mock_tool.apply.call_args
        assert "depth" not in call_args[1]


# ==================== SerenaClient search_for_pattern 测试 ====================


class TestSerenaClientSearchPattern:
    """SerenaClient search_for_pattern 测试"""

    def setup_method(self):
        self.client = SerenaClient(project_path="/test")
        self.mock_tool = MagicMock()
        self.client.agent.get_tool = MagicMock(return_value=self.mock_tool)
        self.client.agent.execute_task = MagicMock(side_effect=lambda fn: fn())
        self.mock_tool.apply = MagicMock(
            return_value=json.dumps({"test.py": [["line 1"]]})
        )

    def test_search_pattern_basic(self):
        """测试基本模式搜索"""
        result = self.client.search_for_pattern(r"def\s+\w+")
        assert "test.py" in result
        self.client.agent.get_tool.assert_called_once_with(
            mock_tool_classes["SearchForPatternTool"]
        )

    def test_search_pattern_with_relative_path(self):
        """测试带相对路径的搜索"""
        self.client.search_for_pattern("pattern", relative_path="src/")
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["relative_path"] == "src/"

    def test_search_pattern_with_include_glob(self):
        """测试带 include glob 的搜索"""
        self.client.search_for_pattern("pattern", paths_include_glob="*.py")
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["paths_include_glob"] == "*.py"

    def test_search_pattern_with_exclude_glob(self):
        """测试带 exclude glob 的搜索"""
        self.client.search_for_pattern("pattern", paths_exclude_glob="*.test.py")
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["paths_exclude_glob"] == "*.test.py"

    def test_search_pattern_with_context_lines(self):
        """测试带上下文行的搜索"""
        self.client.search_for_pattern(
            "pattern", context_lines_before=2, context_lines_after=3
        )
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["context_lines_before"] == 2
        assert call_args[1]["context_lines_after"] == 3

    def test_search_pattern_with_code_only(self):
        """测试仅搜索代码文件"""
        self.client.search_for_pattern("pattern", restrict_search_to_code_files=True)
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["restrict_search_to_code_files"] is True

    def test_search_pattern_zero_context_excluded(self):
        """测试 context_lines=0 时不传递参数"""
        self.client.search_for_pattern("pattern")
        call_args = self.mock_tool.apply.call_args
        assert "context_lines_before" not in call_args[1]
        assert "context_lines_after" not in call_args[1]

    def test_search_pattern_none_optionals_excluded(self):
        """测试 None 可选参数不传递"""
        self.client.search_for_pattern("pattern")
        call_args = self.mock_tool.apply.call_args
        assert "relative_path" not in call_args[1]
        assert "paths_include_glob" not in call_args[1]
        assert "paths_exclude_glob" not in call_args[1]
        assert "restrict_search_to_code_files" not in call_args[1]


# ==================== SerenaClient find_file 测试 ====================


class TestSerenaClientFindFile:
    """SerenaClient find_file 测试"""

    def setup_method(self):
        self.client = SerenaClient(project_path="/test")
        self.mock_tool = MagicMock()
        self.client.agent.get_tool = MagicMock(return_value=self.mock_tool)
        self.client.agent.execute_task = MagicMock(side_effect=lambda fn: fn())
        self.mock_tool.apply = MagicMock(
            return_value=json.dumps({"files": ["main.py", "utils.py"]})
        )

    def test_find_file_basic(self):
        """测试基本文件查找"""
        result = self.client.find_file("*.py")
        assert "files" in result
        self.client.agent.get_tool.assert_called_once_with(
            mock_tool_classes["FindFileTool"]
        )

    def test_find_file_with_relative_path(self):
        """测试带相对路径的文件查找"""
        self.client.find_file("*.py", relative_path="src/")
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["file_mask"] == "*.py"
        assert call_args[1]["relative_path"] == "src/"

    def test_find_file_default_relative_path(self):
        """测试默认相对路径为 ."""
        self.client.find_file("main.py")
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["relative_path"] == "."


# ==================== SerenaClient rename_symbol 测试 ====================


class TestSerenaClientRenameSymbol:
    """SerenaClient rename_symbol 测试"""

    def setup_method(self):
        self.client = SerenaClient(project_path="/test")
        self.mock_tool = MagicMock()
        self.client.agent.get_tool = MagicMock(return_value=self.mock_tool)
        self.client.agent.execute_task = MagicMock(side_effect=lambda fn: fn())
        self.mock_tool.apply = MagicMock(
            return_value=json.dumps({"success": True})
        )

    def test_rename_symbol_basic(self):
        """测试基本重命名"""
        result = self.client.rename_symbol("old_name", "new_name", "src/main.py")
        assert result == {"success": True}
        self.client.agent.get_tool.assert_called_once_with(
            mock_tool_classes["RenameSymbolTool"]
        )

    def test_rename_symbol_args(self):
        """测试重命名参数传递"""
        self.client.rename_symbol("OldClass", "NewClass", "src/main.py")
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["name_path"] == "OldClass"
        assert call_args[1]["new_name"] == "NewClass"
        assert call_args[1]["relative_path"] == "src/main.py"


# ==================== SerenaClient replace_symbol_body 测试 ====================


class TestSerenaClientReplaceSymbolBody:
    """SerenaClient replace_symbol_body 测试"""

    def setup_method(self):
        self.client = SerenaClient(project_path="/test")
        self.mock_tool = MagicMock()
        self.client.agent.get_tool = MagicMock(return_value=self.mock_tool)
        self.client.agent.execute_task = MagicMock(side_effect=lambda fn: fn())
        self.mock_tool.apply = MagicMock(
            return_value=json.dumps({"success": True})
        )

    def test_replace_symbol_body_basic(self):
        """测试基本符号体替换"""
        result = self.client.replace_symbol_body(
            "MyClass.method", "pass", "src/main.py"
        )
        assert result == {"success": True}
        self.client.agent.get_tool.assert_called_once_with(
            mock_tool_classes["ReplaceSymbolBodyTool"]
        )

    def test_replace_symbol_body_args(self):
        """测试替换参数传递"""
        self.client.replace_symbol_body("MyClass.method", "return True", "src/main.py")
        call_args = self.mock_tool.apply.call_args
        assert call_args[1]["name_path"] == "MyClass.method"
        assert call_args[1]["body"] == "return True"
        assert call_args[1]["relative_path"] == "src/main.py"


# ==================== SerenaClient JSON 解析测试 ====================


class TestSerenaClientJsonParsing:
    """SerenaClient JSON 解析异常测试"""

    def setup_method(self):
        self.client = SerenaClient(project_path="/test")
        self.mock_tool = MagicMock()
        self.client.agent.get_tool = MagicMock(return_value=self.mock_tool)

    def test_invalid_json_raises_error(self):
        """测试无效 JSON 返回时抛出异常"""
        self.client.agent.execute_task = MagicMock(return_value="not valid json")
        with pytest.raises(json.JSONDecodeError):
            self.client.find_symbol("MyClass")

    def test_empty_json_array(self):
        """测试空 JSON 数组"""
        self.client.agent.execute_task = MagicMock(return_value="[]")
        result = self.client.find_referencing_symbols("MyClass", "src/main.py")
        assert result == []

    def test_empty_json_object(self):
        """测试空 JSON 对象"""
        self.client.agent.execute_task = MagicMock(return_value="{}")
        result = self.client.find_file("*.py")
        assert result == {}
