#!/usr/bin/env python3
"""
AST 分析集成模块
将 AST 分析集成到完整分析流程中
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ast_analyzer_tool import ASTAnalysisTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ASTIntegration:
    """AST 分析集成器"""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.ast_tool = ASTAnalysisTool(project_path)

    def run_ast_analysis(self, output_dir: str = 'reports') -> Dict[str, Any]:
        """运行 AST 分析"""
        logger.info("🔍 步骤 1/3: 运行 AST 代码分析...")

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 生成 JSON 报告
        json_report = self.ast_tool.generate_report(
            str(output_path / f"ast_analysis.json")
        )

        # 生成 Markdown 报告
        md_report = self.ast_tool.generate_markdown_report(
            str(output_path / f"ast_analysis.md")
        )

        logger.info(f"✅ AST 分析完成")
        logger.info(f"   JSON 报告: {json_report}")
        logger.info(f"   Markdown 报告: {md_report}")

        # 读取 JSON 报告
        with open(json_report, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)

        return analysis_data

    def merge_with_serena_analysis(
        self,
        serena_report: Dict[str, Any],
        ast_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """将 AST 分析结果与 Serena 分析结果合并"""
        logger.info("🔗 合并 AST 和 Serena 分析结果...")

        merged = {
            **serena_report,
            'ast_analysis': ast_analysis,
            'combined_metrics': self._calculate_combined_metrics(serena_report, ast_analysis)
        }

        return merged

    def _calculate_combined_metrics(
        self,
        serena_report: Dict[str, Any],
        ast_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算合并后的指标"""
        ast_summary = ast_analysis.get('summary', {})

        return {
            'total_files': ast_summary.get('total_files', 0),
            'total_functions': ast_summary.get('total_functions', 0),
            'total_classes': ast_summary.get('total_classes', 0),
            'total_code_smells': ast_summary.get('total_code_smells', 0),
            'average_complexity': ast_summary.get('average_complexity', 0),
            'languages': ast_summary.get('languages', {}),
        }

    def generate_combined_report(
        self,
        serena_report: Dict[str, Any],
        ast_analysis: Dict[str, Any],
        output_path: str = 'reports/combined_analysis.md'
    ) -> str:
        """生成合并的分析报告"""
        logger.info("📝 生成合并分析报告...")

        md_content = self._build_combined_markdown(serena_report, ast_analysis)

        output_file = Path(output_path)
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(f"✅ 合并报告已生成: {output_path}")
        return output_path

    def _build_combined_markdown(
        self,
        serena_report: Dict[str, Any],
        ast_analysis: Dict[str, Any]
    ) -> str:
        """构建合并的 Markdown 报告"""
        md = "# 📊 完整代码分析报告\n\n"
        md += "## 🎯 执行摘要\n\n"

        ast_summary = ast_analysis.get('summary', {})
        md += f"""
### 代码规模
- **总文件数**: {ast_summary.get('total_files', 0)}
- **总函数数**: {ast_summary.get('total_functions', 0)}
- **总类数**: {ast_summary.get('total_classes', 0)}
- **平均圈复杂度**: {ast_summary.get('average_complexity', 0):.2f}

### 代码质量
- **代码坏味道数**: {ast_summary.get('total_code_smells', 0)}
- **语言分布**: {len(ast_summary.get('languages', {}))} 种

"""

        # 添加 AST 分析详情
        md += "## 🔍 AST 分析详情\n\n"
        md += "### 语言分布\n\n"
        md += "| 语言 | 文件数 | 函数数 | 类数 |\n"
        md += "|------|--------|--------|------|\n"

        for lang, stats in ast_summary.get('languages', {}).items():
            md += f"| {lang} | {stats['files']} | {stats['functions']} | {stats['classes']} |\n"

        # 添加代码坏味道统计
        md += "\n### 代码坏味道统计\n\n"

        smell_stats = {}
        for file_info in ast_analysis.get('files', []):
            for smell in file_info.get('code_smells', []):
                smell_name = smell['name']
                if smell_name not in smell_stats:
                    smell_stats[smell_name] = {'count': 0, 'severity': smell['severity']}
                smell_stats[smell_name]['count'] += 1

        if smell_stats:
            md += "| 坏味道类型 | 数量 | 严重程度 |\n"
            md += "|-----------|------|----------|\n"
            for smell_name, stats in sorted(smell_stats.items(), key=lambda x: x[1]['count'], reverse=True):
                severity_emoji = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🔴',
                    'critical': '⛔'
                }.get(stats['severity'], '❓')
                md += f"| {smell_name} | {stats['count']} | {severity_emoji} {stats['severity']} |\n"
        else:
            md += "未检测到代码坏味道\n"

        # 添加复杂度最高的文件
        md += "\n### 复杂度最高的文件\n\n"

        files_by_complexity = sorted(
            ast_analysis.get('files', []),
            key=lambda x: x['overall_complexity']['cyclomatic'],
            reverse=True
        )[:5]

        if files_by_complexity:
            md += "| 文件 | 圈复杂度 | 代码行数 |\n"
            md += "|------|----------|----------|\n"
            for file_info in files_by_complexity:
                md += f"| {file_info['file_path']} | {file_info['overall_complexity']['cyclomatic']} | {file_info['overall_complexity']['lines_of_code']} |\n"

        # 添加最长的函数
        md += "\n### 最长的函数\n\n"

        all_functions = []
        for file_info in ast_analysis.get('files', []):
            for func in file_info.get('functions', []):
                all_functions.append({
                    'file': file_info['file_path'],
                    'name': func['name'],
                    'lines': func['line_end'] - func['line_start'] + 1,
                    'complexity': func['complexity']['cyclomatic']
                })

        longest_functions = sorted(all_functions, key=lambda x: x['lines'], reverse=True)[:5]

        if longest_functions:
            md += "| 文件 | 函数 | 行数 | 圈复杂度 |\n"
            md += "|------|------|------|----------|\n"
            for func in longest_functions:
                md += f"| {func['file']} | {func['name']} | {func['lines']} | {func['complexity']} |\n"

        # 添加改进建议
        md += "\n## 💡 改进建议\n\n"

        suggestions = []

        # 基于代码坏味道的建议
        if ast_summary.get('total_code_smells', 0) > 0:
            suggestions.append(f"- 检测到 {ast_summary['total_code_smells']} 个代码坏味道，建议逐一修复")

        # 基于复杂度的建议
        avg_complexity = ast_summary.get('average_complexity', 0)
        if avg_complexity > 10:
            suggestions.append(f"- 平均圈复杂度为 {avg_complexity:.2f}，建议重构复杂函数")

        # 基于文件数的建议
        total_files = ast_summary.get('total_files', 0)
        if total_files > 100:
            suggestions.append(f"- 项目包含 {total_files} 个文件，建议考虑模块化重构")

        if suggestions:
            for suggestion in suggestions:
                md += suggestion + "\n"
        else:
            md += "- 代码质量良好，继续保持\n"

        return md


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='AST 分析集成工具')
    parser.add_argument('project_path', help='项目路径')
    parser.add_argument('--output-dir', default='reports', help='输出目录')

    args = parser.parse_args()

    integration = ASTIntegration(args.project_path)

    # 运行 AST 分析
    ast_analysis = integration.run_ast_analysis(args.output_dir)

    # 生成报告
    integration.generate_combined_report(
        {},
        ast_analysis,
        f"{args.output_dir}/combined_analysis.md"
    )

    print("✅ AST 分析完成")


if __name__ == '__main__':
    main()
