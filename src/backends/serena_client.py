#!/usr/bin/env python3
"""
Serena MCP 客户端工具
通过 MCP 协议与 Serena 服务器通信，不直接 import serena 内部 API
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def _check_serena_available() -> None:
    """检查 serena 是否配置"""
    serena_dir = os.getenv("SERENA_DIR", "")
    if not serena_dir or not Path(serena_dir).exists():
        raise ImportError(
            "serena 未安装或 SERENA_DIR 未配置。"
            "请安装 serena 并在 .env 中设置 SERENA_DIR。"
        )


class SerenaClient:
    """Serena 工具客户端 — 通过 MCP 协议通信"""

    def __init__(self, project_path: str | None = None):
        """
        初始化 Serena 客户端

        Args:
            project_path: 项目路径,如果为 None 则使用当前工作目录
        """
        _check_serena_available()

        if project_path is None:
            project_path = str(Path.cwd())

        self.project_path = project_path

    def _run_async(self, coro):
        """在同步上下文中运行异步协程"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # 已在异步上下文中，创建新线程运行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return asyncio.run(coro)

    async def _get_client(self):
        """获取 SerenaStdioClient 实例"""
        from .serena_stdio_client import SerenaStdioClient

        return SerenaStdioClient(project_path=self.project_path)

    def find_symbol(
        self,
        name_path_pattern: str,
        relative_path: str | None = None,
        depth: int = 0,
        include_body: bool = False,
    ) -> dict[str, Any]:
        """
        查找符号(类、方法、函数等)

        Args:
            name_path_pattern: 符号路径模式
            relative_path: 相对路径限制搜索范围
            depth: 获取子节点的深度
            include_body: 是否包含符号体代码

        Returns:
            查找结果字典
        """
        async def _find():
            async with await self._get_client() as client:
                return await client.find_symbol(
                    name_path_pattern,
                    relative_path=relative_path,
                    depth=depth,
                    include_body=include_body,
                )

        return self._run_async(_find())

    def find_referencing_symbols(
        self,
        name_path: str,
        relative_path: str,
        include_kinds: list[int] | None = None,
        exclude_kinds: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """
        查找引用特定符号的代码

        Args:
            name_path: 符号的完整路径
            relative_path: 包含该符号的文件路径
            include_kinds: 包含的符号类型
            exclude_kinds: 排除的符号类型

        Returns:
            引用列表
        """
        async def _find_refs():
            async with await self._get_client() as client:
                return await client.find_referencing_symbols(
                    name_path,
                    relative_path,
                    include_kinds=include_kinds,
                    exclude_kinds=exclude_kinds,
                )

        return self._run_async(_find_refs())

    def get_symbols_overview(
        self,
        relative_path: str,
        depth: int = 0,
    ) -> dict[str, Any]:
        """
        获取文件的符号概览

        Args:
            relative_path: 文件相对路径
            depth: 获取子节点的深度

        Returns:
            符号概览字典
        """
        async def _overview():
            async with await self._get_client() as client:
                return await client.get_symbols_overview(relative_path, depth=depth)

        return self._run_async(_overview())

    def search_for_pattern(
        self,
        substring_pattern: str,
        relative_path: str | None = None,
        paths_include_glob: str | None = None,
        paths_exclude_glob: str | None = None,
        context_lines_before: int = 0,
        context_lines_after: int = 0,
        restrict_search_to_code_files: bool = False,
    ) -> dict[str, Any]:
        """
        搜索代码模式

        Args:
            substring_pattern: 正则表达式模式
            relative_path: 限制搜索范围
            paths_include_glob: 包含文件模式
            paths_exclude_glob: 排除文件模式
            context_lines_before: 前置上下文行数
            context_lines_after: 后置上下文行数
            restrict_search_to_code_files: 是否限制为代码文件

        Returns:
            搜索结果字典
        """
        async def _search():
            async with await self._get_client() as client:
                return await client.search_for_pattern(
                    substring_pattern,
                    relative_path=relative_path,
                    paths_include_glob=paths_include_glob,
                    paths_exclude_glob=paths_exclude_glob,
                    context_lines_before=context_lines_before,
                    context_lines_after=context_lines_after,
                    restrict_search_to_code_files=restrict_search_to_code_files,
                )

        return self._run_async(_search())

    def find_file(self, file_mask: str, relative_path: str = ".") -> dict[str, Any]:
        """
        查找文件

        Args:
            file_mask: 文件名或通配符
            relative_path: 相对路径

        Returns:
            查找结果字典
        """
        async def _find_file():
            async with await self._get_client() as client:
                return await client.find_file(file_mask, relative_path)

        return self._run_async(_find_file())

    def rename_symbol(
        self,
        name_path: str,
        new_name: str,
        relative_path: str,
    ) -> dict[str, Any]:
        """重命名符号（需要 SerenaBackend 支持）"""
        raise NotImplementedError("rename_symbol requires direct Serena integration. Use SerenaStdioClient directly.")

    def replace_symbol_body(
        self,
        name_path: str,
        body: str,
        relative_path: str,
    ) -> dict[str, Any]:
        """替换符号体（需要 SerenaBackend 支持）"""
        raise NotImplementedError("replace_symbol_body requires direct Serena integration. Use SerenaStdioClient directly.")


def main():
    """主函数 - 演示如何使用 SerenaClient"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Serena MCP 客户端工具")
    parser.add_argument("--project", type=str, help="项目路径", default=str(Path.cwd()))

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    client = SerenaClient(project_path=args.project)

    try:
        if args.command == "find-symbol":
            result = client.find_symbol(
                args.pattern,
                relative_path=args.path,
                depth=args.depth,
                include_body=args.include_body,
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "find-references":
            result = client.find_referencing_symbols(
                args.name_path,
                args.file_path,
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "symbols-overview":
            result = client.get_symbols_overview(args.file_path, depth=args.depth)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "search-pattern":
            result = client.search_for_pattern(
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
            result = client.find_file(args.mask, args.path)
            print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception:
        print("错误: 内部服务器错误", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
