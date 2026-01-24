#!/usr/bin/env python3
"""
Serena MCP Stdio 客户端
通过 stdin/stdout 与 Serena MCP 服务器通信

使用方式:
    # 配置 .env 文件中的 SERENA_DIR
    cp .env.example .env
    # 编辑 .env 文件,设置 SERENA_DIR=/path/to/serena

    # 然后直接使用客户端
    python serena_stdio_client.py find-symbol "main"
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# 加载环境变量
from dotenv import load_dotenv

load_dotenv()


class StdioMCPClient:
    """MCP Stdio 客户端"""

    def __init__(self, server_command: list[str]):
        """
        初始化 Stdio 客户端

        Args:
            server_command: 启动 MCP 服务器的命令列表
        """
        self.server_command = server_command
        self.process: asyncio.subprocess.Process | None = None
        self.request_id = 0

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()

    async def connect(self):
        """连接到 MCP 服务器"""
        self.process = await asyncio.create_subprocess_exec(
            *self.server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # 等待服务器初始化
        await asyncio.sleep(1)

    async def close(self):
        """关闭连接"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None

    async def _send_request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        发送请求到 MCP 服务器

        Args:
            method: JSON-RPC 方法名
            params: 方法参数

        Returns:
            服务器响应
        """
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("未连接到服务器")

        # 构造 JSON-RPC 请求
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params,
        }

        # 发送请求
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()

        # 读取响应
        response_line = await self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("服务器已关闭连接")

        response = json.loads(response_line.decode())

        # 检查错误
        if "error" in response:
            raise RuntimeError(f"服务器错误: {response['error']}")

        return response.get("result", {})

    async def list_tools(self) -> list[dict[str, Any]]:
        """列出所有可用工具"""
        result = await self._send_request("tools/list", {})
        return result.get("tools", [])

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """
        调用工具

        Args:
            name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        result = await self._send_request(
            "tools/call", {"name": name, "arguments": arguments}
        )

        # 解析内容
        content = result.get("content", [])
        if content and isinstance(content, list) and content[0].get("type") == "text":
            text = content[0].get("text", "")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text

        return result

    async def initialize(self) -> dict[str, Any]:
        """初始化连接"""
        result = await self._send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "serena-stdio-client",
                    "version": "1.0.0",
                },
            },
        )
        return result


class SerenaStdioClient:
    """Serena Stdio 客户端的高级接口"""

    def __init__(self, project_path: str | None = None):
        """
        初始化 Serena Stdio 客户端

        Args:
            project_path: 项目路径,如果为 None 则使用当前工作目录
        """
        if project_path is None:
            from pathlib import Path

            project_path = str(Path.cwd())

        # 构建 MCP 服务器启动命令
        serena_dir = os.getenv("SERENA_DIR", "/Users/erishen/Github/serena")
        self.server_command = [
            "uv",
            "run",
            "--directory",
            serena_dir,
            "serena",
            "start-mcp-server",
            "--transport",
            "stdio",
            "--project",
            project_path,
        ]

        self.mcp_client = StdioMCPClient(self.server_command)
        self._initialized = False

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.mcp_client.__aenter__()
        await self._ensure_initialized()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.mcp_client.__aexit__(exc_type, exc_val, exc_tb)

    async def _ensure_initialized(self):
        """确保已初始化"""
        if not self._initialized:
            await self.mcp_client.initialize()
            self._initialized = True

    async def find_symbol(
        self,
        name_path_pattern: str,
        relative_path: str | None = None,
        depth: int = 0,
        include_body: bool = False,
    ) -> dict[str, Any]:
        """查找符号"""
        args: dict[str, Any] = {"name_path_pattern": name_path_pattern}
        if relative_path:
            args["relative_path"] = relative_path
        if depth > 0:
            args["depth"] = depth
        if include_body:
            args["include_body"] = True

        return await self.mcp_client.call_tool("find_symbol", args)

    async def find_referencing_symbols(
        self,
        name_path: str,
        relative_path: str,
        include_kinds: list[int] | None = None,
        exclude_kinds: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """查找引用"""
        args: dict[str, Any] = {
            "name_path": name_path,
            "relative_path": relative_path,
        }
        if include_kinds:
            args["include_kinds"] = include_kinds
        if exclude_kinds:
            args["exclude_kinds"] = exclude_kinds

        result = await self.mcp_client.call_tool("find_referencing_symbols", args)
        return result if isinstance(result, list) else []

    async def get_symbols_overview(
        self,
        relative_path: str,
        depth: int = 0,
    ) -> dict[str, Any]:
        """获取符号概览"""
        args: dict[str, Any] = {"relative_path": relative_path}
        if depth > 0:
            args["depth"] = depth

        return await self.mcp_client.call_tool("get_symbols_overview", args)

    async def search_for_pattern(
        self,
        substring_pattern: str,
        relative_path: str | None = None,
        paths_include_glob: str | None = None,
        paths_exclude_glob: str | None = None,
        context_lines_before: int = 0,
        context_lines_after: int = 0,
        restrict_search_to_code_files: bool = False,
    ) -> dict[str, Any]:
        """搜索模式"""
        args: dict[str, Any] = {"substring_pattern": substring_pattern}
        if relative_path:
            args["relative_path"] = relative_path
        if paths_include_glob:
            args["paths_include_glob"] = paths_include_glob
        if paths_exclude_glob:
            args["paths_exclude_glob"] = paths_exclude_glob
        if context_lines_before > 0:
            args["context_lines_before"] = context_lines_before
        if context_lines_after > 0:
            args["context_lines_after"] = context_lines_after
        if restrict_search_to_code_files:
            args["restrict_search_to_code_files"] = True

        return await self.mcp_client.call_tool("search_for_pattern", args)

    async def find_file(
        self, file_mask: str, relative_path: str = "."
    ) -> dict[str, Any]:
        """查找文件"""
        return await self.mcp_client.call_tool(
            "find_file", {"file_mask": file_mask, "relative_path": relative_path}
        )

    async def list_dir(
        self,
        relative_path: str = ".",
        recursive: bool = False,
        skip_ignored_files: bool = True,
    ) -> dict[str, Any]:
        """列出目录"""
        return await self.mcp_client.call_tool(
            "list_dir",
            {
                "relative_path": relative_path,
                "recursive": recursive,
                "skip_ignored_files": skip_ignored_files,
            },
        )

    async def list_tools(self) -> list[dict[str, Any]]:
        """列出所有可用工具"""
        return await self.mcp_client.list_tools()


async def main():
    """主函数 - 演示如何使用 Stdio 客户端"""
    import argparse

    parser = argparse.ArgumentParser(description="Serena MCP Stdio 客户端")
    parser.add_argument(
        "--project", type=str, help="项目路径", default=str(Path.cwd())
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # list-tools 命令
    list_tools_parser = subparsers.add_parser("list-tools", help="列出所有工具")  # noqa: F841

    # find-symbol 命令
    find_symbol_parser = subparsers.add_parser("find-symbol", help="查找符号")
    find_symbol_parser.add_argument("pattern", help="符号路径模式")
    find_symbol_parser.add_argument("--path", help="文件路径")
    find_symbol_parser.add_argument("--depth", type=int, default=0, help="深度")
    find_symbol_parser.add_argument("--include-body", action="store_true", help="包含符号体")

    # find-references 命令
    find_refs_parser = subparsers.add_parser("find-references", help="查找引用")
    find_refs_parser.add_argument("name_path", help="符号路径")
    find_refs_parser.add_argument("file_path", help="文件路径")

    # symbols-overview 命令
    overview_parser = subparsers.add_parser("symbols-overview", help="符号概览")
    overview_parser.add_argument("file_path", help="文件路径")
    overview_parser.add_argument("--depth", type=int, default=0, help="深度")

    # search-pattern 命令
    search_parser = subparsers.add_parser("search-pattern", help="搜索模式")
    search_parser.add_argument("pattern", help="正则表达式模式")
    search_parser.add_argument("--path", help="文件路径")
    search_parser.add_argument("--include", help="包含文件glob模式")
    search_parser.add_argument("--exclude", help="排除文件glob模式")
    search_parser.add_argument("--before", type=int, default=0, help="前置上下文行数")
    search_parser.add_argument("--after", type=int, default=0, help="后置上下文行数")
    search_parser.add_argument("--code-only", action="store_true", help="仅搜索代码文件")

    # find-file 命令
    find_file_parser = subparsers.add_parser("find-file", help="查找文件")
    find_file_parser.add_argument("mask", help="文件名或通配符")
    find_file_parser.add_argument("--path", default=".", help="相对路径")

    # list-dir 命令
    list_dir_parser = subparsers.add_parser("list-dir", help="列出目录")
    list_dir_parser.add_argument("path", default=".", help="相对路径")
    list_dir_parser.add_argument("--recursive", action="store_true", help="递归")
    list_dir_parser.add_argument("--all", action="store_true", help="包含忽略文件")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        async with SerenaStdioClient(project_path=args.project) as client:
            if args.command == "list-tools":
                tools = await client.list_tools()
                print("可用工具:")
                for tool in tools:
                    print(f"  - {tool.get('name')}: {tool.get('description', 'N/A')}")
                print(f"\n总计: {len(tools)} 个工具")

            elif args.command == "find-symbol":
                result = await client.find_symbol(
                    args.pattern,
                    relative_path=args.path,
                    depth=args.depth,
                    include_body=args.include_body,
                )
                print(json.dumps(result, indent=2, ensure_ascii=False))

            elif args.command == "find-references":
                result = await client.find_referencing_symbols(
                    args.name_path,
                    args.file_path,
                )
                print(json.dumps(result, indent=2, ensure_ascii=False))

            elif args.command == "symbols-overview":
                result = await client.get_symbols_overview(args.file_path, depth=args.depth)
                print(json.dumps(result, indent=2, ensure_ascii=False))

            elif args.command == "search-pattern":
                result = await client.search_for_pattern(
                    args.pattern,
                    relative_path=args.path,
                    paths_include_glob=args.include,
                    paths_exclude_glob=args.exclude,
                    context_lines_before=args.before,
                    context_lines_after=args.after,
                    restrict_search_to_code_files=args.code_only,
                )
                print(json.dumps(result, indent=2, ensure_ascii=False))

            elif args.command == "find-file":
                result = await client.find_file(args.mask, args.path)
                print(json.dumps(result, indent=2, ensure_ascii=False))

            elif args.command == "list-dir":
                result = await client.list_dir(
                    args.path, recursive=args.recursive, skip_ignored_files=not args.all
                )
                print(json.dumps(result, indent=2, ensure_ascii=False))

    except RuntimeError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
