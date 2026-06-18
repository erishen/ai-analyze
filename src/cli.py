"""CLI entry point for ai-analyze: `ai-analyze ast <project_path>`"""

import argparse
import json
import logging
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional


for name in ("src.ast_rules", "src.tech_debt", "src.quality_score", "src.security_scanner", "src"):
    logging.getLogger(name).setLevel(logging.WARNING)

_SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "ast_analyzer_tool.py"

EXCLUDE_DIRS = {".venv", "venv", "__pycache__", ".git", "node_modules", ".ruff_cache", ".mypy_cache", ".pytest_cache", ".cache", "htmlcov", ".eggs"}


def _aggregate_smells(file_result) -> tuple[list, list]:
    """Collect all code smells from file, function, and class levels."""
    all_smells = list(file_result.code_smells)
    for func in file_result.functions:
        all_smells.extend(func.code_smells)
    for cls in file_result.classes:
        all_smells.extend(cls.code_smells)
    return all_smells


def _build_summary_results(p: Path, file_results: list) -> dict:
    """Build aggregated summary from all file analysis results."""
    total_complexity = 0
    language_stats = {}
    severity_counter = Counter()
    smell_counter = Counter()
    deep_nesting = 0
    file_entries = []

    for f_r in file_results:
        total_complexity += f_r.overall_complexity.cyclomatic_complexity

        if f_r.overall_complexity.nesting_depth > 4:
            deep_nesting += 1

        lang = f_r.language
        if lang not in language_stats:
            language_stats[lang] = {"files": 0, "functions": 0, "classes": 0}
        language_stats[lang]["files"] += 1
        language_stats[lang]["functions"] += len(f_r.functions)
        language_stats[lang]["classes"] += len(f_r.classes)

        all_smells = _aggregate_smells(f_r)
        for smell in all_smells:
            severity_counter[smell.severity] += 1
            smell_counter[smell.name] += 1

        file_entries.append({
            "file_path": f_r.file_path,
            "cyclomatic_complexity": f_r.overall_complexity.cyclomatic_complexity,
            "lines_of_code": f_r.overall_complexity.lines_of_code,
            "total_lines": f_r.total_lines,
            "functions": len(f_r.functions),
            "classes": len(f_r.classes),
            "code_smells": len(all_smells),
        })

    total_files = len(file_results)
    total_functions = sum(len(f_r.functions) for f_r in file_results)
    total_classes = sum(len(f_r.classes) for f_r in file_results)
    total_smells = sum(len(_aggregate_smells(f_r)) for f_r in file_results)

    file_entries.sort(key=lambda x: x["cyclomatic_complexity"], reverse=True)
    most_complex = [
        {
            "file": e["file_path"].replace(str(p), "").lstrip("/"),
            "cyclomatic_complexity": e["cyclomatic_complexity"],
            "lines_of_code": e["lines_of_code"],
            "functions": e["functions"],
            "code_smells": e["code_smells"],
        }
        for e in file_entries[:5]
    ]

    file_entries.sort(key=lambda x: x["total_lines"], reverse=True)
    largest = [
        {
            "file": e["file_path"].replace(str(p), "").lstrip("/"),
            "total_lines": e["total_lines"],
            "functions": e["functions"],
            "classes": e["classes"],
            "code_smells": e["code_smells"],
        }
        for e in file_entries[:5]
    ]

    return {
        "total_files": total_files,
        "total_functions": total_functions,
        "total_classes": total_classes,
        "total_code_smells": total_smells,
        "average_cyclomatic_complexity": round(total_complexity / total_files, 1) if total_files else 0,
        "deep_nesting_count": deep_nesting,
        "code_smells_by_severity": dict(severity_counter),
        "most_common_smell_types": dict(smell_counter.most_common()),
        "language_breakdown": language_stats,
        "most_complex_files": most_complex,
        "largest_files": largest,
    }


def _run_ast(project_path: str, output: Optional[str] = None, patterns=None):
    """Run AST analysis via subprocess, filtering out excluded dirs."""
    p = Path(project_path).resolve()

    if patterns is None:
        patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.tsx", "**/*.jsx"]

    files = set()
    for pat in patterns:
        for f in p.glob(pat):
            if f.is_file():
                rel = f.relative_to(p).as_posix()
                parts = Path(rel).parts
                if not any(part in EXCLUDE_DIRS for part in parts):
                    files.add(f)

    if not files:
        print(json.dumps({"error": "No files found to analyze"}, indent=2))
        return

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tools.ast_analyzer_tool import ASTAnalysisTool  # noqa: E402

    tool = ASTAnalysisTool(str(p))

    raw_results = {
        "project_path": str(p),
        "timestamp": datetime.now().isoformat(),
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "files": [],
    }

    file_results = []
    for file_path in sorted(files):
        try:
            file_result = tool.analyze_file(str(file_path))
            if not file_result:
                continue

            serialized = tool._serialize_result(file_result)
            raw_results["files"].append(serialized)
            file_results.append(file_result)

        except Exception as e:
            print(f"Warning: failed to analyze {file_path}: {e}", file=sys.stderr)
            continue

    output_path = p / f"ast_analysis_{p.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    if output:
        output_path = Path(output)

    output_path.write_text(json.dumps(raw_results, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = _build_summary_results(p, file_results)

    print(json.dumps({
        "project_path": str(p),
        "summary": summary,
        "report_file": str(output_path),
    }, indent=2, ensure_ascii=False))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(prog="ai-analyze", description="AI-powered code analysis tool")
    sub = parser.add_subparsers(dest="command", required=True)

    ast_p = sub.add_parser("ast", help="Run AST code structure analysis on a project")
    ast_p.add_argument("project_path", help="Path to the project to analyze")
    ast_p.add_argument("--output", "-o", help="Output JSON file path (default: auto-generated)")
    ast_p.add_argument("--patterns", nargs="+", default=["**/*.py", "**/*.js", "**/*.ts", "**/*.tsx", "**/*.jsx"],
                       help="File glob patterns to include (default: **/*.py, **/*.js, **/*.ts, **/*.tsx, **/*.jsx)")

    args = parser.parse_args()

    if args.command == "ast":
        _run_ast(args.project_path, output=args.output, patterns=args.patterns)


if __name__ == "__main__":
    main()
