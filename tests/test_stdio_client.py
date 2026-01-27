#!/usr/bin/env python3
"""
测试 Serena Stdio 客户端
演示如何通过 stdio 接口调用 Serena MCP 服务器
"""

import asyncio
import json
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from serena_stdio_client import SerenaStdioClient  # noqa: E402

# 检查 Serena 是否可用
SERENA_DIR = os.getenv("SERENA_DIR", "/Users/erishen/Github/serena")
SERENA_AVAILABLE = os.path.exists(SERENA_DIR) or os.path.exists(os.path.join(SERENA_DIR, "pyproject.toml"))


@pytest.mark.skipif(not SERENA_AVAILABLE, reason="Serena 服务器未安装")
@pytest.mark.asyncio
async def test_list_tools():
    """测试列出工具"""
    print("=" * 60)
    print("测试 1: 列出所有可用工具")
    print("=" * 60)

    async with SerenaStdioClient() as client:
        tools = await client.list_tools()
        print(f"\n找到 {len(tools)} 个工具:\n")
        for i, tool in enumerate(tools, 1):
            name = tool.get("name", "N/A")
            description = tool.get("description", "N/A")
            print(f"{i:2d}. {name:30s} - {description}")


@pytest.mark.skipif(not SERENA_AVAILABLE, reason="Serena 服务器未安装")
@pytest.mark.asyncio
async def test_find_file():
    """测试查找文件"""
    print("\n" + "=" * 60)
    print("测试 2: 查找文件")
    print("=" * 60)

    async with SerenaStdioClient() as client:
        print("\n1. 查找所有 Python 文件:")
        result = await client.find_file("*.py", ".")
        print(json.dumps(result, indent=2, ensure_ascii=False))


@pytest.mark.skipif(not SERENA_AVAILABLE, reason="Serena 服务器未安装")
@pytest.mark.asyncio
async def test_find_symbol():
    """测试查找符号"""
    print("\n" + "=" * 60)
    print("测试 3: 查找符号")
    print("=" * 60)

    async with SerenaStdioClient() as client:
        print("\n1. 查找 'main' 符号:")
        result = await client.find_symbol("main")
        print(json.dumps(result, indent=2, ensure_ascii=False))


@pytest.mark.skipif(not SERENA_AVAILABLE, reason="Serena 服务器未安装")
@pytest.mark.asyncio
async def test_symbols_overview():
    """测试符号概览"""
    print("\n" + "=" * 60)
    print("测试 4: 符号概览")
    print("=" * 60)

    async with SerenaStdioClient() as client:
        print("\n1. 获取 serena_stdio_client.py 的符号概览:")
        result = await client.get_symbols_overview("serena_stdio_client.py", depth=1)

        # 显示统计信息
        if isinstance(result, list):
            classes = [s for s in result if s.get("kind") == 5]
            functions = [s for s in result if s.get("kind") == 12]
            methods = [s for s in result if s.get("kind") == 6]

            print("\n统计:")
            print(f"  - 类: {len(classes)}")
            print(f"  - 函数: {len(functions)}")
            print(f"  - 方法: {len(methods)}")
            print(f"  - 总计: {len(result)} 个符号")

            # 显示前几个符号
            print("\n前几个符号:")
            for i, symbol in enumerate(result[:5], 1):
                kind_name = {
                    5: "类",
                    12: "函数",
                    6: "方法",
                    13: "变量",
                }.get(symbol.get("kind"), "未知")
                print(f"  {i}. {symbol.get('name', 'N/A')} ({kind_name})")


@pytest.mark.skipif(not SERENA_AVAILABLE, reason="Serena 服务器未安装")
@pytest.mark.asyncio
async def test_search_pattern():
    """测试搜索模式"""
    print("\n" + "=" * 60)
    print("测试 5: 搜索模式")
    print("=" * 60)

    async with SerenaStdioClient() as client:
        print("\n1. 搜索所有函数定义:")
        result = await client.search_for_pattern(
            r"async def\s+\w+\(",
            paths_include_glob="*.py",
            context_lines_before=0,
            context_lines_after=3,
            restrict_search_to_code_files=True,
        )

        # 显示前几个匹配结果
        count = 0
        for file_path, matches in result.items():
            for match in matches:
                count += 1
                if count <= 3:
                    print(f"\n文件: {file_path}")
                    print("匹配内容:")
                    for line in match:
                        print(f"  {line}")
            if count >= 3:
                break

        if count == 0:
            print("未找到匹配项")
        else:
            total_matches = sum(len(m) for m in result.values())
            print(f"\n找到 {total_matches} 个匹配项 (显示前 3 个)")


@pytest.mark.skipif(not SERENA_AVAILABLE, reason="Serena 服务器未安装")
@pytest.mark.asyncio
async def test_list_dir():
    """测试列出目录"""
    print("\n" + "=" * 60)
    print("测试 6: 列出目录")
    print("=" * 60)

    async with SerenaStdioClient() as client:
        print("\n1. 列出当前目录:")
        result = await client.list_dir(".", recursive=False)
        print(json.dumps(result, indent=2, ensure_ascii=False))


@pytest.mark.skipif(not SERENA_AVAILABLE, reason="Serena 服务器未安装")
@pytest.mark.asyncio
async def test_comprehensive_workflow():
    """测试综合工作流"""
    print("\n" + "=" * 60)
    print("测试 7: 综合工作流")
    print("=" * 60)

    async with SerenaStdioClient() as client:
        print("\n步骤 1: 查找所有 Python 文件")
        files_result = await client.find_file("*.py", ".")

        if "files" not in files_result:
            print("未找到 Python 文件")
            return

        python_files = files_result["files"]
        print(f"找到 {len(python_files)} 个 Python 文件")

        # 步骤 2: 分析第一个文件
        if python_files:
            print(f"\n步骤 2: 分析 {python_files[0]}")
            try:
                overview = await client.get_symbols_overview(python_files[0], depth=1)

                if overview:
                    classes = [s for s in overview if s.get("kind") == 5]
                    functions = [s for s in overview if s.get("kind") == 12]
                    methods = [s for s in overview if s.get("kind") == 6]

                    print(f"  - 类: {len(classes)}")
                    print(f"  - 函数: {len(functions)}")
                    print(f"  - 方法: {len(methods)}")

                    # 步骤 3: 查找第一个函数
                    for symbol in overview:
                        if symbol.get("kind") == 12:
                            func_name = symbol.get("name")
                            print(f"\n步骤 3: 查找 '{func_name}' 的详细信息")
                            detail = await client.find_symbol(
                                func_name, relative_path=python_files[0], include_body=True
                            )
                            print(f"  找到 {len(detail) if isinstance(detail, list) else 1} 个匹配")
                            break
            except Exception as e:
                print(f"  分析失败: {e}")


async def main():
    """运行所有测试"""
    print("Serena Stdio 客户端测试")
    print("=" * 60)
    print("\n注意: Stdio 客户端会自动启动和管理 MCP 服务器进程")
    print("无需手动启动服务器!")
    print("=" * 60)

    if not SERENA_AVAILABLE:
        print("\n警告: Serena 服务器未安装，跳过集成测试")
        print(f"请安装 Serena: git clone git@github.com:oraios/serena.git")
        print("或设置 SERENA_DIR 环境变量")
        return

    try:
        await test_list_tools()
        await test_find_file()
        await test_find_symbol()
        await test_symbols_overview()
        await test_search_pattern()
        await test_list_dir()
        await test_comprehensive_workflow()

        print("\n" + "=" * 60)
        print("所有测试完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        print("\n可能的原因:")
        print("1. uv 命令未安装")
        print("2. Serena 路径不正确")
        print("3. 项目路径权限问题")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
