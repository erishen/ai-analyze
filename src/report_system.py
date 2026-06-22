#!/usr/bin/env python3
"""
报告系统模块
支持 HTML 交互式报告、历史趋势分析、报告对比
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ReportMetadata:
    """报告元数据"""

    project_name: str
    report_type: str
    timestamp: str = ""
    version: str = "0.3.0"

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "report_type": self.report_type,
            "timestamp": self.timestamp,
            "version": self.version,
        }


@dataclass
class TrendDataPoint:
    """趋势数据点"""

    timestamp: str
    value: float
    label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "value": self.value,
            "label": self.label,
        }


@dataclass
class TrendAnalysis:
    """趋势分析结果"""

    metric_name: str
    data_points: List[TrendDataPoint] = field(default_factory=list)

    @property
    def latest_value(self) -> float:
        if not self.data_points:
            return 0.0
        return self.data_points[-1].value

    @property
    def trend_direction(self) -> str:
        """趋势方向: improving, declining, stable"""
        if len(self.data_points) < 2:
            return "stable"
        recent = self.data_points[-1].value
        previous = self.data_points[-2].value
        diff = recent - previous
        if abs(diff) < 0.5:
            return "stable"
        return "improving" if diff > 0 else "declining"

    @property
    def change_rate(self) -> float:
        """变化率"""
        if len(self.data_points) < 2 or self.data_points[-2].value == 0:
            return 0.0
        recent = self.data_points[-1].value
        previous = self.data_points[-2].value
        return round(((recent - previous) / previous) * 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "latest_value": self.latest_value,
            "trend_direction": self.trend_direction,
            "change_rate": self.change_rate,
            "data_points": [d.to_dict() for d in self.data_points],
        }


@dataclass
class ComparisonResult:
    """报告对比结果"""

    metric_name: str
    before_value: float
    after_value: float

    @property
    def absolute_change(self) -> float:
        return round(self.after_value - self.before_value, 2)

    @property
    def relative_change(self) -> float:
        if self.before_value == 0:
            return 0.0
        return round(((self.after_value - self.before_value) / abs(self.before_value)) * 100, 1)

    @property
    def is_improved(self) -> bool:
        return self.after_value > self.before_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "absolute_change": self.absolute_change,
            "relative_change": self.relative_change,
            "is_improved": self.is_improved,
        }


class HistoryManager:
    """历史数据管理"""

    def __init__(self, history_dir: str = ".analysis_history"):
        self.history_dir = Path(history_dir)
        self.logger = logging.getLogger("ai-analyze.history")

    def save_report(self, project_name: str, report_data: Dict[str, Any]) -> str:
        """保存报告到历史"""
        self.history_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{project_name}_{timestamp}.json"
        filepath = self.history_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        self.logger.info("Report saved: %s", filepath)
        return str(filepath)

    def load_history(self, project_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """加载历史报告"""
        if not self.history_dir.exists():
            return []

        files = sorted(
            self.history_dir.glob(f"{project_name}_*.json"),
            reverse=True,
        )
        reports = []
        for filepath in files[:limit]:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    reports.append(json.load(f))
            except (json.JSONDecodeError, OSError) as e:
                self.logger.warning("Failed to load %s: %s", filepath, e)

        return reports

    def analyze_trend(self, project_name: str, metric_path: str, limit: int = 10) -> TrendAnalysis:
        """分析指标趋势

        Args:
            project_name: 项目名
            metric_path: 指标路径，如 "quality_scores.overall_score"
            limit: 历史记录数
        """
        reports = self.load_history(project_name, limit)
        data_points: List[TrendDataPoint] = []

        for report in reports:
            value = self._extract_metric(report, metric_path)
            timestamp = report.get("timestamp", report.get("analysis_date", ""))
            if value is not None:
                data_points.append(
                    TrendDataPoint(
                        timestamp=timestamp,
                        value=float(value),
                        label=timestamp[:10] if timestamp else "",
                    )
                )

        return TrendAnalysis(
            metric_name=metric_path,
            data_points=data_points,
        )

    def _extract_metric(self, data: Dict[str, Any], path: str) -> Any:
        """从嵌套字典中提取指标值"""
        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current


class ReportComparator:
    """报告对比器"""

    @staticmethod
    def compare(
        before: Dict[str, Any],
        after: Dict[str, Any],
        metric_paths: Optional[List[str]] = None,
    ) -> List[ComparisonResult]:
        """对比两个报告

        Args:
            before: 之前的报告数据
            after: 之后的报告数据
            metric_paths: 要对比的指标路径列表
        """
        if metric_paths is None:
            metric_paths = [
                "quality_scores.overall_score",
                "quality_scores.complexity_score",
                "quality_scores.maintainability_score",
                "quality_scores.reliability_score",
                "total_files",
                "total_lines",
            ]

        results = []
        for path in metric_paths:
            before_val = ReportComparator._extract(before, path)
            after_val = ReportComparator._extract(after, path)
            if before_val is not None and after_val is not None:
                results.append(
                    ComparisonResult(
                        metric_name=path,
                        before_value=float(before_val),
                        after_value=float(after_val),
                    )
                )

        return results

    @staticmethod
    def _extract(data: Dict[str, Any], path: str) -> Any:
        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current


class HTMLReportGenerator:
    """HTML 交互式报告生成器"""

    def __init__(self, output_dir: str = ".reports"):
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger("ai-analyze.html_report")

    def generate(
        self,
        report_data: Dict[str, Any],
        project_name: str = "project",
        include_charts: bool = True,
    ) -> str:
        """生成 HTML 报告"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{project_name}_{timestamp}.html"
        filepath = self.output_dir / filename

        html = self._build_html(report_data, project_name, include_charts)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        self.logger.info("HTML report generated: %s", filepath)
        return str(filepath)

    def _build_html(
        self,
        data: Dict[str, Any],
        project_name: str,
        include_charts: bool,
    ) -> str:
        """构建 HTML 内容"""
        title = f"AI-Analyze Report - {project_name}"
        timestamp = data.get("timestamp", datetime.now().isoformat())

        # 摘要卡片
        summary_cards = self._build_summary_cards(data)

        # 详情区域
        details = self._build_details(data)

        # 图表脚本
        charts_script = self._build_charts_script(data) if include_charts else ""

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, sans-serif; background: #f5f5f5; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ text-align: center; padding: 20px 0; color: #2c3e50; }}
        .timestamp {{ text-align: center; color: #7f8c8d; margin-bottom: 20px; }}
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                  gap: 16px; margin-bottom: 30px; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card h3 {{ color: #2c3e50; margin-bottom: 10px; }}
        .card .value {{ font-size: 2em; font-weight: bold; color: #3498db; }}
        .card .label {{ color: #7f8c8d; margin-top: 5px; }}
        .section {{ background: white; border-radius: 8px; padding: 20px;
                   margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #2c3e50; margin-bottom: 15px; border-bottom: 2px solid #3498db; padding-bottom: 8px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; color: #2c3e50; }}
        .severity-critical {{ color: #e74c3c; font-weight: bold; }}
        .severity-high {{ color: #e67e22; font-weight: bold; }}
        .severity-medium {{ color: #f39c12; }}
        .severity-low {{ color: #27ae60; }}
        .chart-container {{ width: 100%; height: 300px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="timestamp">Generated: {timestamp}</div>
        <div class="cards">{summary_cards}</div>
        {details}
    </div>
    {charts_script}
</body>
</html>"""

    def _build_summary_cards(self, data: Dict[str, Any]) -> str:
        """构建摘要卡片"""
        cards = []
        quality = data.get("quality_scores", {})
        if quality:
            overall = quality.get("overall_score", "N/A")
            cards.append(
                f'<div class="card"><h3>Overall Score</h3>'
                f'<div class="value">{overall}</div>'
                f'<div class="label">Quality Score</div></div>'
            )

        security = data.get("security_scan", {})
        if security:
            risk = security.get("risk_score", "N/A")
            cards.append(
                f'<div class="card"><h3>Risk Score</h3>'
                f'<div class="value">{risk}</div>'
                f'<div class="label">Security Risk</div></div>'
            )

        perf = data.get("performance_analysis", {})
        if perf:
            ps = perf.get("performance_score", "N/A")
            cards.append(
                f'<div class="card"><h3>Performance</h3>'
                f'<div class="value">{ps}</div>'
                f'<div class="label">Performance Score</div></div>'
            )

        debt = data.get("tech_debt", {})
        if debt:
            ds = debt.get("debt_score", "N/A")
            cards.append(
                f'<div class="card"><h3>Tech Debt</h3>'
                f'<div class="value">{ds}</div>'
                f'<div class="label">Debt Score (lower is better)</div></div>'
            )

        return "\n".join(cards)

    def _build_details(self, data: Dict[str, Any]) -> str:
        """构建详情区域"""
        sections = []

        # 安全发现
        findings = data.get("security_scan", {}).get("findings", [])
        if findings:
            rows = ""
            for f in findings[:20]:
                sev = f.get("severity", "low")
                rows += (
                    f'<tr><td class="severity-{sev}">{sev}</td>'
                    f'<td>{f.get("rule_name", "")}</td>'
                    f'<td>{f.get("file_path", "")}:{f.get("line_number", "")}</td>'
                    f'<td>{f.get("description", "")}</td></tr>'
                )
            sections.append(
                f'<div class="section"><h2>Security Findings</h2>'
                f"<table><tr><th>Severity</th><th>Rule</th>"
                f"<th>Location</th><th>Description</th></tr>"
                f"{rows}</table></div>"
            )

        # 性能问题
        issues = data.get("performance_analysis", {}).get("issues", [])
        if issues:
            rows = ""
            for i in issues[:20]:
                impact = i.get("impact", "low")
                rows += (
                    f'<tr><td class="severity-{impact}">{impact}</td>'
                    f'<td>{i.get("name", "")}</td>'
                    f'<td>{i.get("file_path", "")}:{i.get("line_number", "")}</td>'
                    f'<td>{i.get("suggestion", "")}</td></tr>'
                )
            sections.append(
                f'<div class="section"><h2>Performance Issues</h2>'
                f"<table><tr><th>Impact</th><th>Name</th>"
                f"<th>Location</th><th>Suggestion</th></tr>"
                f"{rows}</table></div>"
            )

        return "\n".join(sections)

    def _build_charts_script(self, data: Dict[str, Any]) -> str:
        """构建 Chart.js 图表脚本"""
        charts = []

        # 安全评分雷达图
        security = data.get("security_scan", {})
        if security:
            charts.append(
                self._build_radar_chart(
                    "securityChart",
                    "Security Risk",
                    ["Injection", "Sensitive Data", "Misconfig", "Crypto", "Input Validation", "Error Handling"],
                    [
                        security.get("injection_count", security.get("critical_count", 0)),
                        security.get("sensitive_count", security.get("high_count", 0)),
                        security.get("misconfig_count", security.get("medium_count", 0)),
                        security.get("crypto_count", security.get("low_count", 0)),
                        0,
                        0,
                    ],
                )
            )

        # 性能评分柱状图
        perf = data.get("performance_analysis", {})
        if perf:
            by_cat = perf.get("by_category", {})
            if by_cat:
                charts.append(
                    self._build_bar_chart(
                        "performanceChart",
                        "Performance Issues by Category",
                        list(by_cat.keys()),
                        list(by_cat.values()),
                    )
                )

        if not charts:
            return ""

        chart_divs = "\n".join(
            f'<div class="section"><h2>Charts</h2>' f'<canvas id="{cid}" ' f'class="chart-container"></canvas></div>'
            for cid, _ in charts
        )
        chart_scripts = "\n".join(script for _, script in charts)

        return (
            '<script src="https://cdn.jsdelivr.net/npm/chart.js">'
            "</script>"
            f"{chart_divs}"
            f"<script>{chart_scripts}</script>"
        )

    @staticmethod
    def _build_radar_chart(
        canvas_id: str,
        title: str,
        labels: List[str],
        values: List[Any],
    ) -> tuple:
        """构建雷达图"""
        script = f"""
        new Chart(document.getElementById('{canvas_id}'), {{
            type: 'radar',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [{{ label: '{title}', data: {json.dumps(values)},
                    backgroundColor: 'rgba(52,152,219,0.2)',
                    borderColor: 'rgba(52,152,219,1)' }}]
            }}
        }});"""
        return (canvas_id, script)

    @staticmethod
    def _build_bar_chart(
        canvas_id: str,
        title: str,
        labels: List[str],
        values: List[Any],
    ) -> tuple:
        """构建柱状图"""
        script = f"""
        new Chart(document.getElementById('{canvas_id}'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [{{ label: '{title}', data: {json.dumps(values)},
                    backgroundColor: 'rgba(46,204,113,0.6)' }}]
            }}
        }});"""
        return (canvas_id, script)
