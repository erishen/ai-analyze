#!/usr/bin/env python3
"""
AST 分析工具
集成 AST 分析到完整分析流程中
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import logging

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzers.ast_analyzer import (  # noqa: E402
    ASTAnalyzerFactory,
    detect_language,
    FileAnalysisResult,
)
from src.reports.ast_visualizer import ASTVisualizer  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ASTAnalysisTool:
    """AST 分析工具"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)

    def analyze_project(self, file_patterns: List[str] = None) -> Dict[str, Any]:
        """分析整个项目"""
        from datetime import datetime

        if file_patterns is None:
            file_patterns = ['**/*.py', '**/*.js', '**/*.ts', '**/*.tsx', '**/*.jsx']

        now = datetime.now()
        results = {
            'project_path': str(self.project_path),
            'timestamp': now.isoformat(),
            'analysis_date': now.strftime('%Y-%m-%d %H:%M:%S'),
            'files': [],
            'summary': {
                'total_files': 0,
                'total_functions': 0,
                'total_classes': 0,
                'total_code_smells': 0,
                'average_complexity': 0,
                'languages': {}
            }
        }

        files_to_analyze = []
        for pattern in file_patterns:
            files_to_analyze.extend(self.project_path.glob(pattern))

        # 去重
        files_to_analyze = list(set(files_to_analyze))

        total_complexity = 0
        language_stats = {}

        for file_path in files_to_analyze:
            if file_path.is_file():
                try:
                    file_result = self.analyze_file(str(file_path))
                    if file_result:
                        results['files'].append(self._serialize_result(file_result))
                        results['summary']['total_files'] += 1
                        results['summary']['total_functions'] += len(file_result.functions)
                        results['summary']['total_classes'] += len(file_result.classes)
                        results['summary']['total_code_smells'] += len(file_result.code_smells)
                        total_complexity += file_result.overall_complexity.cyclomatic_complexity

                        # 统计语言
                        lang = file_result.language
                        if lang not in language_stats:
                            language_stats[lang] = {'files': 0, 'functions': 0, 'classes': 0}
                        language_stats[lang]['files'] += 1
                        language_stats[lang]['functions'] += len(file_result.functions)
                        language_stats[lang]['classes'] += len(file_result.classes)

                except Exception as e:
                    logger.error(f"Failed to analyze {file_path}: {e}")

        if results['summary']['total_files'] > 0:
            results['summary']['average_complexity'] = total_complexity / results['summary']['total_files']

        results['summary']['languages'] = language_stats

        return results

    def analyze_file(self, file_path: str) -> FileAnalysisResult:
        """分析单个文件"""
        language = detect_language(file_path)
        if not language:
            logger.warning(f"Unknown language for {file_path}")
            return None

        analyzer = ASTAnalyzerFactory.create_analyzer(language)
        return analyzer.analyze_file(file_path)

    def _serialize_result(self, result: FileAnalysisResult) -> Dict[str, Any]:
        """序列化分析结果"""
        return {
            'file_path': result.file_path,
            'language': result.language,
            'total_lines': result.total_lines,
            'functions': [
                {
                    'name': f.name,
                    'line_start': f.line_start,
                    'line_end': f.line_end,
                    'complexity': {
                        'cyclomatic': f.complexity.cyclomatic_complexity,
                        'cognitive': f.complexity.cognitive_complexity,
                        'nesting_depth': f.complexity.nesting_depth,
                        'lines_of_code': f.complexity.lines_of_code,
                    },
                    'parameters': f.parameters,
                    'is_async': f.is_async,
                    'is_static': f.is_static,
                    'code_smells': [
                        {
                            'name': smell.name,
                            'severity': smell.severity,
                            'description': smell.description,
                            'suggestion': smell.suggestion,
                        }
                        for smell in f.code_smells
                    ]
                }
                for f in result.functions
            ],
            'classes': [
                {
                    'name': c.name,
                    'line_start': c.line_start,
                    'line_end': c.line_end,
                    'methods_count': len(c.methods),
                    'inheritance_depth': c.inheritance_depth,
                    'code_smells': [
                        {
                            'name': smell.name,
                            'severity': smell.severity,
                            'description': smell.description,
                        }
                        for smell in c.code_smells
                    ]
                }
                for c in result.classes
            ],
            'imports': result.imports,
            'code_smells': [
                {
                    'name': smell.name,
                    'severity': smell.severity,
                    'location': smell.location,
                    'description': smell.description,
                    'suggestion': smell.suggestion,
                }
                for smell in result.code_smells
            ],
            'overall_complexity': {
                'cyclomatic': result.overall_complexity.cyclomatic_complexity,
                'cognitive': result.overall_complexity.cognitive_complexity,
                'lines_of_code': result.overall_complexity.lines_of_code,
                'comment_lines': result.overall_complexity.comment_lines,
                'blank_lines': result.overall_complexity.blank_lines,
            }
        }

    def generate_report(self, output_path: str = None) -> str:
        """生成 AST 分析报告"""
        from datetime import datetime

        results = self.analyze_project()

        # 添加时间戳和日期
        now = datetime.now()
        results['timestamp'] = now.isoformat()
        results['analysis_date'] = now.strftime('%Y-%m-%d %H:%M:%S')

        if output_path is None:
            # 从项目路径提取项目名
            project_name = self.project_path.name or "project"
            timestamp = now.strftime('%Y%m%d_%H%M%S')
            reports_dir = Path(__file__).resolve().parent.parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            output_path = str(reports_dir / f"ast_analysis_{project_name}_{timestamp}.json")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"AST analysis report saved to {output_path}")
        return output_path

    def generate_markdown_report(self, output_path: str = None) -> str:
        """生成 Markdown 格式的 AST 分析报告"""
        from datetime import datetime

        results = self.analyze_project()

        if output_path is None:
            # 从项目路径提取项目名
            project_name = self.project_path.name or "project"
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            reports_dir = Path(__file__).resolve().parent.parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            output_path = str(reports_dir / f"ast_analysis_{project_name}_{timestamp}.md")

        md_content = self._build_markdown_report(results)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(f"AST analysis markdown report saved to {output_path}")
        return output_path

    def generate_visualization(
        self,
        output_dir: str = None,
        formats: List[str] = None,
    ) -> Dict[str, str]:
        """
        生成 AST 可视化报告

        Args:
            output_dir: 输出目录
            formats: 输出格式列表 ['html', 'json']

        Returns:
            生成的文件路径字典
        """
        if output_dir is None:
            output_dir = str(self.project_path / 'ast_visualizations')
        if formats is None:
            formats = ['html', 'json']

        visualizer = ASTVisualizer(output_dir=output_dir)
        results = self.analyze_project()
        generated_files = {}

        # 收集所有 FileAnalysisResult 对象
        file_results = []
        for file_path_str in [f['file_path'] for f in results['files']]:
            try:
                file_result = self.analyze_file(file_path_str)
                if file_result:
                    file_results.append(file_result)
            except Exception as e:
                logger.error(f"Failed to re-analyze {file_path_str}: {e}")

        for fr in file_results:
            for fmt in formats:
                filepath = visualizer.visualize_tree(fr, output_format=fmt)
                generated_files[f"tree_{Path(fr.file_path).stem}_{fmt}"] = filepath

        # 生成热力图
        if file_results:
            for fmt in formats:
                filepath = visualizer.visualize_complexity_heatmap(file_results, output_format=fmt)
                generated_files[f"heatmap_{fmt}"] = filepath

        logger.info(f"Generated {len(generated_files)} visualization files in {output_dir}")
        return generated_files

    def _build_markdown_report(self, results: Dict[str, Any]) -> str:
        """构建 Markdown 报告内容"""
        summary = results['summary']

        md = """# AST 代码分析报告

## 📊 项目概览

- **项目路径**: {results['project_path']}
- **分析文件数**: {summary['total_files']}
- **总函数数**: {summary['total_functions']}
- **总类数**: {summary['total_classes']}
- **代码坏味道数**: {summary['total_code_smells']}
- **平均圈复杂度**: {summary['average_complexity']:.2f}

## 📈 语言分布

| 语言 | 文件数 | 函数数 | 类数 |
|------|--------|--------|------|
"""

        for lang, stats in summary['languages'].items():
            md += f"| {lang} | {stats['files']} | {stats['functions']} | {stats['classes']} |\n"

        md += "\n## 🔍 文件详情\n\n"

        for file_info in results['files']:
            md += f"### {file_info['file_path']}\n\n"
            md += f"- **语言**: {file_info['language']}\n"
            md += f"- **总行数**: {file_info['total_lines']}\n"
            md += f"- **代码行数**: {file_info['overall_complexity']['lines_of_code']}\n"
            md += f"- **注释行数**: {file_info['overall_complexity']['comment_lines']}\n"
            md += f"- **圈复杂度**: {file_info['overall_complexity']['cyclomatic']}\n"

            if file_info['functions']:
                md += f"\n#### 函数列表 ({len(file_info['functions'])})\n\n"
                for func in file_info['functions']:
                    md += f"- **{func['name']}** (行 {func['line_start']}-{func['line_end']})\n"
                    md += f"  - 圈复杂度: {func['complexity']['cyclomatic']}\n"
                    md += f"  - 参数数: {len(func['parameters'])}\n"
                    if func['is_async']:
                        md += "  - 异步函数\n"

            if file_info['classes']:
                md += f"\n#### 类列表 ({len(file_info['classes'])})\n\n"
                for cls in file_info['classes']:
                    md += f"- **{cls['name']}** (行 {cls['line_start']}-{cls['line_end']})\n"
                    md += f"  - 方法数: {cls['methods_count']}\n"
                    md += f"  - 继承深度: {cls['inheritance_depth']}\n"

            if file_info['code_smells']:
                md += f"\n#### 代码坏味道 ({len(file_info['code_smells'])})\n\n"
                for smell in file_info['code_smells']:
                    severity_emoji = {
                        'low': '🟢',
                        'medium': '🟡',
                        'high': '🔴',
                        'critical': '⛔'
                    }.get(smell['severity'], '❓')
                    md += f"- {severity_emoji} **{smell['name']}** ({smell['severity']})\n"
                    md += f"  - {smell['description']}\n"
                    if 'suggestion' in smell:
                        md += f"  - 建议: {smell['suggestion']}\n"

            md += "\n"

        return md


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='AST 代码分析工具')
    parser.add_argument('project_path', help='项目路径')
    parser.add_argument('--format', choices=['json', 'markdown', 'visualize'], default='json',
                        help='输出格式 (默认: json)')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--patterns', nargs='+', help='文件匹配模式')
    parser.add_argument('--viz-formats', nargs='+', default=['html', 'json'],
                        help='可视化输出格式 (默认: html json)')

    args = parser.parse_args()

    tool = ASTAnalysisTool(args.project_path)

    if args.format == 'visualize':
        files = tool.generate_visualization(formats=args.viz_formats)
        for name, path in files.items():
            print(f"  {name}: {path}")
        print(f"✅ 可视化完成: {len(files)} files generated")
    elif args.format == 'markdown':
        output_path = tool.generate_markdown_report(args.output)
        print(f"✅ 分析完成: {output_path}")
    else:
        output_path = tool.generate_report(args.output)
        print(f"✅ 分析完成: {output_path}")


if __name__ == '__main__':
    main()
