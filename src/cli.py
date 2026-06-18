"""CLI entry point for ai-analyze: `ai-analyze ast <project_path>`"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# Re-export the analysis functions from tools/ast_analyzer_tool.py via subprocess
# We import from the tool module directly for the heavy lifting.
_SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "ast_analyzer_tool.py"

EXCLUDE_DIRS = {".venv", "venv", "__pycache__", ".git", "node_modules", ".ruff_cache", ".mypy_cache", ".pytest_cache", ".cache", "htmlcov", ".eggs"}


def _run_ast(project_path: str, output: Optional[str] = None, patterns=None):
    """Run AST analysis via subprocess, filtering out excluded dirs."""
    import tempfile

    p = Path(project_path).resolve()
    out_path = output

    # Stage 1: list all matching files, excluding unwanted dirs
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

    # Stage 2: build a temp project with only these files (symlinks) for analysis
    # Actually, simpler: write a file list and pass to analyzer
    # OR: just run the analysis on each file individually via the tool API
    # Simplest: write a temp file list and use it

    # Actually the easiest: run the tool on the real project but pass patterns
    # that exclude .venv etc. Not possible with glob patterns alone.
    # So let's do it file-by-file using the tool's analyze_file method.

    # Better approach: use the tool's API directly
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tools.ast_analyzer_tool import ASTAnalysisTool  # noqa: E402

    tool = ASTAnalysisTool(str(p))

    results = {
        "project_path": str(p),
        "timestamp": datetime.now().isoformat(),
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "files": [],
        "summary": {
            "total_files": 0,
            "total_functions": 0,
            "total_classes": 0,
            "total_code_smells": 0,
            "average_complexity": 0,
            "languages": {},
        },
    }

    total_complexity = 0
    language_stats = {}

    for file_path in sorted(files):
        try:
            file_result = tool.analyze_file(str(file_path))
            if not file_result:
                continue

            serialized = tool._serialize_result(file_result)
            results["files"].append(serialized)
            results["summary"]["total_files"] += 1
            results["summary"]["total_functions"] += len(file_result.functions)
            results["summary"]["total_classes"] += len(file_result.classes)
            results["summary"]["total_code_smells"] += len(file_result.code_smells)
            total_complexity += file_result.overall_complexity.cyclomatic_complexity

            lang = file_result.language
            if lang not in language_stats:
                language_stats[lang] = {"files": 0, "functions": 0, "classes": 0}
            language_stats[lang]["files"] += 1
            language_stats[lang]["functions"] += len(file_result.functions)
            language_stats[lang]["classes"] += len(file_result.classes)

        except Exception as e:
            print(f"Warning: failed to analyze {file_path}: {e}", file=sys.stderr)
            continue

    if results["summary"]["total_files"] > 0:
        results["summary"]["average_complexity"] = total_complexity / results["summary"]["total_files"]
    results["summary"]["languages"] = language_stats

    output_path = p / f"ast_analysis_{p.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    if output:
        output_path = Path(output)

    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    # Print summary to stdout
    s = results["summary"]
    print(json.dumps({
        "project_path": str(p),
        "summary": s,
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
