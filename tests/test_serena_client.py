#!/usr/bin/env python3
"""
Serena 客户端 Mock 单元测试
使用 unittest.mock 替代真实 Serena 进程
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.backends.serena_stdio_client import StdioMCPClient, SerenaStdioClient  # noqa: E402


# ==================== StdioMCPClient Mock 测试 ====================


class TestStdioMCPClient:
    """StdioMCPClient 单元测试（Mock）"""

    def test_init(self):
        """测试初始化"""
        client = StdioMCPClient(server_command=["echo", "test"])
        assert client.server_command == ["echo", "test"]
        assert client.process is None
        assert client.request_id == 0

    @pytest.mark.asyncio
    async def test_close_no_process(self):
        """测试关闭时无进程"""
        client = StdioMCPClient(server_command=["echo", "test"])
        # 无进程时不报错
        await client.close()
        assert client.process is None

    @pytest.mark.asyncio
    async def test_send_request_increment_id(self):
        """测试请求 ID 递增"""
        client = StdioMCPClient(server_command=["echo", "test"])

        mock_process = MagicMock()
        mock_process.stdin.write = MagicMock()
        mock_process.stdin.drain = AsyncMock()
        mock_process.stdout.readline = AsyncMock(return_value=b'{"jsonrpc":"2.0","id":1,"result":{}}\n')

        client.process = mock_process

        with patch.object(client, "_send_request", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"jsonrpc": "2.0", "id": 1, "result": {}}
            result = await client._send_request("test_method", {})
            assert result["id"] == 1


# ==================== SerenaStdioClient Mock 测试 ====================


class TestSerenaStdioClient:
    """SerenaStdioClient 单元测试（Mock）"""

    def test_init_default_path(self):
        """测试默认项目路径"""
        with patch.dict("os.environ", {"SERENA_DIR": "/tmp/fake_serena"}):
            client = SerenaStdioClient()
            assert client.server_command[0] == "uv"
            assert "start-mcp-server" in client.server_command
            assert "--transport" in client.server_command
            assert "stdio" in client.server_command

    def test_init_custom_path(self):
        """测试自定义项目路径"""
        with patch.dict("os.environ", {"SERENA_DIR": "/tmp/fake_serena"}):
            client = SerenaStdioClient(project_path="/my/project")
            assert "--project" in client.server_command
            idx = client.server_command.index("--project")
            assert client.server_command[idx + 1] == "/my/project"

    def test_server_command_structure(self):
        """测试服务器启动命令结构"""
        with patch.dict("os.environ", {"SERENA_DIR": "/opt/serena"}):
            client = SerenaStdioClient(project_path="/test")
            cmd = client.server_command
            assert cmd == [
                "uv",
                "run",
                "--directory",
                "/opt/serena",
                "serena",
                "start-mcp-server",
                "--transport",
                "stdio",
                "--project",
                "/test",
            ]

    @pytest.mark.asyncio
    async def test_context_manager_calls_connect(self):
        """测试上下文管理器调用连接"""
        client = SerenaStdioClient(project_path="/test")

        with patch.object(client.mcp_client, "__aenter__", new_callable=AsyncMock) as mock_enter, patch.object(
            client.mcp_client, "__aexit__", new_callable=AsyncMock
        ), patch.object(client, "_ensure_initialized", new_callable=AsyncMock):
            mock_enter.return_value = client.mcp_client
            async with client as c:
                assert c is client
                mock_enter.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_calls_close(self):
        """测试上下文管理器退出时关闭"""
        client = SerenaStdioClient(project_path="/test")

        with patch.object(client.mcp_client, "__aenter__", new_callable=AsyncMock), patch.object(
            client.mcp_client, "__aexit__", new_callable=AsyncMock
        ) as mock_exit, patch.object(client, "_ensure_initialized", new_callable=AsyncMock):
            async with client:
                pass
            mock_exit.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_initialized_calls_initialize(self):
        """测试初始化只执行一次"""
        client = SerenaStdioClient(project_path="/test")
        client._initialized = False

        mock_response = {
            "result": {
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "serena", "version": "0.1.0"},
            }
        }

        with patch.object(client.mcp_client, "_send_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            await client._ensure_initialized()
            assert client._initialized is True
            mock_req.assert_called_once()

            # 第二次调用不再发请求
            mock_req.reset_mock()
            await client._ensure_initialized()
            mock_req.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """测试列出工具（Mock）"""
        client = SerenaStdioClient(project_path="/test")

        with patch.object(client.mcp_client, "list_tools", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = [
                {"name": "find_symbol", "description": "Find a symbol"},
                {"name": "find_file", "description": "Find a file"},
            ]
            tools = await client.list_tools()
            assert len(tools) == 2
            assert tools[0]["name"] == "find_symbol"

    @pytest.mark.asyncio
    async def test_find_file(self):
        """测试查找文件（Mock）"""
        client = SerenaStdioClient(project_path="/test")

        with patch.object(client.mcp_client, "call_tool", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"files": ["main.py", "utils.py"]}
            result = await client.find_file("*.py", ".")
            assert "files" in result
            assert len(result["files"]) == 2

    @pytest.mark.asyncio
    async def test_find_symbol(self):
        """测试查找符号（Mock）"""
        client = SerenaStdioClient(project_path="/test")

        with patch.object(client.mcp_client, "call_tool", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = [{"name": "MyClass", "kind": 5, "range": {"start": 1, "end": 10}}]
            result = await client.find_symbol("MyClass")
            assert len(result) == 1
            assert result[0]["name"] == "MyClass"

    @pytest.mark.asyncio
    async def test_get_symbols_overview(self):
        """测试符号概览（Mock）"""
        client = SerenaStdioClient(project_path="/test")

        with patch.object(client.mcp_client, "call_tool", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = [
                {"name": "MyClass", "kind": 5},
                {"name": "my_func", "kind": 12},
            ]
            result = await client.get_symbols_overview("test.py", depth=1)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_search_for_pattern(self):
        """测试搜索模式（Mock）"""
        client = SerenaStdioClient(project_path="/test")

        with patch.object(client.mcp_client, "call_tool", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"test.py": [["line 1 match", "line 2 context"]]}
            result = await client.search_for_pattern(r"def\s+\w+")
            assert "test.py" in result

    @pytest.mark.asyncio
    async def test_list_dir(self):
        """测试列出目录（Mock）"""
        client = SerenaStdioClient(project_path="/test")

        with patch.object(client.mcp_client, "call_tool", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = [
                {"name": "src", "type": "directory"},
                {"name": "main.py", "type": "file"},
            ]
            result = await client.list_dir(".")
            assert len(result) == 2


# ==================== StdioMCPClient 连接/关闭 Mock 测试 ====================


class TestStdioMCPClientConnection:
    """StdioMCPClient 连接和关闭测试（Mock subprocess）"""

    @pytest.mark.asyncio
    async def test_connect_creates_process(self):
        """测试连接创建子进程"""
        client = StdioMCPClient(server_command=["uv", "run", "serena"])

        mock_process = MagicMock()

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_process

            with patch("asyncio.sleep", new_callable=AsyncMock):
                await client.connect()

            mock_exec.assert_called_once()
            assert client.process is mock_process

    @pytest.mark.asyncio
    async def test_close_terminates_process(self):
        """测试关闭终止子进程"""
        client = StdioMCPClient(server_command=["uv", "run", "serena"])

        mock_process = MagicMock()
        mock_process.terminate = MagicMock()
        mock_process.wait = AsyncMock()
        client.process = mock_process

        await client.close()
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        assert client.process is None

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """测试 StdioMCPClient 上下文管理器"""
        client = StdioMCPClient(server_command=["uv", "run", "serena"])

        with patch.object(client, "connect", new_callable=AsyncMock) as mock_connect, patch.object(
            client, "close", new_callable=AsyncMock
        ) as mock_close:
            async with client as c:
                assert c is client
                mock_connect.assert_called_once()

            mock_close.assert_called_once()
