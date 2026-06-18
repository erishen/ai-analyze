#!/usr/bin/env python3
"""
AI-Analyze MCP Server
对外暴露代码分析能力为 MCP Tools，供 AI Agent 调用
"""

import dataclasses
import json
import os
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("ai-analyze")


def _load_project_files(project_path: str, max_files: int = 500) -> dict[str, str]:
    """加载项目源代码文件"""
    files: dict[str, str] = {}
    supported_ext = {".py", ".js", ".ts", ".go", ".java", ".jsx", ".tsx", ".rs", ".cpp", ".c", ".rb", ".php"}

    for root, dirs, filenames in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".venv", "venv", ".mypy_cache", ".ruff_cache"}]
        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext not in supported_ext:
                continue
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    files[filepath] = f.read()
            except OSError:
                continue
            if len(files) >= max_files:
                break

    return files


def _validate_project_path(project_path: str) -> str:
    """验证项目路径"""
    path = Path(project_path).resolve()
    if not path.exists():
        raise ValueError(f"Project path does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"Project path is not a directory: {path}")
    return str(path)


@mcp.tool()
def analyze_project(project_path: str, analysis_types: str = "all") -> str:
    """Analyze a code project comprehensively. Returns security, quality, dependency and performance analysis.

    Args:
        project_path: Absolute path to the project directory to analyze
        analysis_types: Comma-separated analysis types: security,quality,dependency,performance,ast,similarity or "all"
    """
    project_path = _validate_project_path(project_path)
    files = _load_project_files(project_path)

    if not files:
        return json.dumps({"error": "No source files found in the project"})

    types = [t.strip() for t in analysis_types.split(",")]
    if "all" in types:
        types = ["security", "quality", "dependency", "ast"]

    results: dict[str, Any] = {
        "project_path": project_path,
        "total_files": len(files),
        "analysis_types": types,
    }

    if "security" in types:
        from src.security_scanner import SecurityScanner

        scanner = SecurityScanner()
        scan_result = scanner.scan_project(files)
        results["security"] = scan_result.to_dict()

    if "quality" in types:
        from src.quality_score import QualityMetrics, QualityScorer

        scorer = QualityScorer()
        metrics = QualityMetrics(
            lines_of_code=sum(len(c.split("\n")) for c in files.values()),
        )
        results["quality"] = scorer.calculate_score(metrics).to_dict()

    if "dependency" in types:
        from src.dependency_graph import DependencyAnalyzer

        analyzer = DependencyAnalyzer(project_path)
        results["dependency"] = analyzer.analyze_project(files).to_dict()

    if "ast" in types:
        from src.ast_analyzer import ASTAnalyzerFactory, detect_language

        all_functions = 0
        all_classes = 0
        all_smells = 0
        complexities: list[float] = []
        severity_count: dict[str, int] = {}
        smell_types: dict[str, int] = {}
        nesting_count = 0
        file_details: list[dict[str, Any]] = []

        for file_path in list(files.keys())[:100]:
            try:
                language = detect_language(file_path)
                if not language:
                    continue
                analyzer = ASTAnalyzerFactory.create_analyzer(language)
                if not analyzer:
                    continue
                result = analyzer.analyze_file(file_path)

                all_functions += len(result.functions)
                all_classes += len(result.classes)
                all_smells += len(result.code_smells)

                if result.overall_complexity:
                    complexities.append(result.overall_complexity.cyclomatic_complexity)
                    if result.overall_complexity.nesting_depth > 4:
                        nesting_count += 1

                for smell in result.code_smells:
                    sev = smell.severity
                    severity_count[sev] = severity_count.get(sev, 0) + 1
                    smell_types[smell.name] = smell_types.get(smell.name, 0) + 1

                file_details.append(dataclasses.asdict(result))
            except Exception:
                continue

        avg_complexity = round(sum(complexities) / len(complexities), 1) if complexities else 0

        sorted_complexity = sorted(
            file_details,
            key=lambda f: f.get("overall_complexity", {}).get("cyclomatic_complexity", 0),
            reverse=True,
        )
        sorted_lines = sorted(
            file_details,
            key=lambda f: f.get("total_lines", 0),
            reverse=True,
        )

        results["ast"] = {
            "analyzed_files": len(file_details),
            "total_files_in_project": len(files),
            "total_functions": all_functions,
            "total_classes": all_classes,
            "total_code_smells": all_smells,
            "average_cyclomatic_complexity": avg_complexity,
            "deep_nesting_count": nesting_count,
            "code_smells_by_severity": dict(
                sorted(severity_count.items(), key=lambda x: -x[1])
            ),
            "most_common_smell_types": dict(
                sorted(smell_types.items(), key=lambda x: -x[1])[:10]
            ),
            "most_complex_files": [
                {
                    "file": f["file_path"].replace(project_path, "").lstrip("/"),
                    "cyclomatic_complexity": f.get("overall_complexity", {}).get(
                        "cyclomatic_complexity", 0
                    ),
                    "lines_of_code": f.get("overall_complexity", {}).get(
                        "lines_of_code", 0
                    ),
                    "functions": len(f.get("functions", [])),
                    "code_smells": len(f.get("code_smells", [])),
                }
                for f in sorted_complexity[:5]
            ],
            "largest_files": [
                {
                    "file": f["file_path"].replace(project_path, "").lstrip("/"),
                    "total_lines": f.get("total_lines", 0),
                    "functions": len(f.get("functions", [])),
                    "classes": len(f.get("classes", [])),
                    "code_smells": len(f.get("code_smells", [])),
                }
                for f in sorted_lines[:5]
            ],
            "language_breakdown": {},
        }

        for f in file_details:
            lang = f.get("language", "unknown")
            if lang not in results["ast"]["language_breakdown"]:
                results["ast"]["language_breakdown"][lang] = {
                    "files": 0,
                    "functions": 0,
                    "classes": 0,
                }
            results["ast"]["language_breakdown"][lang]["files"] += 1
            results["ast"]["language_breakdown"][lang]["functions"] += len(
                f.get("functions", [])
            )
            results["ast"]["language_breakdown"][lang]["classes"] += len(
                f.get("classes", [])
            )

    return json.dumps(results, ensure_ascii=False, indent=2, default=str)


@mcp.tool()
def scan_security(project_path: str, max_findings: int = 100) -> str:
    """Scan a project for security vulnerabilities. Detects injection, auth issues, sensitive data exposure, misconfigurations, and more.

    Args:
        project_path: Absolute path to the project directory
        max_findings: Maximum number of findings to return (default: 100)
    """
    project_path = _validate_project_path(project_path)
    files = _load_project_files(project_path)

    if not files:
        return json.dumps({"error": "No source files found"})

    from src.security_scanner import SecurityScanner

    scanner = SecurityScanner()
    result = scanner.scan_project(files, max_findings=max_findings)

    return json.dumps(result.to_dict(), ensure_ascii=False, indent=2, default=str)


@mcp.tool()
def analyze_quality(project_path: str) -> str:
    """Analyze code quality and generate a quality score (0-100) with grade (A-F). Covers complexity, maintainability, reliability, and security dimensions.

    Args:
        project_path: Absolute path to the project directory
    """
    project_path = _validate_project_path(project_path)
    files = _load_project_files(project_path)

    if not files:
        return json.dumps({"error": "No source files found"})

    from src.quality_score import QualityMetrics, QualityScorer

    total_loc = sum(len(c.split("\n")) for c in files.values())

    # Try to get more metrics from AST analysis
    code_smells_count = 0
    avg_complexity = 0.0
    try:
        from src.ast_analyzer import ASTAnalyzerFactory, detect_language

        complexities = []
        for file_path in list(files.keys())[:50]:
            try:
                language = detect_language(file_path)
                if not language:
                    continue
                analyzer = ASTAnalyzerFactory.create_analyzer(language)
                if analyzer:
                    result = analyzer.analyze_file(file_path)
                    for func in result.functions:
                        if func.complexity:
                            complexities.append(func.complexity.cyclomatic_complexity)
                    code_smells_count += len(result.code_smells)
            except Exception:
                continue
        if complexities:
            avg_complexity = sum(complexities) / len(complexities)
    except Exception:
        pass

    metrics = QualityMetrics(
        lines_of_code=total_loc,
        cyclomatic_complexity=avg_complexity,
        code_smells=code_smells_count,
    )

    scorer = QualityScorer()
    score = scorer.calculate_score(metrics)

    return json.dumps(score.to_dict(), ensure_ascii=False, indent=2)


@mcp.tool()
def analyze_ast(file_path: str) -> str:
    """Analyze a single source file using AST (Abstract Syntax Tree). Returns functions, classes, complexity metrics, code smells, and import dependencies.

    Args:
        file_path: Absolute path to the source file to analyze
    """
    path = Path(file_path).resolve()
    if not path.exists():
        return json.dumps({"error": f"File not found: {file_path}"})
    if not path.is_file():
        return json.dumps({"error": f"Not a file: {file_path}"})

    from src.ast_analyzer import ASTAnalyzerFactory, detect_language

    language = detect_language(str(path))
    if not language:
        return json.dumps({"error": f"Unsupported file type: {path.suffix}"})

    analyzer = ASTAnalyzerFactory.create_analyzer(language)
    if not analyzer:
        return json.dumps({"error": f"Unsupported file type: {path.suffix}"})

    result = analyzer.analyze_file(str(path))
    return json.dumps(dataclasses.asdict(result), ensure_ascii=False, indent=2, default=str)


@mcp.tool()
def detect_similarities(project_path: str, min_lines: int = 6, similarity_threshold: float = 0.8) -> str:
    """Detect duplicate and similar code blocks across the project. Helps identify refactoring opportunities.

    Args:
        project_path: Absolute path to the project directory
        min_lines: Minimum lines for a code block to be considered (default: 6)
        similarity_threshold: Similarity threshold 0-1 (default: 0.8)
    """
    project_path = _validate_project_path(project_path)
    files = _load_project_files(project_path)

    if not files:
        return json.dumps({"error": "No source files found"})

    from src.similarity import CodeBlock, SimilarityDetector

    detector = SimilarityDetector(similarity_threshold=similarity_threshold)

    # Extract code blocks from files
    for file_path, content in files.items():
        lines = content.split("\n")
        ext = os.path.splitext(file_path)[1]
        language_map = {".py": "python", ".js": "javascript", ".ts": "typescript", ".go": "go", ".java": "java"}
        language = language_map.get(ext, "unknown")

        for i in range(0, len(lines) - min_lines + 1, max(1, min_lines // 2)):
            block_content = "\n".join(lines[i : i + min_lines])
            if block_content.strip():
                block = CodeBlock(
                    file_path=file_path,
                    start_line=i + 1,
                    end_line=min(i + min_lines, len(lines)),
                    content=block_content,
                    language=language,
                )
                detector.add_block(block)

    # Detect duplicates and similar code
    duplicates = detector.find_duplicates()
    similar = detector.find_similar()

    result = {
        "total_blocks": len(detector._blocks) if hasattr(detector, "_blocks") else 0,
        "duplicates": [
            {
                "blocks": [
                    {"file": b.file_path, "start_line": b.start_line, "end_line": b.end_line}
                    for b in pair.blocks
                ],
                "similarity": pair.similarity,
            }
            for pair in duplicates
        ],
        "similar_pairs": [
            {
                "blocks": [
                    {"file": b.file_path, "start_line": b.start_line, "end_line": b.end_line}
                    for b in pair.blocks
                ],
                "similarity": pair.similarity,
            }
            for pair in similar
        ],
    }

    return json.dumps(result, ensure_ascii=False, indent=2, default=str)


@mcp.tool()
def analyze_dependencies(project_path: str) -> str:
    """Analyze module dependencies and generate a dependency graph. Shows import relationships between files, identifies highly-coupled modules and circular dependencies.

    Args:
        project_path: Absolute path to the project directory
    """
    project_path = _validate_project_path(project_path)
    files = _load_project_files(project_path)

    if not files:
        return json.dumps({"error": "No source files found"})

    from src.dependency_graph import DependencyAnalyzer

    analyzer = DependencyAnalyzer(project_path)
    result = analyzer.analyze_project(files)

    return json.dumps(result.to_dict(), ensure_ascii=False, indent=2, default=str)


@mcp.resource("ai-analyze://version")
def get_version() -> str:
    """Get the version of ai-analyze"""
    return "0.3.0"


@mcp.resource("ai-analyze://capabilities")
def get_capabilities() -> str:
    """Get the list of analysis capabilities"""
    return json.dumps({
        "tools": [
            "analyze_project - Full project analysis (security, quality, dependency, AST)",
            "scan_security - Security vulnerability scanning",
            "analyze_quality - Code quality scoring (0-100, A-F grade)",
            "analyze_ast - Single file AST analysis (complexity, code smells)",
            "detect_similarities - Duplicate and similar code detection",
            "analyze_dependencies - Module dependency graph analysis",
        ],
        "supported_languages": ["Python", "JavaScript", "TypeScript", "Go", "Java"],
        "version": "0.3.0",
    })


def main():
    """Start the MCP server"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
