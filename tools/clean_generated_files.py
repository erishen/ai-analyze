#!/usr/bin/env python3
"""
清理目标项目中由 ai-analyze 生成的 Docker 相关文件
用法：python clean_generated_files.py /path/to/target/project [--yes]
      --yes: 跳过确认，直接删除
"""

import os
import sys
import subprocess
from pathlib import Path

def get_git_new_files(project_dir: Path):
    """
    获取 git 状态中新增或未跟踪的文件列表
    
    Args:
        project_dir: 项目目录路径
        
    Returns:
        set or None: 新增或未跟踪的文件路径集合（相对路径），
                    如果目标目录不是 git 仓库则返回 None
    """
    # 检查是否为 git 仓库
    git_dir = project_dir / ".git"
    if not git_dir.exists():
        return None  # 表示不是 git 仓库
    
    new_files = set()
    try:
        # 在项目目录中运行 git status -s .
        result = subprocess.run(
            ["git", "status", "-s", "."],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print(f"⚠️  git status 失败: {result.stderr}")
            return set()  # 返回空集合，跳过删除
        
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            # git status -s 输出格式：状态字符 文件名
            # 状态字符可能是 'A' (新增), '??' (未跟踪), 'M' (修改) 等
            # 我们只关心新增和未跟踪的文件
            status = line[:2].strip()
            filename = line[3:].strip()
            # 检查状态：'A' 表示已暂存新增，'??' 表示未跟踪
            if status == 'A' or status == '??':
                new_files.add(filename)
            # 注意：'AM' 表示新增并修改，第一个字符是 'A'，我们也视为新增
            elif len(status) > 0 and status[0] == 'A':
                new_files.add(filename)
                
    except subprocess.TimeoutExpired:
        print("⚠️  git status 超时")
        return set()
    except Exception as e:
        print(f"⚠️  获取 git 状态时出错: {e}")
        return set()
    
    return new_files

def confirm_delete(filename: str, reason: str) -> bool:
    """
    询问用户是否确认删除文件
    
    Args:
        filename: 文件名
        reason: 删除原因（用于显示）
        
    Returns:
        bool: True 表示确认删除，False 表示取消
    """
    print(f"❓ 确认删除 {filename} 吗？ ({reason})")
    print("   输入 'y' 或 'yes' 确认删除，其他输入跳过")
    try:
        response = input("   > ").strip().lower()
        return response in ['y', 'yes']
    except (KeyboardInterrupt, EOFError):
        print("\n⏹️  取消删除")
        return False

def confirm_batch_delete(files_to_delete: list[tuple[str, str]]) -> bool:
    """
    批量确认删除文件
    
    Args:
        files_to_delete: 列表，每个元素为 (文件名, 删除原因)
        
    Returns:
        bool: True 表示确认删除所有文件，False 表示取消
    """
    if not files_to_delete:
        return True  # 没有文件需要删除，直接返回 True
    
    print("📋 以下文件将被删除：")
    for filename, reason in files_to_delete:
        print(f"   • {filename} ({reason})")
    
    print(f"\n❓ 确认删除以上 {len(files_to_delete)} 个文件吗？")
    print("   输入 'y' 或 'yes' 确认删除，其他输入取消")
    try:
        response = input("   > ").strip().lower()
        return response in ['y', 'yes']
    except (KeyboardInterrupt, EOFError):
        print("\n⏹️  取消删除")
        return False

def clean_docker_files(project_path: str, skip_confirmation: bool = False) -> int:
    """
    清理目标项目中的 Docker 相关生成文件
    
    Args:
        project_path: 目标项目路径（支持 ~ 扩展）
        skip_confirmation: 是否跳过确认（直接删除）
        
    Returns:
        删除的文件数量
    """
    # 展开 ~ 到用户主目录
    expanded_path = os.path.expanduser(project_path)
    target_dir = Path(expanded_path)
    
    if not target_dir.exists():
        raise FileNotFoundError(f"目标目录不存在: {expanded_path}")
    if not target_dir.is_dir():
        raise NotADirectoryError(f"目标路径不是目录: {expanded_path}")
    
    print(f"正在清理目标项目: {target_dir}")
    if skip_confirmation:
        print("⚠️  跳过确认模式，将直接删除文件")
    
    # 获取 git 新增文件列表
    git_new_files = get_git_new_files(target_dir)
    
    # 要删除的文件列表
    files_to_delete = [
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        ".dockerignore",
        "docker-build.sh",
        "docker-run.sh",
    ]
    
    # 收集待删除文件列表
    pending_deletions = []  # (filename, reason)
    
    for filename in files_to_delete:
        file_path = target_dir / filename
        if file_path.exists() and file_path.is_file():
            # 判断是否检查 git 状态
            if git_new_files is None:
                # 不是 git 仓库，可以删除
                pending_deletions.append((filename, "目标目录不是 git 仓库"))
            elif filename in git_new_files:
                # 在 git 新增列表中，可以删除
                pending_deletions.append((filename, "git 新增文件"))
            else:
                # 不在 git 新增列表中，跳过
                print(f"跳过: {filename} (不在 git 新增列表中，可能已提交)")
    
    # 如果没有待删除文件，直接返回
    if not pending_deletions:
        print("没有需要删除的文件。")
        return 0
    
    # 确认删除
    should_delete = False
    if skip_confirmation:
        should_delete = True
        print(f"跳过确认，将删除 {len(pending_deletions)} 个文件。")
    else:
        should_delete = confirm_batch_delete(pending_deletions)
    
    # 执行删除
    deleted_count = 0
    if should_delete:
        for filename, reason in pending_deletions:
            file_path = target_dir / filename
            try:
                file_path.unlink()
                print(f"删除: {filename} ({reason})")
                deleted_count += 1
            except Exception as e:
                print(f"删除失败 {filename}: {e}")
    else:
        print("取消删除，没有文件被删除。")
    
    return deleted_count

def main():
    # 解析命令行参数
    skip_confirmation = False
    project_path = None
    
    if len(sys.argv) == 2:
        project_path = sys.argv[1]
    elif len(sys.argv) == 3 and sys.argv[2] == "--yes":
        project_path = sys.argv[1]
        skip_confirmation = True
    else:
        print("用法: python clean_generated_files.py /path/to/target/project [--yes]")
        print("      --yes: 跳过确认，直接删除")
        sys.exit(1)
    
    try:
        deleted_count = clean_docker_files(project_path, skip_confirmation)
        print(f"✅ 清理完成，删除了 {deleted_count} 个文件。")
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()