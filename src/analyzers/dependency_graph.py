#!/usr/bin/env python3
"""
依赖关系分析模块
分析文件/模块间的依赖关系，生成依赖图数据
"""

import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class DependencyNode:
    """依赖图节点"""

    module_name: str
    file_path: str
    language: str
    out_degree: int = 0
    in_degree: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "file_path": self.file_path,
            "language": self.language,
            "out_degree": self.out_degree,
            "in_degree": self.in_degree,
        }


@dataclass
class DependencyEdge:
    """依赖图边"""

    source: str
    target: str
    import_type: str  # import, from_import, require, include
    line_number: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "import_type": self.import_type,
            "line_number": self.line_number,
        }


@dataclass
class DependencyGraphResult:
    """依赖图分析结果"""

    nodes: List[DependencyNode] = field(default_factory=list)
    edges: List[DependencyEdge] = field(default_factory=list)
    total_files: int = 0

    @property
    def circular_dependencies(self) -> List[List[str]]:
        """检测循环依赖"""
        adj: Dict[str, Set[str]] = defaultdict(set)
        for edge in self.edges:
            adj[edge.source].add(edge.target)

        cycles: List[List[str]] = []
        visited: Set[str] = set()
        path: List[str] = []
        path_set: Set[str] = set()

        def dfs(node: str) -> None:
            if node in path_set:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            path_set.add(node)
            for neighbor in adj[node]:
                dfs(neighbor)
            path.pop()
            path_set.discard(node)

        for node_name in list(adj.keys()):
            if node_name not in visited:
                dfs(node_name)

        return cycles

    @property
    def hub_modules(self) -> List[Tuple[str, int]]:
        """高入度的核心模块（被最多模块依赖）"""
        in_counts: Dict[str, int] = defaultdict(int)
        for edge in self.edges:
            in_counts[edge.target] += 1
        sorted_hubs = sorted(in_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_hubs[:10]

    @property
    def leaf_modules(self) -> List[str]:
        """叶子模块（不依赖其他模块）"""
        sources = {e.source for e in self.edges}
        targets = {e.target for e in self.edges}
        return sorted(sources - targets)

    @property
    def module_coupling(self) -> Dict[str, float]:
        """模块耦合度（每个模块的出度/总模块数）"""
        if not self.nodes:
            return {}
        total = max(len(self.nodes), 1)
        out_counts: Dict[str, int] = defaultdict(int)
        for edge in self.edges:
            out_counts[edge.source] += 1
        return {k: round(v / total, 3) for k, v in out_counts.items()}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "total_files": self.total_files,
            "circular_dependencies": self.circular_dependencies,
            "hub_modules": self.hub_modules,
            "leaf_modules": self.leaf_modules,
            "module_coupling": self.module_coupling,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }

    def to_mermaid(self) -> str:
        """生成 Mermaid 格式的依赖图"""
        lines = ["graph LR"]
        for edge in self.edges:
            src = edge.source.replace(".", "_")
            tgt = edge.target.replace(".", "_")
            lines.append(f"    {src} --> {tgt}")
        return "\n".join(lines)

    def to_dot(self) -> str:
        """生成 Graphviz DOT 格式的依赖图"""
        lines = ["digraph dependencies {", "    rankdir=LR;"]
        for edge in self.edges:
            lines.append(
                f'    "{edge.source}" -> "{edge.target}";'
            )
        lines.append("}")
        return "\n".join(lines)


class DependencyAnalyzer:
    """依赖关系分析器"""

    # 文件扩展名到语言的映射
    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".java": "java",
    }

    # Python 导入模式
    PY_IMPORT_PATTERNS = [
        (re.compile(r'^import\s+(\S+)'), "import"),
        (re.compile(r'^from\s+([\w.]+)\s+import'), "from_import"),
    ]

    # JS/TS 导入模式
    JS_IMPORT_PATTERNS = [
        (re.compile(r'require\s*\(\s*[\'"]([^"\']+)[\'"]'), "require"),
        (re.compile(r'import\s+.*from\s+[\'"]([^"\']+)[\'"]'), "import"),
        (re.compile(r'import\s+[\'"]([^"\']+)[\'"]'), "import"),
    ]

    # Go 导入模式
    GO_IMPORT_PATTERNS = [
        (re.compile(r'"([^"]+)"'), "include"),
    ]

    def __init__(self, project_root: str = "."):
        self.logger = logging.getLogger("ai-analyze.dependency")
        self.project_root = project_root

    def analyze_file(self, file_path: str, content: str) -> List[DependencyEdge]:
        """分析单个文件的依赖"""
        ext = os.path.splitext(file_path)[1]
        language = self.LANGUAGE_MAP.get(ext, "unknown")
        module_name = self._file_to_module(file_path)

        patterns = self._get_patterns(language)
        edges: List[DependencyEdge] = []

        lines = content.split("\n")
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            for regex, import_type in patterns:
                match = regex.search(stripped)
                if match:
                    target = match.group(1)
                    edges.append(
                        DependencyEdge(
                            source=module_name,
                            target=target,
                            import_type=import_type,
                            line_number=line_num,
                        )
                    )

        return edges

    def analyze_project(self, files: Dict[str, str]) -> DependencyGraphResult:
        """分析项目依赖关系"""
        all_edges: List[DependencyEdge] = []
        node_map: Dict[str, DependencyNode] = {}

        for file_path, content in files.items():
            ext = os.path.splitext(file_path)[1]
            language = self.LANGUAGE_MAP.get(ext, "unknown")
            module_name = self._file_to_module(file_path)

            edges = self.analyze_file(file_path, content)
            all_edges.extend(edges)

            node_map[module_name] = DependencyNode(
                module_name=module_name,
                file_path=file_path,
                language=language,
            )

        # 计算出入度
        out_counts: Dict[str, int] = defaultdict(int)
        in_counts: Dict[str, int] = defaultdict(int)
        for edge in all_edges:
            out_counts[edge.source] += 1
            in_counts[edge.target] += 1

        for name, node in node_map.items():
            node.out_degree = out_counts.get(name, 0)
            node.in_degree = in_counts.get(name, 0)

        # 补充 target 节点（外部依赖）
        existing = set(node_map.keys())
        for edge in all_edges:
            if edge.target not in existing:
                node_map[edge.target] = DependencyNode(
                    module_name=edge.target,
                    file_path="(external)",
                    language="unknown",
                    in_degree=in_counts.get(edge.target, 0),
                )
                existing.add(edge.target)

        return DependencyGraphResult(
            nodes=list(node_map.values()),
            edges=all_edges,
            total_files=len(files),
        )

    def _file_to_module(self, file_path: str) -> str:
        """将文件路径转换为模块名"""
        rel = os.path.relpath(file_path, self.project_root)
        # 去掉扩展名
        base, _ = os.path.splitext(rel)
        # 路径分隔符转为 .
        return base.replace(os.sep, ".")

    def _get_patterns(
        self, language: str
    ) -> List[Tuple[re.Pattern, str]]:
        """获取对应语言的导入模式"""
        if language == "python":
            return self.PY_IMPORT_PATTERNS
        elif language in ("javascript", "typescript"):
            return self.JS_IMPORT_PATTERNS
        elif language == "go":
            return self.GO_IMPORT_PATTERNS
        return []
