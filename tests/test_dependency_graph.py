#!/usr/bin/env python3
"""Tests for dependency_graph module"""

import sys
from pathlib import Path

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.analyzers.dependency_graph import DependencyAnalyzer, DependencyNode, DependencyEdge, DependencyGraphResult  # noqa: E402


class TestDependencyAnalyzer:
    def setup_method(self):
        self.analyzer = DependencyAnalyzer(project_root=".")

    def test_python_import(self):
        code = "import os\nfrom pathlib import Path\n"
        edges = self.analyzer.analyze_file("main.py", code)
        assert len(edges) >= 2
        assert any(e.target == "os" for e in edges)
        assert any(e.target == "pathlib" for e in edges)

    def test_from_import(self):
        code = "from typing import List, Dict\n"
        edges = self.analyzer.analyze_file("types.py", code)
        assert len(edges) == 1
        assert edges[0].import_type == "from_import"
        assert edges[0].target == "typing"

    def test_js_require(self):
        code = 'const fs = require("fs");\n'
        edges = self.analyzer.analyze_file("app.js", code)
        assert len(edges) >= 1
        assert any(e.target == "fs" for e in edges)

    def test_analyze_project(self):
        files = {
            "main.py": "import os\nfrom pathlib import Path\n",
            "utils.py": "import json\n",
        }
        result = self.analyzer.analyze_project(files)
        assert result.total_files == 2
        assert len(result.nodes) >= 2
        assert len(result.edges) >= 3

    def test_hub_modules(self):
        result = DependencyGraphResult(
            nodes=[
                DependencyNode("a", "a.py", "python", 0, 0),
                DependencyNode("b", "b.py", "python", 0, 0),
            ],
            edges=[
                DependencyEdge("a", "os", "import"),
                DependencyEdge("b", "os", "import"),
            ],
        )
        hubs = result.hub_modules
        assert len(hubs) >= 1
        assert hubs[0][0] == "os"
        assert hubs[0][1] == 2

    def test_circular_dependencies(self):
        result = DependencyGraphResult(
            nodes=[
                DependencyNode("a", "a.py", "python"),
                DependencyNode("b", "b.py", "python"),
            ],
            edges=[
                DependencyEdge("a", "b", "import"),
                DependencyEdge("b", "a", "import"),
            ],
        )
        cycles = result.circular_dependencies
        assert len(cycles) >= 1

    def test_no_circular_dependencies(self):
        result = DependencyGraphResult(
            nodes=[
                DependencyNode("a", "a.py", "python"),
                DependencyNode("b", "b.py", "python"),
            ],
            edges=[
                DependencyEdge("a", "b", "import"),
            ],
        )
        cycles = result.circular_dependencies
        assert len(cycles) == 0

    def test_to_mermaid(self):
        result = DependencyGraphResult(
            edges=[DependencyEdge("a", "b", "import")],
        )
        mermaid = result.to_mermaid()
        assert "graph LR" in mermaid
        assert "a --> b" in mermaid

    def test_to_dot(self):
        result = DependencyGraphResult(
            edges=[DependencyEdge("a", "b", "import")],
        )
        dot = result.to_dot()
        assert "digraph" in dot
        assert '"a" -> "b"' in dot

    def test_leaf_modules(self):
        result = DependencyGraphResult(
            nodes=[
                DependencyNode("a", "a.py", "python"),
                DependencyNode("b", "b.py", "python"),
            ],
            edges=[
                DependencyEdge("a", "b", "import"),
            ],
        )
        leaves = result.leaf_modules
        assert "a" in leaves

    def test_module_coupling(self):
        result = DependencyGraphResult(
            nodes=[
                DependencyNode("a", "a.py", "python"),
                DependencyNode("b", "b.py", "python"),
            ],
            edges=[
                DependencyEdge("a", "b", "import"),
                DependencyEdge("a", "c", "import"),
            ],
        )
        coupling = result.module_coupling
        assert "a" in coupling
        assert coupling["a"] > 0

    def test_result_to_dict(self):
        result = DependencyGraphResult()
        d = result.to_dict()
        assert "total_nodes" in d
        assert "circular_dependencies" in d
