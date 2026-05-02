#!/usr/bin/env python3
"""
AST 可视化模块
支持 AST 树形结构展示、代码复杂度热力图、依赖关系图
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import logging

from .ast_analyzer import (
    ClassInfo,
    CodeSmell,
    ComplexityMetrics,
    FileAnalysisResult,
    FunctionInfo,
)

logger = logging.getLogger(__name__)


class ASTVisualizer:
    """AST 分析结果可视化器"""

    def __init__(self, output_dir: str = "./ast_visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def visualize_tree(
        self,
        analysis_result: FileAnalysisResult,
        output_format: str = "html",
        max_depth: int = 10,
    ) -> str:
        """
        生成 AST 树形结构可视化

        Args:
            analysis_result: 文件分析结果
            output_format: 输出格式 (html/json)
            max_depth: 最大展示深度

        Returns:
            生成的文件路径
        """
        if output_format == "json":
            return self._visualize_tree_json(analysis_result)
        return self._visualize_tree_html(analysis_result, max_depth)

    def _build_tree_data(self, result: FileAnalysisResult, max_depth: int) -> Dict[str, Any]:
        """构建树形数据结构"""
        children: List[Dict[str, Any]] = []

        # 添加导入节点
        if result.imports:
            import_children = []
            for imp in result.imports:
                import_children.append({
                    "name": imp,
                    "type": "import",
                    "severity": "info",
                })
            children.append({
                "name": f"Imports ({len(result.imports)})",
                "type": "import_group",
                "severity": "info",
                "children": import_children,
            })

        # 添加类节点
        for cls in result.classes:
            cls_node = self._build_class_node(cls)
            children.append(cls_node)

        # 添加独立函数节点
        for func in result.functions:
            # 跳过已属于类的方法
            is_method = any(
                func.name == m.name and func.line_start == m.line_start
                for cls in result.classes
                for m in cls.methods
            )
            if not is_method:
                children.append(self._build_function_node(func))

        # 添加代码坏味道节点
        if result.code_smells:
            smell_children = []
            for smell in result.code_smells:
                smell_children.append({
                    "name": f"{smell.name} (L{smell.location.split(':')[-1]})",
                    "type": "code_smell",
                    "severity": smell.severity,
                    "detail": smell.description,
                    "suggestion": smell.suggestion,
                })
            children.append({
                "name": f"Code Smells ({len(result.code_smells)})",
                "type": "smell_group",
                "severity": self._worst_severity(result.code_smells),
                "children": smell_children,
            })

        tree = {
            "name": Path(result.file_path).name,
            "type": "file",
            "severity": self._compute_file_severity(result),
            "detail": f"Total lines: {result.total_lines}",
            "children": children,
            "metrics": self._complexity_to_dict(result.overall_complexity),
        }
        return tree

    def _build_class_node(self, cls: ClassInfo) -> Dict[str, Any]:
        """构建类节点"""
        method_children = [self._build_function_node(m) for m in cls.methods]

        # 属性节点
        prop_children = []
        for prop in cls.properties:
            prop_children.append({
                "name": prop,
                "type": "property",
                "severity": "info",
            })

        children = method_children + prop_children

        cls_smells = [s for s in cls.code_smells]
        if cls_smells:
            smell_children = []
            for smell in cls_smells:
                smell_children.append({
                    "name": f"{smell.name}",
                    "type": "code_smell",
                    "severity": smell.severity,
                    "detail": smell.description,
                })
            children.append({
                "name": f"Smells ({len(cls_smells)})",
                "type": "smell_group",
                "severity": self._worst_severity(cls_smells),
                "children": smell_children,
            })

        return {
            "name": f"class {cls.name}",
            "type": "class",
            "severity": self._compute_class_severity(cls),
            "detail": f"Lines {cls.line_start}-{cls.line_end}, Inheritance: {cls.inheritance_depth}",
            "children": children,
        }

    def _build_function_node(self, func: FunctionInfo) -> Dict[str, Any]:
        """构建函数节点"""
        prefix = "async " if func.is_async else ""
        static = "static " if func.is_static else ""
        params = ", ".join(func.parameters)
        ret = f" -> {func.return_type}" if func.return_type else ""

        severity = "info"
        cc = func.complexity.cyclomatic_complexity
        if cc > 15:
            severity = "critical"
        elif cc > 10:
            severity = "high"
        elif cc > 5:
            severity = "medium"

        children = []

        # 复杂度指标子节点
        metrics_node = {
            "name": "Complexity Metrics",
            "type": "metrics",
            "severity": severity,
            "children": [
                {
                    "name": f"Cyclomatic: {func.complexity.cyclomatic_complexity}",
                    "type": "metric",
                    "severity": "critical" if cc > 10 else "info",
                },
                {
                    "name": f"Cognitive: {func.complexity.cognitive_complexity}",
                    "type": "metric",
                    "severity": "info",
                },
                {
                    "name": f"Nesting: {func.complexity.nesting_depth}",
                    "type": "metric",
                    "severity": "high" if func.complexity.nesting_depth > 4 else "info",
                },
                {
                    "name": f"LOC: {func.complexity.lines_of_code}",
                    "type": "metric",
                    "severity": "info",
                },
            ],
        }
        children.append(metrics_node)

        # 参数节点
        if func.parameters:
            param_children = [
                {"name": p, "type": "parameter", "severity": "info"}
                for p in func.parameters
            ]
            children.append({
                "name": f"Parameters ({len(func.parameters)})",
                "type": "param_group",
                "severity": "high" if len(func.parameters) > 5 else "info",
                "children": param_children,
            })

        # 代码坏味道
        if func.code_smells:
            smell_children = []
            for smell in func.code_smells:
                smell_children.append({
                    "name": smell.name,
                    "type": "code_smell",
                    "severity": smell.severity,
                    "detail": smell.description,
                    "suggestion": smell.suggestion,
                })
            children.append({
                "name": f"Smells ({len(func.code_smells)})",
                "type": "smell_group",
                "severity": self._worst_severity(func.code_smells),
                "children": smell_children,
            })

        return {
            "name": f"{prefix}{static}{func.name}({params}){ret}",
            "type": "function",
            "severity": severity,
            "detail": f"Lines {func.line_start}-{func.line_end}",
            "children": children,
        }

    def _visualize_tree_html(self, result: FileAnalysisResult, max_depth: int) -> str:
        """生成 HTML 格式的 AST 树形可视化"""
        tree_data = self._build_tree_data(result, max_depth)
        html_content = self._generate_tree_html(tree_data, result)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = Path(result.file_path).stem
        filename = f"ast_tree_{project_name}_{timestamp}.html"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"AST tree visualization saved to {filepath}")
        return str(filepath)

    def _visualize_tree_json(self, result: FileAnalysisResult) -> str:
        """生成 JSON 格式的 AST 树形数据"""
        tree_data = self._build_tree_data(result, max_depth=10)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = Path(result.file_path).stem
        filename = f"ast_tree_{project_name}_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(tree_data, f, indent=2, ensure_ascii=False)

        logger.info(f"AST tree JSON saved to {filepath}")
        return str(filepath)

    def visualize_complexity_heatmap(
        self,
        analysis_results: List[FileAnalysisResult],
        output_format: str = "html",
    ) -> str:
        """
        生成代码复杂度热力图

        Args:
            analysis_results: 多个文件的分析结果
            output_format: 输出格式 (html/json)

        Returns:
            生成的文件路径
        """
        heatmap_data = self._build_heatmap_data(analysis_results)

        if output_format == "json":
            return self._save_heatmap_json(heatmap_data)
        return self._save_heatmap_html(heatmap_data, analysis_results)

    def _build_heatmap_data(self, results: List[FileAnalysisResult]) -> List[Dict[str, Any]]:
        """构建热力图数据"""
        data = []
        for result in results:
            file_data = {
                "file": Path(result.file_path).name,
                "file_path": result.file_path,
                "total_lines": result.total_lines,
                "cyclomatic_complexity": result.overall_complexity.cyclomatic_complexity,
                "cognitive_complexity": result.overall_complexity.cognitive_complexity,
                "nesting_depth": result.overall_complexity.nesting_depth,
                "loc": result.overall_complexity.lines_of_code,
                "comment_ratio": (
                    result.overall_complexity.comment_lines / max(result.overall_complexity.lines_of_code, 1)
                ),
                "function_count": len(result.functions),
                "class_count": len(result.classes),
                "smell_count": len(result.code_smells),
                "functions": [],
            }

            for func in result.functions:
                file_data["functions"].append({
                    "name": func.name,
                    "line_start": func.line_start,
                    "line_end": func.line_end,
                    "cyclomatic": func.complexity.cyclomatic_complexity,
                    "cognitive": func.complexity.cognitive_complexity,
                    "nesting": func.complexity.nesting_depth,
                    "loc": func.complexity.lines_of_code,
                    "params": len(func.parameters),
                })

            data.append(file_data)
        return data

    def _save_heatmap_json(self, data: List[Dict[str, Any]]) -> str:
        """保存热力图 JSON 数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ast_heatmap_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Heatmap JSON saved to {filepath}")
        return str(filepath)

    def _save_heatmap_html(self, data: List[Dict[str, Any]], results: List[FileAnalysisResult]) -> str:
        """保存热力图 HTML"""
        html_content = self._generate_heatmap_html(data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ast_heatmap_{timestamp}.html"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Heatmap HTML saved to {filepath}")
        return str(filepath)

    # ---- 辅助方法 ----

    @staticmethod
    def _complexity_to_dict(m: ComplexityMetrics) -> Dict[str, int]:
        return {
            "cyclomatic": m.cyclomatic_complexity,
            "cognitive": m.cognitive_complexity,
            "nesting": m.nesting_depth,
            "loc": m.lines_of_code,
            "comments": m.comment_lines,
            "blank": m.blank_lines,
        }

    @staticmethod
    def _worst_severity(smells: List[CodeSmell]) -> str:
        """返回最严重的坏味道等级"""
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        worst = "info"
        for s in smells:
            if severity_order.get(s.severity, 0) > severity_order.get(worst, 0):
                worst = s.severity
        return worst

    @staticmethod
    def _compute_file_severity(result: FileAnalysisResult) -> str:
        """计算文件整体严重程度"""
        cc = result.overall_complexity.cyclomatic_complexity
        smell_count = len(result.code_smells)
        if cc > 30 or smell_count > 10:
            return "critical"
        if cc > 15 or smell_count > 5:
            return "high"
        if cc > 8 or smell_count > 2:
            return "medium"
        return "info"

    @staticmethod
    def _compute_class_severity(cls: ClassInfo) -> str:
        """计算类严重程度"""
        max_cc = max((m.complexity.cyclomatic_complexity for m in cls.methods), default=0)
        smell_count = len(cls.code_smells)
        if max_cc > 15 or smell_count > 5:
            return "critical"
        if max_cc > 10 or smell_count > 2:
            return "high"
        if max_cc > 5 or smell_count > 0:
            return "medium"
        return "info"

    # ---- HTML 模板生成 ----

    @staticmethod
    def _severity_color(severity: str) -> str:
        colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#20c997",
            "info": "#0d6efd",
        }
        return colors.get(severity, "#6c757d")

    @staticmethod
    def _type_icon(node_type: str) -> str:
        icons = {
            "file": "📄",
            "class": "🏗️",
            "function": "⚡",
            "import": "📦",
            "import_group": "📦",
            "property": "🔑",
            "code_smell": "💨",
            "smell_group": "💨",
            "metrics": "📊",
            "metric": "📏",
            "param_group": "📋",
            "parameter": "📌",
        }
        return icons.get(node_type, "•")

    def _generate_tree_html(self, tree_data: Dict[str, Any], result: FileAnalysisResult) -> str:  # noqa: C901
        """生成 AST 树形可视化 HTML"""
        tree_json = json.dumps(tree_data, ensure_ascii=False)
        metrics = tree_data.get("metrics", {})
        gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Build HTML parts to avoid E501 in f-string templates
        html_head = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1.0">
<title>AST Tree - {tree_data['name']}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont,
  'Segoe UI', Roboto, sans-serif;
  background: #1a1a2e; color: #e0e0e0; padding: 20px; }}
.header {{ background: #16213e; border-radius: 12px;
  padding: 24px; margin-bottom: 20px; }}
.header h1 {{ color: #e94560; font-size: 24px;
  margin-bottom: 8px; }}
.header .meta {{ color: #a0a0b0; font-size: 14px; }}
.metrics-bar {{ display: flex; gap: 16px;
  flex-wrap: wrap; margin-top: 16px; }}
.metric-card {{ background: #0f3460; border-radius: 8px;
  padding: 12px 20px; min-width: 120px; }}
.metric-card .label {{ font-size: 12px; color: #a0a0b0; }}
.metric-card .value {{ font-size: 24px;
  font-weight: 700; color: #e94560; }}
.tree-container {{ background: #16213e;
  border-radius: 12px; padding: 20px; }}
.tree-node {{ margin-left: 20px; }}
.tree-node-header {{ display: flex; align-items: center;
  gap: 8px; padding: 6px 12px; border-radius: 6px;
  cursor: pointer; transition: background 0.2s; }}
.tree-node-header:hover {{ background: #0f3460; }}
.tree-node-header .icon {{ font-size: 16px; }}
.tree-node-header .name {{ font-weight: 500; }}
.tree-node-header .badge {{ font-size: 11px;
  padding: 2px 8px; border-radius: 10px; color: #fff; }}
.tree-node-header .detail {{ font-size: 12px;
  color: #a0a0b0; margin-left: auto; }}
.tree-children {{ margin-left: 16px;
  border-left: 1px dashed #333; padding-left: 8px; }}
.tree-children.collapsed {{ display: none; }}
.search-bar {{ margin-bottom: 16px; }}
.search-bar input {{ width: 100%; padding: 10px 16px;
  border-radius: 8px; border: 1px solid #333;
  background: #0f3460; color: #e0e0e0;
  font-size: 14px; outline: none; }}
.search-bar input:focus {{ border-color: #e94560; }}
.legend {{ display: flex; gap: 12px;
  flex-wrap: wrap; margin-bottom: 16px; }}
.legend-item {{ display: flex; align-items: center;
  gap: 4px; font-size: 12px; }}
.legend-dot {{ width: 10px; height: 10px;
  border-radius: 50%; }}
</style>
</head>
<body>
<div class="header">
  <h1>AST Tree Visualization</h1>
  <div class="meta">File: {tree_data['name']}
    | Generated: {gen_time}</div>
  <div class="metrics-bar">
    <div class="metric-card">
      <div class="label">Cyclomatic</div>
      <div class="value">{metrics.get('cyclomatic', 0)}</div>
    </div>
    <div class="metric-card">
      <div class="label">Cognitive</div>
      <div class="value">{metrics.get('cognitive', 0)}</div>
    </div>
    <div class="metric-card">
      <div class="label">Nesting</div>
      <div class="value">{metrics.get('nesting', 0)}</div>
    </div>
    <div class="metric-card">
      <div class="label">LOC</div>
      <div class="value">{metrics.get('loc', 0)}</div>
    </div>
    <div class="metric-card">
      <div class="label">Functions</div>
      <div class="value">{len(result.functions)}</div>
    </div>
    <div class="metric-card">
      <div class="label">Classes</div>
      <div class="value">{len(result.classes)}</div>
    </div>
  </div>
</div>"""

        html_legend = """
<div class="legend">
  <div class="legend-item">
    <div class="legend-dot" style="background:#dc3545"></div>
    Critical</div>
  <div class="legend-item">
    <div class="legend-dot" style="background:#fd7e14"></div>
    High</div>
  <div class="legend-item">
    <div class="legend-dot" style="background:#ffc107"></div>
    Medium</div>
  <div class="legend-item">
    <div class="legend-dot" style="background:#20c997"></div>
    Low</div>
  <div class="legend-item">
    <div class="legend-dot" style="background:#0d6efd"></div>
    Info</div>
</div>
<div class="search-bar">
  <input type="text" id="searchInput"
         placeholder="Search nodes...">
</div>
<div class="tree-container" id="treeContainer"></div>"""

        html_script = f"""<script>
const treeData = {tree_json};
const severityColors = {{
  critical:'#dc3545', high:'#fd7e14',
  medium:'#ffc107', low:'#20c997', info:'#0d6efd'
}};
const typeIcons = {{
  file:'📄', class:'🏗️', function:'⚡',
  import:'📦', import_group:'📦', property:'🔑',
  code_smell:'💨', smell_group:'💨',
  metrics:'📊', metric:'📏',
  param_group:'📋', parameter:'📌'
}};

function renderNode(node, depth) {{{{
  const div = document.createElement('div');
  div.className = 'tree-node';
  div.dataset.name = node.name.toLowerCase();

  const header = document.createElement('div');
  header.className = 'tree-node-header';

  const icon = typeIcons[node.type] || '•';
  const color = severityColors[node.severity] || '#6c757d';

  const hasChildren = node.children && node.children.length > 0;
  const arrow = hasChildren ? '▼' : '';

  header.innerHTML = `
    <span class="icon">${{icon}}</span>
    <span class="name">${{node.name}}</span>
    <span class="badge"
          style="background:${{color}}">${{node.severity}}</span>
    ${{node.detail ? `<span class="detail">${{node.detail}}</span>` : ''}}
    ${{hasChildren ? '<span style="color:#a0a0b0;font-size:12px">' + arrow + '</span>' : ''}}
  `;

  div.appendChild(header);

  if (hasChildren) {{{{
    const childrenDiv = document.createElement('div');
    childrenDiv.className = 'tree-children';
    if (depth > 3) childrenDiv.classList.add('collapsed');
    node.children.forEach(child =>
      childrenDiv.appendChild(renderNode(child, depth + 1)));
    div.appendChild(childrenDiv);

    header.addEventListener('click', () => {{{{
      childrenDiv.classList.toggle('collapsed');
    }}}});
  }}}}

  if (node.suggestion) {{{{
    header.title = 'Suggestion: ' + node.suggestion;
  }}}}

  return div;
}}}}

const container = document.getElementById('treeContainer');
container.appendChild(renderNode(treeData, 0));

document.getElementById('searchInput')
  .addEventListener('input', function(e) {{{{
    const q = e.target.value.toLowerCase();
    document.querySelectorAll('.tree-node')
      .forEach(node => {{{{
        const name = node.dataset.name || '';
        const match = !q || name.includes(q);
        node.style.display = match ? '' : 'none';
      }}}});
  }}}});
</script>
</body>
</html>"""

        return html_head + html_legend + html_script

    def _generate_heatmap_html(self, data: List[Dict[str, Any]]) -> str:
        """生成复杂度热力图 HTML"""
        data_json = json.dumps(data, ensure_ascii=False)
        gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        html_head = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1.0">
<title>AST Complexity Heatmap</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont,
  'Segoe UI', Roboto, sans-serif;
  background: #1a1a2e; color: #e0e0e0; padding: 20px; }}
.header {{ background: #16213e; border-radius: 12px;
  padding: 24px; margin-bottom: 20px; }}
.header h1 {{ color: #e94560; font-size: 24px;
  margin-bottom: 8px; }}
.header .meta {{ color: #a0a0b0; font-size: 14px; }}
.heatmap {{ background: #16213e; border-radius: 12px;
  padding: 20px; overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ padding: 10px 14px; text-align: left;
  border-bottom: 1px solid #2a2a4a; }}
th {{ background: #0f3460; color: #e94560;
  font-weight: 600; position: sticky; top: 0; }}
tr:hover {{ background: #1a1a3e; }}
.cc-cell {{ font-weight: 700; border-radius: 4px;
  padding: 4px 8px; text-align: center;
  display: inline-block; min-width: 40px; }}
.legend {{ display: flex; gap: 16px;
  margin-bottom: 16px; flex-wrap: wrap; }}
.legend-item {{ display: flex; align-items: center;
  gap: 6px; font-size: 13px; }}
.legend-bar {{ width: 60px; height: 12px;
  border-radius: 4px; }}
.func-section {{ margin-top: 8px; padding: 8px;
  background: #0f3460; border-radius: 6px;
  font-size: 13px; }}
.func-row {{ display: flex; justify-content: space-between;
  padding: 4px 8px;
  border-bottom: 1px solid #1a1a3e; }}
.sort-btn {{ cursor: pointer; user-select: none; }}
.sort-btn:hover {{ color: #e94560; }}
</style>
</head>
<body>
<div class="header">
  <h1>AST Complexity Heatmap</h1>
  <div class="meta">Generated: {gen_time}
    | Files: {len(data)}</div>
</div>
<div class="legend">
  <div class="legend-item">
    <div class="legend-bar"
      style="background:linear-gradient(
        to right,#20c997,#ffc107,#fd7e14,#dc3545)">
    </div>Complexity: Low → Critical</div>
</div>
<div class="heatmap">
  <table id="heatmapTable">
    <thead>
      <tr>
        <th class="sort-btn" data-col="file">File ↕</th>
        <th class="sort-btn" data-col="total_lines">Lines ↕</th>
        <th class="sort-btn" data-col="cyclomatic_complexity">Cyclomatic ↕</th>
        <th class="sort-btn" data-col="cognitive_complexity">Cognitive ↕</th>
        <th class="sort-btn" data-col="nesting_depth">Nesting ↕</th>
        <th class="sort-btn" data-col="function_count">Functions ↕</th>
        <th class="sort-btn" data-col="class_count">Classes ↕</th>
        <th class="sort-btn" data-col="smell_count">Smells ↕</th>
        <th>Details</th>
      </tr>
    </thead>
    <tbody id="heatmapBody"></tbody>
  </table>
</div>"""

        html_script = f"""<script>
const data = {data_json};

function ccColor(val) {{{{
  if (val > 15) return '#dc3545';
  if (val > 10) return '#fd7e14';
  if (val > 5) return '#ffc107';
  if (val > 2) return '#20c997';
  return '#0d6efd';
}}}}

function ccCell(val) {{{{
  const c = ccColor(val);
  return `<span class="cc-cell"
    style="background:${{c}}22;color:${{c}}">${{val}}</span>`;
}}}}

let sortCol = 'cyclomatic_complexity';
let sortAsc = false;

function render() {{{{
  const sorted = [...data].sort((a, b) => {{{{
    const av = a[sortCol], bv = b[sortCol];
    return sortAsc ? (av > bv ? 1 : -1) : (bv > av ? 1 : -1);
  }}}});
  const tbody = document.getElementById('heatmapBody');
  tbody.innerHTML = sorted.map(row => {{{{
    const funcsHtml = row.functions.map(f =>
      `<div class="func-row"><span>${{f.name}}()</span>` +
      `${{ccCell(f.cyclomatic)}}` +
      `<span style="color:#a0a0b0">L${{f.line_start}}-${{f.line_end}}</span></div>`
    ).join('');
    return `<tr>
      <td title="${{row.file_path}}">${{row.file}}</td>
      <td>${{row.total_lines}}</td>
      <td>${{ccCell(row.cyclomatic_complexity)}}</td>
      <td>${{ccCell(row.cognitive_complexity)}}</td>
      <td>${{ccCell(row.nesting_depth)}}</td>
      <td>${{row.function_count}}</td>
      <td>${{row.class_count}}</td>
      <td>${{ccCell(row.smell_count)}}</td>
      <td><details>
        <summary style="cursor:pointer;color:#e94560">
          Functions</summary>
        <div class="func-section">
          ${{funcsHtml || 'N/A'}}</div>
      </details></td>
    </tr>`;
  }}}}).join('');
}}}}

document.querySelectorAll('.sort-btn').forEach(th => {{{{
  th.addEventListener('click', () => {{{{
    const col = th.dataset.col;
    if (sortCol === col) sortAsc = !sortAsc;
    else {{ sortCol = col; sortAsc = false; }}
    render();
  }}}});
}}}});

render();
</script>
</body>
</html>"""

        return html_head + html_script
