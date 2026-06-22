#!/usr/bin/env python3
"""
PR Diff 分析模块
只分析 PR 变更的文件，输出增量质量评估

使用方式：
1. 通过 git diff 获取变更文件列表
2. 只分析变更的文件
3. 输出增量质量评估报告
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .language_backend import BackendFactory

logger = logging.getLogger(__name__)


@dataclass
class DiffHunk:
    """代码变更块"""
    file_path: str
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    content: str = ""
    change_type: str = "modify"  # add, delete, modify


@dataclass
class FileDiff:
    """文件变更"""
    file_path: str
    change_type: str  # added, deleted, modified, renamed
    hunks: list[DiffHunk] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0


@dataclass
class PRDiffResult:
    """PR Diff 分析结果"""
    total_files: int = 0
    total_additions: int = 0
    total_deletions: int = 0
    file_diffs: list[FileDiff] = field(default_factory=list)
    analysis_results: list[dict[str, Any]] = field(default_factory=list)
    quality_assessment: dict[str, Any] = field(default_factory=dict)


def parse_git_diff(diff_output: str) -> list[FileDiff]:
    """解析 git diff 输出

    Args:
        diff_output: git diff 的输出文本

    Returns:
        FileDiff 列表
    """
    file_diffs: list[FileDiff] = []
    current_file: Optional[FileDiff] = None

    for line in diff_output.split("\n"):
        if line.startswith("diff --git"):
            # 新文件
            if current_file:
                file_diffs.append(current_file)

            # 解析文件路径
            parts = line.split(" b/")
            if len(parts) >= 2:
                file_path = parts[-1].strip()
            else:
                file_path = line.split()[-1]

            current_file = FileDiff(file_path=file_path, change_type="modified")

        elif line.startswith("new file"):
            if current_file:
                current_file.change_type = "added"

        elif line.startswith("deleted file"):
            if current_file:
                current_file.change_type = "deleted"

        elif line.startswith("rename from"):
            if current_file:
                current_file.change_type = "renamed"

        elif line.startswith("@@"):
            # 解析 hunk 头: @@ -old_start,old_lines +new_start,new_lines @@
            if current_file:
                try:
                    # 提取 +new_start,new_lines 部分
                    plus_part = line.split("+")[1].split("@@")[0].strip()
                    if "," in plus_part:
                        new_start = int(plus_part.split(",")[0])
                        new_lines = int(plus_part.split(",")[1])
                    else:
                        new_start = int(plus_part)
                        new_lines = 1

                    # 提取 -old_start,old_lines 部分
                    minus_part = line.split("-")[1].split("+")[0].strip()
                    if "," in minus_part:
                        old_start = int(minus_part.split(",")[0])
                        old_lines = int(minus_part.split(",")[1])
                    else:
                        old_start = int(minus_part)
                        old_lines = 1

                    current_file.hunks.append(DiffHunk(
                        file_path=current_file.file_path,
                        old_start=old_start,
                        old_lines=old_lines,
                        new_start=new_start,
                        new_lines=new_lines,
                    ))
                except (ValueError, IndexError):
                    pass

        elif line.startswith("+") and not line.startswith("+++"):
            if current_file:
                current_file.additions += 1

        elif line.startswith("-") and not line.startswith("---"):
            if current_file:
                current_file.deletions += 1

    if current_file:
        file_diffs.append(current_file)

    return file_diffs


def get_diff_from_git(
    project_path: str,
    base: str = "main",
    head: str = "HEAD",
) -> str:
    """从 git 获取 diff

    Args:
        project_path: 项目路径
        base: 基准分支
        head: 目标分支

    Returns:
        git diff 输出
    """
    try:
        result = subprocess.run(
            ["git", "diff", f"{base}...{head}", "--no-color"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"git diff failed: {e.stderr}")
        raise
    except FileNotFoundError:
        raise FileNotFoundError("git not found. Please install git.")


def get_changed_files_from_git(
    project_path: str,
    base: str = "main",
    head: str = "HEAD",
) -> list[str]:
    """从 git 获取变更文件列表

    Args:
        project_path: 项目路径
        base: 基准分支
        head: 目标分支

    Returns:
        变更文件路径列表
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...{head}"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except subprocess.CalledProcessError as e:
        logger.error(f"git diff --name-only failed: {e.stderr}")
        raise


def analyze_pr_diff(
    project_path: str,
    base: str = "main",
    head: str = "HEAD",
    backend_name: Optional[str] = None,
) -> PRDiffResult:
    """分析 PR Diff

    Args:
        project_path: 项目路径
        base: 基准分支
        head: 目标分支
        backend_name: 语言后端名称

    Returns:
        PRDiffResult
    """
    result = PRDiffResult()

    # 获取 diff
    diff_output = get_diff_from_git(project_path, base, head)
    file_diffs = parse_git_diff(diff_output)

    result.file_diffs = file_diffs
    result.total_files = len(file_diffs)
    result.total_additions = sum(f.additions for f in file_diffs)
    result.total_deletions = sum(f.deletions for f in file_diffs)

    # 只分析有新增/修改的代码文件
    analyzable_extensions = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java",
        ".cpp", ".cc", ".c", ".h", ".rs", ".rb", ".php",
    }

    backend = BackendFactory.create(project_path, backend_name=backend_name)

    for file_diff in file_diffs:
        if file_diff.change_type == "deleted":
            continue

        ext = os.path.splitext(file_diff.file_path)[1]
        if ext not in analyzable_extensions:
            continue

        full_path = os.path.join(project_path, file_diff.file_path)
        if not os.path.exists(full_path):
            continue

        try:
            analysis = backend.analyze_file(full_path)
            # 转换为字典
            from dataclasses import asdict
            result.analysis_results.append({
                "file_path": file_diff.file_path,
                "change_type": file_diff.change_type,
                "additions": file_diff.additions,
                "deletions": file_diff.deletions,
                "functions": len(analysis.functions),
                "classes": len(analysis.classes),
                "code_smells": len(analysis.code_smells),
                "complexity": analysis.overall_complexity.cyclomatic_complexity if analysis.overall_complexity else 0,
            })
        except Exception as e:
            logger.warning(f"Failed to analyze {file_diff.file_path}: {e}")

    # 质量评估
    total_smells = sum(r["code_smells"] for r in result.analysis_results)
    total_complexity = sum(r["complexity"] for r in result.analysis_results)
    files_with_smells = sum(1 for r in result.analysis_results if r["code_smells"] > 0)

    result.quality_assessment = {
        "files_analyzed": len(result.analysis_results),
        "total_code_smells": total_smells,
        "total_complexity": total_complexity,
        "files_with_smells": files_with_smells,
        "risk_level": _assess_risk(total_smells, total_complexity, result.total_additions),
        "recommendation": _generate_recommendation(total_smells, files_with_smells, result.total_additions),
    }

    return result


def _assess_risk(smells: int, complexity: int, additions: int) -> str:
    """评估风险等级"""
    # 每 50 行新增代码超过 2 个 smell 或复杂度 > 10 认为高风险
    if additions == 0:
        return "low"

    smell_rate = smells / (additions / 50) if additions > 0 else 0
    complexity_rate = complexity / (additions / 50) if additions > 0 else 0

    if smell_rate > 3 or complexity_rate > 15:
        return "high"
    elif smell_rate > 1.5 or complexity_rate > 8:
        return "medium"
    return "low"


def _generate_recommendation(smells: int, files_with_smells: int, additions: int) -> str:
    """生成审查建议"""
    if additions == 0:
        return "No code additions in this PR."

    parts = []
    if smells == 0:
        parts.append("No code smells detected in changed files.")
    elif smells <= 3:
        parts.append(f"Minor issues: {smells} code smell(s) in {files_with_smells} file(s). Consider quick review.")
    else:
        parts.append(f"Significant issues: {smells} code smell(s) in {files_with_smells} file(s). Thorough review recommended.")

    if additions > 500:
        parts.append("Large PR (>500 additions). Consider splitting into smaller PRs.")

    return " ".join(parts)
