#!/usr/bin/env python3
"""
AI 增强代码分析器
集成 deepseek API 进行深度代码分析
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import openai

# 加载环境变量（从 ai-analyze 根目录）
script_dir = Path(__file__).parent
ai_analyze_root = script_dir.parent
load_dotenv(ai_analyze_root / '.env')

class AIEnhancedAnalyzer:
    """AI 增强代码分析器"""
    
    def __init__(self):
        # 配置 deepseek API
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
        self.model = os.getenv("OPENAI_MODEL", "deepseek-chat")
        
        if not self.api_key:
            raise ValueError("请设置 OPENAI_API_KEY 环境变量")
        
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def analyze_code_quality(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI 分析代码质量
        
        Args:
            analysis_data: Serena 分析得到的代码结构数据
            
        Returns:
            AI 分析结果，包括质量评估、建议等
        """
        # 准备提示词
        prompt = self._prepare_quality_analysis_prompt(analysis_data)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位经验丰富的软件架构师和代码审查专家。请基于提供的代码分析数据，给出专业的代码质量评估和改进建议。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            ai_analysis = response.choices[0].message.content
            return self._parse_ai_analysis(ai_analysis)
            
        except Exception as e:
            return {
                "error": f"AI 分析失败: {str(e)}",
                "raw_analysis": None
            }
    
    def _prepare_quality_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """准备代码质量分析的提示词"""
        
        # 提取关键信息
        project_path = data.get("project_path", "")
        languages = data.get("languages", {})
        dir_stats = data.get("directory_structure", {})
        symbols = data.get("symbols_overview", [])
        
        # 构建文件结构摘要
        file_summary = []
        total_files = sum(languages.values())
        
        for lang, count in languages.items():
            percentage = (count / total_files * 100) if total_files > 0 else 0
            file_summary.append(f"- {lang}: {count} 个文件 ({percentage:.1f}%)")
        
        # 构建目录结构摘要
        dir_summary = []
        if dir_stats:
            dir_summary.append(f"- 总目录数: {len(dir_stats)}")
            dir_summary.append(f"- 各目录文件分布:")
            # 按文件数排序，显示前10个
            sorted_dirs = sorted(dir_stats.items(), key=lambda x: x[1], reverse=True)[:10]
            for dir_path, file_count in sorted_dirs:
                dir_summary.append(f"  - {dir_path}: {file_count} 个文件")
        
        # 构建符号摘要
        symbol_summary = []
        total_symbols = len(symbols)
        successful_symbols = 0
        failed_symbols = 0
        
        if total_symbols > 0:
            # 分析符号解析结果
            symbol_types = {}
            failed_files = []
            
            for symbol in symbols:
                if "error" in symbol:
                    failed_symbols += 1
                    failed_files.append(symbol.get("file", "unknown"))
                else:
                    successful_symbols += 1
                    symbol_type = symbol.get("type", "unknown")
                    symbol_types[symbol_type] = symbol_types.get(symbol_type, 0) + 1
            
            # 显示符号类型统计
            if symbol_types:
                symbol_summary.append(f"- 成功解析的符号类型:")
                for sym_type, count in symbol_types.items():
                    symbol_summary.append(f"  - {sym_type}: {count} 个")
            
            # 显示失败的文件数（前5个）
            if failed_files:
                symbol_summary.append(f"- 解析失败的文件: {len(failed_files)} 个")
                for failed_file in failed_files[:5]:
                    symbol_summary.append(f"  - {failed_file}")
                if len(failed_files) > 5:
                    symbol_summary.append(f"  - ... 还有 {len(failed_files) - 5} 个")
        
        # 统计成功解析的符号比例
        symbol_success_rate = (successful_symbols / total_symbols * 100) if total_symbols > 0 else 0
        
        prompt = f"""请对以下项目进行深入的代码质量分析和架构评估：

## 项目基本信息
- **项目路径**: {project_path}
- **总文件数**: {total_files}

## 编程语言分布
{chr(10).join(file_summary)}

## 目录结构
{chr(10).join(dir_summary) if dir_summary else "- 暂无详细目录结构信息"}

## 代码符号分析结果
- **尝试解析文件数**: {total_symbols}
- **成功解析**: {successful_symbols} 个 ({symbol_success_rate:.1f}%)
- **解析失败**: {failed_symbols} 个 ({100-symbol_success_rate:.1f}%)

### 符号解析详情
{chr(10).join(symbol_summary) if symbol_summary else "暂无有效符号信息"}

## 分析要求
请从以下维度进行专业分析：

1. **项目架构评估**
   - 基于目录结构分析模块划分合理性
   - 评估项目组织是否符合 {list(languages.keys())[0] if languages else "该语言"} 最佳实践
   - 分析可扩展性和可维护性

2. **技术栈分析**
   - 评估编程语言选择是否合适
   - 分析技术栈的现代化程度
   - 识别可能需要更新的依赖或工具

3. **潜在问题识别**
   - 基于目录结构识别可能的代码组织问题
   - 评估测试覆盖率（如果存在测试文件）
   - 识别配置文件中的潜在问题

4. **改进建议**
   - 目录结构优化建议
   - 代码组织改进方案
   - 开发效率提升建议

## 限制说明
**注意**: 代码符号解析成功率较低（{symbol_success_rate:.1f}%），无法深入分析具体代码实现。建议检查 Serena 配置或手动审查关键代码文件。

请提供详细、专业且可操作的分析结果。"""
        
        return prompt
    
    def _parse_ai_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """解析 AI 分析结果"""
        # 这里可以根据 AI 返回的格式进行解析
        # 为简单起见，先返回原始文本
        return {
            "raw_analysis": analysis_text,
            "quality_score": self._extract_quality_score(analysis_text),
            "key_findings": self._extract_key_findings(analysis_text),
            "recommendations": self._extract_recommendations(analysis_text)
        }
    
    def _extract_quality_score(self, text: str) -> Optional[int]:
        """从 AI 分析中提取质量评分"""
        import re
        match = re.search(r'(\d+)[\s/]*10', text)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_key_findings(self, text: str) -> List[str]:
        """提取关键发现"""
        # 简单的提取逻辑，可以根据实际输出格式调整
        lines = text.split('\n')
        findings = []
        in_findings = False
        
        for line in lines:
            if '潜在问题' in line or '关键发现' in line:
                in_findings = True
            elif in_findings and line.strip().startswith('-'):
                findings.append(line.strip())
            elif in_findings and line.strip() == '':
                break
        
        return findings
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """提取改进建议"""
        lines = text.split('\n')
        recommendations = []
        in_recs = False
        
        for line in lines:
            if '改进建议' in line or '建议' in line:
                in_recs = True
            elif in_recs and line.strip().startswith('-'):
                recommendations.append(line.strip())
            elif in_recs and line.strip() == '' and recommendations:
                break
        
        return recommendations
    
    def enhance_report(self, serena_report_path: str, output_path: Optional[str] = None) -> str:
        """
        增强 Serena 分析报告，添加 AI 分析结果
        
        Args:
            serena_report_path: Serena 生成的 JSON 报告路径
            output_path: 增强报告的输出路径
            
        Returns:
            增强后的报告内容
        """
        # 读取 Serena 分析报告
        with open(serena_report_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        # 获取 AI 分析
        print("🤖 正在进行 AI 深度代码分析...")
        ai_results = self.analyze_code_quality(analysis_data)
        
        if "error" in ai_results:
            print(f"⚠️  AI 分析警告: {ai_results['error']}")
            ai_markdown = "\n## ⚠️ AI 分析暂时不可用\n\n请检查 API 配置或网络连接。\n"
        else:
            # 生成 AI 分析的 Markdown 内容
            ai_markdown = self._generate_ai_markdown(ai_results)
        
        # 读取原始的 Markdown 报告
        md_path = serena_report_path.replace('.json', '.md')
        with open(md_path, 'r', encoding='utf-8') as f:
            original_md = f.read()
        
        # 在原始报告后添加 AI 分析
        enhanced_report = f"""{original_md}

{ai_markdown}

---

*报告由 Serena + AI 增强分析器生成*
"""
        
        # 保存增强后的报告
        if output_path:
            output_file = Path(output_path)
        else:
            # 默认在原文件名后添加 -ai-enhanced
            output_file = Path(md_path.replace('.md', '-ai.md'))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(enhanced_report)
        
        print(f"✅ AI 增强报告已保存至: {output_file}")
        
        return enhanced_report
    
    def _generate_ai_markdown(self, ai_results: Dict[str, Any]) -> str:
        """生成 AI 分析的 Markdown 内容"""
        
        md = f"""## 🤖 AI 深度代码分析

### 📊 代码质量评分
"""
        
        score = ai_results.get("quality_score")
        if score:
            stars = "⭐" * (score // 2) + "☆" * (5 - (score // 2))
            md += f"{stars} **{score}/10**\n\n"
        
        md += f"### 📝 详细分析\n\n{ai_results.get('raw_analysis', '暂无分析结果')}\n"
        
        findings = ai_results.get("key_findings", [])
        if findings:
            md += f"\n### ⚠️ 关键发现\n\n"
            for finding in findings:
                md += f"{finding}\n"
        
        recommendations = ai_results.get("recommendations", [])
        if recommendations:
            md += f"\n### 💡 改进建议\n\n"
            for rec in recommendations:
                md += f"{rec}\n"
        
        return md


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI 增强代码分析器")
    parser.add_argument("report_path", help="Serena 生成的 JSON 报告路径")
    parser.add_argument("-o", "--output", help="增强报告的输出路径（可选）")
    
    args = parser.parse_args()
    
    try:
        analyzer = AIEnhancedAnalyzer()
        analyzer.enhance_report(args.report_path, args.output)
    except Exception as e:
        print(f"❌ 错误: {e}")
        exit(1)


if __name__ == "__main__":
    main()
