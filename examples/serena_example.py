#!/usr/bin/env python3
"""
Serena MCP 客户端使用示例
演示如何使用 Serena 客户端进行代码分析
"""

import json
from pathlib import Path
from serena_client import SerenaClient


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("示例 1: 基本使用")
    print("=" * 60)

    # 创建客户端 (使用当前目录作为项目)
    client = SerenaClient(project_path=str(Path.cwd()))

    # 查找文件
    print("\n1. 查找 Python 文件:")
    result = client.find_file("*.py", ".")
    if "files" in result:
        print(f"找到 {len(result['files'])} 个 Python 文件:")
        for f in result["files"][:5]:  # 只显示前5个
            print(f"  - {f}")
        if len(result["files"]) > 5:
            print(f"  ... 还有 {len(result['files']) - 5} 个文件")


def example_find_symbols():
    """查找符号示例"""
    print("\n" + "=" * 60)
    print("示例 2: 查找符号")
    print("=" * 60)

    client = SerenaClient()

    # 查找一个特定的函数或类
    print("\n1. 查找 'main' 函数:")
    result = client.find_symbol("main")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def example_symbols_overview():
    """符号概览示例"""
    print("\n" + "=" * 60)
    print("示例 3: 获取文件符号概览")
    print("=" * 60)

    client = SerenaClient()

    # 获取当前脚本的符号概览
    script_path = "serena_client.py"
    if Path(script_path).exists():
        print(f"\n1. 获取 {script_path} 的符号概览:")
        result = client.get_symbols_overview(script_path, depth=1)
        print(json.dumps(result, indent=2, ensure_ascii=False))


def example_search_pattern():
    """搜索模式示例"""
    print("\n" + "=" * 60)
    print("示例 4: 搜索代码模式")
    print("=" * 60)

    client = SerenaClient()

    # 搜索所有函数定义
    print("\n1. 搜索所有函数定义:")
    result = client.search_for_pattern(
        r"def\s+\w+\(",
        paths_include_glob="*.py",
        context_lines_before=0,
        context_lines_after=2,
        restrict_search_to_code_files=True,
    )

    # 显示前几个匹配结果
    count = 0
    for file_path, matches in result.items():
        for match in matches:
            count += 1
            if count <= 3:
                print(f"\n文件: {file_path}")
                for line in match:
                    print(f"  {line}")
        if count >= 3:
            break

    print(f"\n找到 {sum(len(m) for m in result.values())} 个匹配项")


def example_find_references():
    """查找引用示例"""
    print("\n" + "=" * 60)
    print("示例 5: 查找符号引用")
    print("=" * 60)

    # 查找某个符号的引用
    # 需要先知道符号的完整路径和文件位置
    # 这里只是一个示例,实际使用时需要替换为真实的符号路径
    print("\n1. 查找引用 (示例):")
    print("   首先需要通过 find_symbol 找到符号的完整路径")
    print("   然后使用该路径查找引用")
    print("\n   例如:")
    print("   result = client.find_referencing_symbols(")
    print("       name_path='MyClass/my_method',")
    print("       relative_path='src/main.py'")
    print("   )")


def example_comprehensive_analysis():
    """综合分析示例"""
    print("\n" + "=" * 60)
    print("示例 6: 综合分析")
    print("=" * 60)

    client = SerenaClient()

    # 1. 获取项目中的所有 Python 文件
    print("\n步骤 1: 获取项目中的 Python 文件")
    files_result = client.find_file("*.py", ".")

    if "files" not in files_result:
        print("未找到 Python 文件")
        return

    python_files = files_result["files"]
    print(f"找到 {len(python_files)} 个 Python 文件")

    # 2. 对前几个文件进行符号分析
    print("\n步骤 2: 分析文件结构")
    for i, file_path in enumerate(python_files[:3], 1):
        print(f"\n文件 {i}: {file_path}")
        try:
            overview = client.get_symbols_overview(file_path, depth=1)

            # 统计符号类型
            if overview:
                classes = [s for s in overview if s.get("kind") == 5]
                functions = [s for s in overview if s.get("kind") == 12]
                methods = [s for s in overview if s.get("kind") == 6]

                print(f"  - 类: {len(classes)}")
                print(f"  - 函数: {len(functions)}")
                print(f"  - 方法: {len(methods)}")

                # 显示顶层符号
                print("  顶层符号:")
                for symbol in overview[:5]:
                    kind_name = {
                        5: "类",
                        12: "函数",
                        6: "方法",
                        13: "变量",
                    }.get(symbol.get("kind"), "未知")
                    print(f"    - {symbol.get('name', 'N/A')} ({kind_name})")
        except Exception as e:
            print(f"  分析失败: {e}")


def main():
    """运行所有示例"""
    print("Serena MCP 客户端使用示例")
    print("=" * 60)

    try:
        example_basic_usage()
        example_find_symbols()
        example_symbols_overview()
        example_search_pattern()
        example_find_references()
        example_comprehensive_analysis()

        print("\n" + "=" * 60)
        print("所有示例执行完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
