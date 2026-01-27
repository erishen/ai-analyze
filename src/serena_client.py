#!/usr/bin/env python3
"""
Serena MCP 客户端工具
用于直接调用 serena 的各种工具,无需启动 MCP 服务器
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

# 加载环境变量
from dotenv import load_dotenv

load_dotenv()

# 添加 serena 到 Python 路径
serena_path = Path(os.getenv("SERENA_DIR", "/Users/erishen/Github/serena"))
if serena_path.exists():
    sys.path.insert(0, str(serena_path / "src"))

# Serene imports after setting up path
from serena.agent import SerenaAgent  # noqa: E402
from serena.tools import (  # noqa: E402
    FindFileTool,
    FindReferencingSymbolsTool,
    FindSymbolTool,
    GetSymbolsOverviewTool,
    RenameSymbolTool,
    ReplaceSymbolBodyTool,
    SearchForPatternTool,
    Tool,
)


class SerenaClient:
    """Serena 工具客户端"""

    def __init__(self, project_path: str | None = None):
        """
        初始化 Serena 客户端

        Args:
            project_path: 项目路径,如果为 None 则使用当前工作目录
        """
        if project_path is None:
            project_path = str(Path.cwd())

        self.agent = SerenaAgent(project=project_path)
        self.project_path = project_path

    def get_tool(self, tool_class: type[Tool]) -> Tool:
        """获取工具实例"""
        return self.agent.get_tool(tool_class)

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
        tool = self.get_tool(FindSymbolTool)

        args: dict[str, Any] = {"name_path_pattern": name_path_pattern}
        if relative_path is not None:
            args["relative_path"] = relative_path
        if depth > 0:
            args["depth"] = depth
        if include_body:
            args["include_body"] = True

        result = self.agent.execute_task(lambda: tool.apply(**args))
        return json.loads(result)

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
        tool = self.get_tool(FindReferencingSymbolsTool)

        args: dict[str, Any] = {
            "name_path": name_path,
            "relative_path": relative_path,
        }
        if include_kinds is not None:
            args["include_kinds"] = include_kinds
        if exclude_kinds is not None:
            args["exclude_kinds"] = exclude_kinds

        result = self.agent.execute_task(lambda: tool.apply(**args))
        return json.loads(result)

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
        tool = self.get_tool(GetSymbolsOverviewTool)

        args: dict[str, Any] = {"relative_path": relative_path}
        if depth > 0:
            args["depth"] = depth

        result = self.agent.execute_task(lambda: tool.apply(**args))
        return json.loads(result)

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
        tool = self.get_tool(SearchForPatternTool)

        args: dict[str, Any] = {"substring_pattern": substring_pattern}
        if relative_path is not None:
            args["relative_path"] = relative_path
        if paths_include_glob is not None:
            args["paths_include_glob"] = paths_include_glob
        if paths_exclude_glob is not None:
            args["paths_exclude_glob"] = paths_exclude_glob
        if context_lines_before > 0:
            args["context_lines_before"] = context_lines_before
        if context_lines_after > 0:
            args["context_lines_after"] = context_lines_after
        if restrict_search_to_code_files:
            args["restrict_search_to_code_files"] = True

        result = self.agent.execute_task(lambda: tool.apply(**args))
        return json.loads(result)

    def find_file(self, file_mask: str, relative_path: str = ".") -> dict[str, Any]:
        """
        查找文件

        Args:
            file_mask: 文件名或通配符
            relative_path: 相对路径

        Returns:
            查找结果字典
        """
        tool = self.get_tool(FindFileTool)

        result = self.agent.execute_task(lambda: tool.apply(file_mask=file_mask, relative_path=relative_path))
        return json.loads(result)

    def rename_symbol(
        self,
        name_path: str,
        new_name: str,
        relative_path: str,
    ) -> dict[str, Any]:
        """
        重命名符号

        Args:
            name_path: 符号的完整路径
            new_name: 新名称
            relative_path: 包含该符号的文件路径

        Returns:
            操作结果
        """
        tool = self.get_tool(RenameSymbolTool)

        result = self.agent.execute_task(
            lambda: tool.apply(name_path=name_path, new_name=new_name, relative_path=relative_path)
        )
        return json.loads(result)

    def replace_symbol_body(
        self,
        name_path: str,
        body: str,
        relative_path: str,
    ) -> dict[str, Any]:
        """
        替换符号体

        Args:
            name_path: 符号的完整路径
            body: 新的符号体
            relative_path: 包含该符号的文件路径

        Returns:
            操作结果
        """
        tool = self.get_tool(ReplaceSymbolBodyTool)

        result = self.agent.execute_task(
            lambda: tool.apply(name_path=name_path, body=body, relative_path=relative_path)
        )
        return json.loads(result)


def main():
    """主函数 - 演示如何使用 SerenaClient"""
    import argparse

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

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
