#!/usr/bin/env python3
"""
一键分析目标项目（多语言增强版，支持自然语言报告）
自动读取 .env 中的 PROJECT_PATH 和 SERENA_DIR，启动 MCP 服务器并执行分析。
支持 Python、JavaScript、TypeScript、Java、Go、Rust、C/C++ 等多种语言。
可选择生成 JSON 或人话报告。
"""

import os
import sys
import json
import argparse
import asyncio
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# 加载 .env 环境变量（从项目根目录）
def load_env():
    # 获取项目根目录（tools/ 的上级目录）
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

load_env()

# 将脚本所在项目的根目录添加到 Python 路径，确保可以导入 src 模块
# （需要在切换工作目录之前完成）
script_dir = Path(__file__).parent
ai_analyze_root = script_dir.parent
if str(ai_analyze_root) not in sys.path:
    sys.path.insert(0, str(ai_analyze_root))

PROJECT_PATH = os.getenv('PROJECT_PATH')
if not PROJECT_PATH:
    PROJECT_PATH = os.getcwd()
else:
    # 展开 ~ 为实际的家目录路径
    PROJECT_PATH = os.path.expanduser(PROJECT_PATH)

# 切换到项目目录
os.chdir(PROJECT_PATH)

# 多语言配置
LANGUAGES_CONFIG = {
    'python': {
        'extensions': ['.py'],
        'patterns': ['*.py'],
        'symbol_patterns': {
            'class': 'class ',
            'function': 'def ',
            'import': '^import |^from '
        },
        'description': 'Python'
    },
    'javascript': {
        'extensions': ['.js', '.jsx'],
        'patterns': ['*.js', '*.jsx'],
        'symbol_patterns': {
            'class': 'class ',
            'function': 'function |const |let |var ',
            'import': 'import |require('
        },
        'description': 'JavaScript'
    },
    'typescript': {
        'extensions': ['.ts', '.tsx'],
        'patterns': ['*.ts', '*.tsx'],
        'symbol_patterns': {
            'class': 'class ',
            'function': 'function |const |let |var ',
            'import': 'import |require('
        },
        'description': 'TypeScript'
    },
    'java': {
        'extensions': ['.java'],
        'patterns': ['*.java'],
        'symbol_patterns': {
            'class': '(public |private |protected )?class ',
            'function': '(public |private |protected ).*(',
            'import': 'import '
        },
        'description': 'Java'
    },
    'go': {
        'extensions': ['.go'],
        'patterns': ['*.go'],
        'symbol_patterns': {
            'class': 'type .* struct',
            'function': 'func ',
            'import': 'import '
        },
        'description': 'Go'
    },
    'rust': {
        'extensions': ['.rs'],
        'patterns': ['*.rs'],
        'symbol_patterns': {
            'class': 'struct |enum |trait ',
            'function': 'fn ',
            'import': 'use |extern '
        },
        'description': 'Rust'
    },
    'cpp': {
        'extensions': ['.cpp', '.cc', '.cxx', '.h', '.hpp'],
        'patterns': ['*.cpp', '*.cc', '*.cxx', '*.h', '.hpp'],
        'symbol_patterns': {
            'class': 'class ',
            'function': '(void|int|string|bool|float|double|char)s+w+s*(',
            'import': '#include '
        },
        'description': 'C/C++'
    }
}

# 导入 Serena 客户端
from src.serena_stdio_client import SerenaStdioClient

async def extract_file_paths(find_result):
    """从 find_file 结果中提取文件路径列表"""
    if isinstance(find_result, list):
        return find_result
    elif isinstance(find_result, dict):
        if 'files' in find_result:
            return find_result['files']
        elif 'matches' in find_result:
            return list(find_result['matches'].keys())
        elif 'results' in find_result:
            return find_result['results']
        elif 'data' in find_result and isinstance(find_result['data'], list):
            return find_result['data']
        else:
            for key in ['files', 'matches', 'results', 'data', 'items']:
                if key in find_result and isinstance(find_result[key], (list, dict)):
                    if isinstance(find_result[key], list):
                        return find_result[key]
                    else:
                        return list(find_result[key].keys()) if isinstance(find_result[key], dict) else []
            return list(find_result.keys())
    else:
        print(f"警告: find_file 返回未知类型: {type(find_result)}, 值: {find_result}")
        return []

async def safe_extract_symbols(client, file, symbol_types):
    """安全地从符号数据中提取类和函数"""
    try:
        overview = await client.get_symbols_overview(file)
        if not overview or not isinstance(overview, dict):
            return [], [], []
        
        classes = overview.get('classes', []) or \
                  overview.get('Classes', []) or \
                  overview.get('class', []) or \
                  []
        
        functions = overview.get('functions', []) or \
                    overview.get('Functions', []) or \
                    overview.get('function', []) or \
                    overview.get('defs', []) or \
                    []
        
        variables = overview.get('variables', []) or \
                    overview.get('Variables', []) or \
                    overview.get('variable', []) or \
                    []
        
        return classes, functions, variables
    except Exception as e:
        print(f"      ⚠️ 符号提取失败 {file}: {str(e)}")
        return [], [], []

async def detect_project_languages(file_paths):
    """检测项目中使用的编程语言"""
    lang_stats = defaultdict(int)
    lang_files = defaultdict(list)
    
    for file_path in file_paths:
        ext = Path(file_path).suffix.lower()
        for lang, config in LANGUAGES_CONFIG.items():
            if ext in config['extensions']:
                lang_stats[lang] += 1
                lang_files[lang].append(file_path)
                break
    
    return dict(lang_stats), dict(lang_files)

async def find_files_by_language(client, language):
    """按语言查找文件"""
    if language not in LANGUAGES_CONFIG:
        return []
    
    patterns = LANGUAGES_CONFIG[language]['patterns']
    all_files = []
    
    for pattern in patterns:
        try:
            result = await client.find_file(pattern)
            files = await extract_file_paths(result)
            all_files.extend(files)
        except Exception as e:
            print(f"警告: 查找 {language} 文件时出错 ({pattern}): {e}")
    
    return all_files

async def main():
    from collections import defaultdict
    
    parser = argparse.ArgumentParser(description='分析项目并生成报告')
    parser.add_argument('--format', choices=['json', 'text'], default='text',
                       help='报告格式: json 或 text (默认: text)')
    parser.add_argument('--output', '-o', help='输出文件路径 (可选)')
    parser.add_argument('--languages', nargs='*', 
                       choices=list(LANGUAGES_CONFIG.keys()) + ['all'],
                       default=['all'],
                       help='指定要分析的语言 (默认: all)')
    args = parser.parse_args()
    
    print(f"🔍 开始分析项目: {PROJECT_PATH}\n")

    report = {}

    try:
        async with SerenaStdioClient(project_path=PROJECT_PATH) as client:
            # 1. 列出可用工具
            tools = await client.list_tools()
            report['tools'] = tools

            # 2. 查找所有代码文件
            all_files = []
            languages_to_analyze = args.languages if 'all' not in args.languages else list(LANGUAGES_CONFIG.keys())
            
            print(f"📁 分析语言: {', '.join(languages_to_analyze)}")
            
            for lang in languages_to_analyze:
                if lang in LANGUAGES_CONFIG:
                    lang_files = await find_files_by_language(client, lang)
                    all_files.extend(lang_files)
                    print(f"  {LANGUAGES_CONFIG[lang]['description']}: 找到 {len(lang_files)} 个文件")
            
            # 去重
            all_files = list(set(all_files))
            report['all_files'] = all_files
            
            # 3. 检测项目语言分布
            lang_stats, lang_files = await detect_project_languages(all_files)
            report['language_stats'] = lang_stats
            report['language_files'] = lang_files

            # 4. 按语言分析符号概览 & 代码行数
            symbols_overview = []
            code_line_stats = defaultdict(int)
            print("\n🔍 分析代码符号与行数...")
            
            for lang in languages_to_analyze:
                if lang in lang_files and lang_files[lang]:
                    cfg = LANGUAGES_CONFIG[lang]
                    files_to_process = lang_files[lang]  # 分析所有文件
                    print(f"  {LANGUAGES_CONFIG[lang]['description']}: 分析 {len(files_to_process)} 个文件")
                    lang_classes = []
                    lang_functions = []
                    lang_variables = []
                    
                    for file in files_to_process:
                        try:
                            classes, functions, variables = await safe_extract_symbols(client, file, cfg["symbol_types"])
                            # 重新获取完整概览用于报告
                            overview = await client.get_symbols_overview(file)
                            symbols_overview.append({
                                'file': file, 
                                'language': lang,
                                'symbols': overview,
                                'classes': classes,
                                'functions': functions,
                                'variables': variables
                            })
                            lang_classes.extend(classes)
                            lang_functions.extend(functions)
                            lang_variables.extend(variables)
                            # 精确统计代码行数
                            try:
                                content_res = await client.read_file(file)
                                content_str = str(content_res)
                                lines = content_str.count('\n') + (1 if content_str and not content_str.endswith('\n') else 0)
                            except Exception:
                                lines = 0
                            code_line_stats[lang] += lines
                        except Exception as e:
                            symbols_overview.append({'file': file, 'language': lang, 'error': str(e)})
                    # 汇总该语言
                    report.setdefault('lang_symbols', {})[lang] = {
                        'classes': lang_classes,
                        'functions': lang_functions,
                        'variables': lang_variables,
                        'files_analyzed': len(files_to_process)
                    }
            report['symbols_overview'] = symbols_overview
            report['code_line_stats'] = dict(code_line_stats)

            # 5. 搜索各语言关键模式（最终版：在特定语言文件中搜索）
            print("\n🔎 搜索各语言关键模式...")
            pattern_results = {}
            
            # 简化的模式定义 - 先用基础模式测试
            basic_patterns = {
                'python': {
                    'class': 'class ',
                    'function': 'def ',
                    'import': 'import '
                },
                'javascript': {
                    'class': 'class ',
                    'function': 'function ',
                    'import': 'import '
                },
                'typescript': {
                    'class': 'class ',
                    'function': 'function ',
                    'import': 'import '
                },
                'java': {
                    'class': 'class ',
                    'function': 'public ',
                    'import': 'import '
                },
                'go': {
                    'class': 'type.*struct',
                    'function': 'func ',
                    'import': 'import '
                },
                'rust': {
                    'class': 'struct ',
                    'function': 'fn ',
                    'import': 'use '
                },
                'cpp': {
                    'class': 'class ',
                    'function': '(void|int|string|bool|float|double|char) s+ w+ s*(',
                    'import': '#include '
                }
            }
            
            # 为每种语言在其自己的文件中搜索
            for lang in languages_to_analyze:
                if lang not in lang_files or not lang_files[lang]:
                    print(f"  {LANGUAGES_CONFIG[lang]['description']}: 无文件可分析")
                    continue
                    
                print(f"  {LANGUAGES_CONFIG[lang]['description']}:")
                lang_patterns = []
                conf = LANGUAGES_CONFIG[lang]
                patterns = basic_patterns.get(lang, conf.get('symbol_patterns', {}))
                
                for kind, pat in patterns.items():
                    lang_patterns.append({'lang': lang, 'kind': kind, 'pattern': pat, 'desc': f'{conf["description"]} {kind}'})
                
                # 在该语言的文件中搜索
                for p in lang_patterns:
                    try:
                        total_matches = 0
                        # 限制搜索范围到该语言的文件
                        for file_path in lang_files[lang][:10]:  # 限制文件数量避免过慢
                            try:
                                res = await client.search_for_pattern(p['pattern'], relative_path=file_path)
                                # 统计匹配数量
                                if isinstance(res, list):
                                    total_matches += len(res)
                                elif isinstance(res, dict):
                                    for k, v in res.items():
                                        if isinstance(v, list):
                                            total_matches += len(v)
                                            break
                            except Exception as file_e:
                                if file_path == lang_files[lang][0]:
                                    print(f"      ERROR 文件 {file_path} 搜索出错: {file_e}")

                        pattern_results[f"{p['lang']}_{p['kind']}"] = {
                            'lang': p['lang'],
                            'kind': p['kind'],
                            'desc': p['desc'],
                            'match_count': total_matches,
                            'files_searched': min(len(lang_files[lang]), 10)
                        }

                        if total_matches > 0:
                            print(f"    {p['desc']}: 找到 {total_matches} 个匹配")
                        else:
                            print(f"    {p['desc']}: 未找到匹配")
                    except Exception as e:
                        pattern_results[f"{p['lang']}_{p['kind']}"] = {
                            'lang': p['lang'], 
                            'kind': p['kind'], 
                            'desc': p['desc'], 
                            'error': str(e),
                            'match_count': 0
                        }
                        print(f"    {p['desc']}: 搜索出错 - {e}")
            
            report['pattern_search'] = pattern_results

            # 6. 查找配置文件
            try:
                config_files_result = await client.find_file('*config*')
                config_files = await extract_file_paths(config_files_result)
                
                config_symbols = await client.find_symbol('Config')
                workflow = {
                    'config_files': config_files,
                    'config_symbols': config_symbols
                }
                report['workflow'] = workflow
            except Exception as e:
                report['workflow'] = {'error': str(e)}

        # 生成 Markdown 报告
        print("\n📝 生成报告...")
        
        lines = []
        lines.append("# 📊 项目多语言分析报告")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **分析路径**: `{PROJECT_PATH}`")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 项目概况
        lines.append("## 🏗️ 项目概况")
        lines.append("")
        lines.append(f"- **项目路径**: `{PROJECT_PATH}`")
        lines.append(f"- **总文件数**: {len(all_files)} 个代码文件")
        lines.append("")
        
        # 语言分布
        if lang_stats:
            lines.append("## 🌐 编程语言分布")
            lines.append("")
            lines.append("| 语言 | 文件数 | 占比 |")
            lines.append("|:---|:---:|---:|")
            
            total_files = sum(lang_stats.values())
            for lang, count in sorted(lang_stats.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_files * 100) if total_files > 0 else 0
                desc = LANGUAGES_CONFIG.get(lang, {}).get('description', lang)
                lines.append(f"| **{desc}** | {count} | {percentage:.1f}% |")
            lines.append("")
            
            # 列出各语言的文件
            lines.append("### 📋 各语言文件列表")
            lines.append("")
            for lang in sorted(lang_stats.keys(), key=lambda x: lang_stats[x], reverse=True):
                desc = LANGUAGES_CONFIG.get(lang, {}).get('description', lang)
                files = lang_files.get(lang, [])
                lines.append(f"#### {desc} ({len(files)} 个文件)")
                lines.append("")
                # 显示前20个文件
                for file in files[:20]:
                    lines.append(f"- `{file}`")
                if len(files) > 20:
                    lines.append(f"- ... 还有 {len(files)-20} 个文件")
                lines.append("")
        
        # 代码行数统计
        if code_line_stats:
            lines.append("## 📊 代码行数统计")
            lines.append("")
            lines.append("| 语言 | 估算代码行数 |")
            lines.append("|:---|---:|")
            total_lines = sum(code_line_stats.values())
            for lang in sorted(code_line_stats.keys(), key=lambda x: code_line_stats[x], reverse=True):
                desc = LANGUAGES_CONFIG.get(lang, {}).get('description', lang)
                lines.append(f"| **{desc}** | {code_line_stats[lang]:,} |")
            lines.append(f"| **总计** | **{total_lines:,}** |")
            lines.append("")
        
        # 目录结构
        if all_files:
            lines.append("## 📁 目录结构")
            lines.append("")
            from collections import defaultdict
            dir_stats = defaultdict(int)
            for file_path in all_files:
                dir_name = str(Path(file_path).parent)
                dir_stats[dir_name] = dir_stats.get(dir_name, 0) + 1
            
            lines.append("| 目录 | 文件数 |")
            lines.append("|:---|---:|")
            for dir_name, count in sorted(dir_stats.items(), key=lambda x: x[1], reverse=True):
                if dir_name == '.':
                    lines.append(f"| 📂 **根目录** | {count} |")
                else:
                    # 缩短长路径显示
                    display_name = dir_name if len(dir_name) < 60 else f"...{dir_name[-57:]}"
                    lines.append(f"| 📁 `{display_name}` | {count} |")
            lines.append("")
        
        # 项目模块功能简述（自动生成）
        lines.append("## 📖 项目模块功能简述")
        lines.append("")
        # 功能推测规则
        def guess_module_desc(path: str) -> str:
            path_lower = path.lower()
            if "test" in path_lower:
                return "单元测试"
            if "example" in path_lower:
                return "示例/演示代码"
            if path_lower.startswith("src/"):
                return "核心源码模块"
            if "/" not in path and path_lower.startswith("analyze_"):
                return "主分析程序"
            return "通用模块"
        
        for f in sorted(all_files):
            desc = guess_module_desc(f)
            lines.append(f"- `{f}`：{desc}")
        lines.append("")
        
        # 符号分析
        if symbols_overview:
            lines.append("## 🔍 代码符号分析")
            lines.append("")
            
            # 按语言分组统计
            from collections import defaultdict
            lang_summary = defaultdict(lambda: {'files': 0, 'classes': 0, 'functions': 0, 'variables': 0})
            
            for item in symbols_overview:
                if 'error' in item:
                    continue
                
                lang = item.get('language', 'unknown')
                classes = item.get('classes', [])
                functions = item.get('functions', [])
                variables = item.get('variables', [])
                
                if classes or functions or variables:
                    lang_summary[lang]['files'] += 1
                    lang_summary[lang]['classes'] += len(classes)
                    lang_summary[lang]['functions'] += len(functions)
                    lang_summary[lang]['variables'] += len(variables)
            
            # 语言汇总表格
            lines.append("### 📈 语言符号汇总")
            lines.append("")
            lines.append("| 语言 | 分析文件 | 类 | 函数 | 变量 |")
            lines.append("|:---|:---:|:---:|:---:|:---:|")
            
            for lang, stats in sorted(lang_summary.items(), key=lambda x: x[1]['files'], reverse=True):
                desc = LANGUAGES_CONFIG.get(lang, {}).get('description', lang)
                lines.append(f"| **{desc}** | {stats['files']} | {stats['classes']} | {stats['functions']} | {stats['variables']} |")
            lines.append("")
            
            # 详细文件分析
            lines.append("### 🔬 详细文件分析")
            lines.append("")
            
            # 按语言分组显示
            for lang in sorted(lang_summary.keys(), key=lambda x: lang_summary[x]['files'], reverse=True):
                desc = LANGUAGES_CONFIG.get(lang, {}).get('description', lang)
                lines.append(f"#### {desc}")
                lines.append("")
                
                lang_items = [item for item in symbols_overview if item.get('language') == lang and 'error' not in item]
                
                for item in lang_items:
                    file_path = item['file']
                    classes = item.get('classes', [])
                    functions = item.get('functions', [])
                    variables = item.get('variables', [])
                    
                    if not classes and not functions and not variables:
                        continue
                    
                    lines.append(f"##### `{file_path}`")
                    lines.append("")
                    
                    if classes:
                        lines.append(f"- **类定义** ({len(classes)} 个)")
                        for cls in classes[:10]:
                            lines.append(f"  - `{cls}`")
                        if len(classes) > 10:
                            lines.append(f"  - ... 还有 {len(classes)-10} 个")
                        lines.append("")
                    
                    if functions:
                        lines.append(f"- **函数/方法** ({len(functions)} 个)")
                        for func in functions[:15]:
                            lines.append(f"  - `{func}`")
                        if len(functions) > 15:
                            lines.append(f"  - ... 还有 {len(functions)-15} 个")
                        lines.append("")
                    
                    if variables:
                        lines.append(f"- **变量** ({len(variables)} 个)")
                        for var in variables[:10]:
                            lines.append(f"  - `{var}`")
                        if len(variables) > 10:
                            lines.append(f"  - ... 还有 {len(variables)-10} 个")
                        lines.append("")
        
        # 模式搜索结果
        if pattern_results:
            lines.append("## 🔎 代码模式统计")
            lines.append("")
            lines.append("| 模式类型 | 语言 | 匹配数量 | 搜索文件数 |")
            lines.append("|:---|:---|---:|---:|")
            
            for pattern_key, result in pattern_results.items():
                if 'error' in result:
                    continue
                
                if isinstance(result, dict):
                    match_count = result.get('match_count', 0)
                    files_searched = result.get('files_searched', 0)
                    lang = result.get('lang', '')
                    kind = result.get('kind', '')
                    desc = result.get('desc', '')
                    
                    lang_desc = LANGUAGES_CONFIG.get(lang, {}).get('description', lang)
                    lines.append(f"| {kind} | {lang_desc} | {match_count} | {files_searched} |")
            lines.append("")
            
            # 模式示例（占位，实际可以从搜索结果中提取）
            lines.append("### 💡 模式示例")
            lines.append("")
            lines.append("> 此处可展示具体的代码模式匹配示例")
            lines.append("")
        
        # 配置文件
        if 'workflow' in report and 'error' not in report['workflow']:
            workflow = report['workflow']
            if workflow.get('config_files'):
                lines.append("## ⚙️ 配置文件")
                lines.append("")
                lines.append(f"发现 {len(workflow['config_files'])} 个配置文件:")
                lines.append("")
                for config in workflow['config_files']:
                    lines.append(f"- `{config}`")
                lines.append("")
        

        
        lines.append("---")
        lines.append("")
        lines.append("## ✅ 分析完成")
        lines.append("")
        lines.append("> Generated by Serena MCP Multi-Language Analyzer")
        lines.append("> 本报告包含完整的多语言代码分析结果，可用于项目理解和架构评估")
        
        # 生成时间与项目信息
        project_name = Path(PROJECT_PATH).name
        gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.insert(-2, f"> 生成时间：{gen_time} | 项目名称：{project_name}")
        
        report_text = "\n".join(lines)
        
        # 保存报告
        if args.output:
            output_path = Path(args.output)
        else:
            # 默认保存到 ai-analyze/reports 目录，带项目名和日期戳
            output_dir = ai_analyze_root / 'reports'
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"{project_name}_analysis_{timestamp}.md"
            output_path = output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print("\n" + report_text)
        print(f"\n✅ 多语言分析报告已保存至: {output_path.absolute()}")

        # 保存 JSON 报告（原始数据）
        json_output_path = output_path.with_suffix('.json')
        json_data = {
            "project_path": PROJECT_PATH,
            "generated_at": datetime.now().isoformat(),
            "languages": dict(lang_stats),
            "language_files": dict(lang_files),
            "directory_structure": dir_stats,
            "symbols_overview": symbols_overview,
            "tools": report.get('tools', [])
        }
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON 数据报告已保存至: {json_output_path.absolute()}")

    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
