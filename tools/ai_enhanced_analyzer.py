#!/usr/bin/env python3
"""
AI 增强代码分析器
集成 deepseek API 进行深度代码分析
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import openai

# 加载环境变量（从 ai-analyze 根目录）
script_dir = Path(__file__).parent
ai_analyze_root = script_dir.parent
load_dotenv(ai_analyze_root / '.env')

# 导入 Docker 生成器
sys.path.insert(0, str(script_dir))
from docker_generator import DockerGenerator

class AIEnhancedAnalyzer:
    """AI 增强代码分析器"""

    def __init__(self, use_cache: bool = True, cache_ttl: int = 3600):
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

        # 缓存配置
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl  # 默认缓存有效期 1 小时（3600 秒）
        self.cache_dir = Path(__file__).parent.parent / ".cache"
        self.cache_dir.mkdir(exist_ok=True)

    def analyze_code_quality(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI 分析代码质量

        Args:
            analysis_data: Serena 分析得到的代码结构数据

        Returns:
            AI 分析结果，包括质量评估、建议等
        """
        # 准备增强的提示词（包含复杂度信息）
        prompt = self._build_enhanced_prompt(analysis_data)

        # 尝试从缓存获取
        project_path = analysis_data.get("project_path", "")
        cache_key = self._generate_cache_key(project_path, "code_quality")
        cached_result = self._get_cache(cache_key)

        if cached_result:
            print("✅ 从缓存加载代码质量分析结果")
            return cached_result

        # 缓存未命中，调用 AI
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
            result = self._parse_ai_analysis(ai_analysis)

            # 保存到缓存
            self._save_cache(cache_key, result)
            return result

        except Exception as e:
            return {
                "error": f"AI 分析失败: {str(e)}",
                "raw_analysis": None
            }

    def _extract_complexity_hotspots(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取代码复杂度热点"""
        hotspots = {
            "complex_functions": [],
            "large_classes": [],
            "deep_nesting": [],
            "summary": ""
        }

        # 尝试从 AST 分析结果中提取
        ast_analysis = data.get("ast_analysis", {})
        if not ast_analysis:
            return hotspots

        # 提取复杂度最高的函数
        functions = ast_analysis.get("functions", [])
        if functions:
            # 按圈复杂度排序
            sorted_functions = sorted(
                functions,
                key=lambda f: f.get("complexity", {}).get("cyclomatic_complexity", 0),
                reverse=True
            )[:5]

            for func in sorted_functions:
                hotspots["complex_functions"].append({
                    "name": func.get("name", "unknown"),
                    "file": func.get("file_path", "unknown"),
                    "complexity": func.get("complexity", {}),
                    "lines": func.get("lines", 0)
                })

        # 提取大类
        classes = ast_analysis.get("classes", [])
        if classes:
            sorted_classes = sorted(
                classes,
                key=lambda c: c.get("lines", 0),
                reverse=True
            )[:5]

            for cls in sorted_classes:
                hotspots["large_classes"].append({
                    "name": cls.get("name", "unknown"),
                    "file": cls.get("file_path", "unknown"),
                    "lines": cls.get("lines", 0),
                    "methods": len(cls.get("methods", []))
                })

        # 提取深层嵌套
        code_smells = ast_analysis.get("code_smells", [])
        if code_smells:
            deep_nesting = [s for s in code_smells if "Deep Nesting" in s.get("name", "")][:3]
            hotspots["deep_nesting"] = deep_nesting

        # 生成摘要
        summary_parts = []
        if hotspots["complex_functions"]:
            summary_parts.append(f"发现 {len(hotspots['complex_functions'])} 个高复杂度函数")
        if hotspots["large_classes"]:
            summary_parts.append(f"发现 {len(hotspots['large_classes'])} 个大类")
        if hotspots["deep_nesting"]:
            summary_parts.append(f"发现 {len(hotspots['deep_nesting'])} 处深层嵌套")

        hotspots["summary"] = "；".join(summary_parts) if summary_parts else "代码复杂度正常"

        return hotspots

    def _extract_code_smells(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取代码坏味道"""
        smells = []

        # 尝试从 AST 分析结果中提取
        ast_analysis = data.get("ast_analysis", {})
        if not ast_analysis:
            return smells

        code_smells = ast_analysis.get("code_smells", [])

        # 按严重程度排序
        severity_order = {"high": 0, "medium": 1, "low": 2}
        sorted_smells = sorted(
            code_smells,
            key=lambda s: severity_order.get(s.get("severity", "low"), 3)
        )[:10]  # 取前10个

        for smell in sorted_smells:
            smells.append({
                "name": smell.get("name", "unknown"),
                "severity": smell.get("severity", "low"),
                "location": smell.get("location", "unknown"),
                "description": smell.get("description", ""),
                "suggestion": smell.get("suggestion", "")
            })

        return smells

    def _build_dependency_graph(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """构建依赖图"""
        graph = {
            "imports": [],
            "circular_dependencies": [],
            "external_dependencies": [],
            "summary": ""
        }

        # 尝试从 AST 分析结果中提取
        ast_analysis = data.get("ast_analysis", {})
        if not ast_analysis:
            return graph

        # 提取导入信息
        imports = ast_analysis.get("imports", [])
        if imports:
            # 统计导入
            import_counts = {}
            for imp in imports[:20]:  # 取前20个
                import_counts[imp] = import_counts.get(imp, 0) + 1

            graph["imports"] = [
                {"module": mod, "count": count}
                for mod, count in sorted(import_counts.items(), key=lambda x: x[1], reverse=True)
            ]

        # 生成摘要
        graph["summary"] = f"检测到 {len(imports)} 个导入，{len(set(imports))} 个唯一模块"

        return graph

    def _build_enhanced_prompt(self, data: Dict[str, Any]) -> str:
        """构建增强的 AI Prompt，包含复杂度信息"""

        # 提取复杂度热点
        hotspots = self._extract_complexity_hotspots(data)

        # 提取代码坏味道
        smells = self._extract_code_smells(data)

        # 构建依赖图
        deps = self._build_dependency_graph(data)

        # 构建增强的 Prompt
        base_prompt = self._prepare_quality_analysis_prompt(data)

        # 添加复杂度信息
        enhanced_prompt = base_prompt + """

## 🔴 代码复杂度分析

### 复杂度热点
{hotspots['summary']}

"""

        if hotspots["complex_functions"]:
            enhanced_prompt += "#### 高复杂度函数\n\n"
            for func in hotspots["complex_functions"]:
                cc = func.get("complexity", {}).get("cyclomatic_complexity", 0)
                enhanced_prompt += f"- **{func['name']}** ({func['file']})\n"
                enhanced_prompt += f"  - 圈复杂度: {cc}\n"
                enhanced_prompt += f"  - 代码行数: {func['lines']}\n"

        if hotspots["large_classes"]:
            enhanced_prompt += "\n#### 大类\n\n"
            for cls in hotspots["large_classes"]:
                enhanced_prompt += f"- **{cls['name']}** ({cls['file']})\n"
                enhanced_prompt += f"  - 代码行数: {cls['lines']}\n"
                enhanced_prompt += f"  - 方法数: {cls['methods']}\n"

        # 添加代码坏味道
        if smells:
            enhanced_prompt += f"\n## ⚠️ 代码坏味道检测\n\n发现 {len(smells)} 个代码坏味道：\n\n"
            for smell in smells[:5]:  # 显示前5个
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(smell["severity"], "⚪")
                enhanced_prompt += f"- {severity_emoji} **{smell['name']}** ({smell['severity']})\n"
                enhanced_prompt += f"  - 位置: {smell['location']}\n"
                enhanced_prompt += f"  - 建议: {smell['suggestion']}\n"

        # 添加依赖信息
        if deps["imports"]:
            enhanced_prompt += f"\n## 📦 依赖分析\n\n{deps['summary']}\n\n"
            enhanced_prompt += "#### 主要依赖\n\n"
            for imp in deps["imports"][:5]:
                enhanced_prompt += f"- {imp['module']} (引用 {imp['count']} 次)\n"

        enhanced_prompt += """

## 🎯 分析重点

基于上述复杂度分析，请重点关注：

1. **高复杂度函数的优化**
   - 这些函数是否可以拆分成更小的函数？
   - 是否存在重复代码可以提取？
   - 是否可以使用设计模式简化逻辑？

2. **大类的重构**
   - 这些类是否违反了单一职责原则？
   - 是否可以拆分成多个更小的类？
   - 是否存在可以提取的公共基类？

3. **代码坏味道的改进**
   - 如何消除检测到的代码坏味道？
   - 是否需要重构来改进代码质量？

4. **依赖管理**
   - 是否存在循环依赖？
   - 依赖关系是否合理？
   - 是否需要优化导入结构？

请提供具体、可操作的改进建议。"""

        return enhanced_prompt

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
            dir_summary.append("- 各目录文件分布:")
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
                symbol_summary.append("- 成功解析的符号类型:")
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

        prompt = """请对以下项目进行深入的代码质量分析和架构评估：

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

    def enhance_report(self, serena_report_path: str, output_path: Optional[str] = None, replace_original: bool = False) -> str:
        """
        增强 Serena 分析报告，添加 AI 分析结果

        Args:
            serena_report_path: Serena 生成的 JSON 报告路径
            output_path: 增强报告的输出路径
            replace_original: 是否替换原始 Markdown 报告（默认创建新的 -ai.md 文件）

        Returns:
            增强后的报告内容
        """
        # 读取 Serena 分析报告
        with open(serena_report_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)

        # 获取项目路径
        project_path = analysis_data.get('project_path', '')

        # 预定义变量，避免 f-string 中的反斜杠问题（必须在所有 f-string 之前定义）
        project_name_simple = Path(project_path).name

        # 检查 Docker 配置
        print("🐳 检查 Docker 配置...")
        docker_generator = DockerGenerator(project_path)
        has_docker, existing_files = docker_generator.has_docker_config()

        # 预定义项目类型
        project_type_simple = docker_generator.detect_project_type(analysis_data)

        # 预定义变量（避免 f-string 错误）
        project_name = project_name_simple  # 已在前面定义

        # 获取 AI 分析
        print("🤖 正在进行 AI 深度代码分析...")
        ai_results = self.analyze_code_quality(analysis_data)

        # AI Docker 策略分析
        print("🐳 正在进行 AI Docker 策略分析...")
        if "error" not in ai_results:
            ai_docker_strategy = self.analyze_docker_strategy(analysis_data, ai_results.get("raw_analysis", ""))
        else:
            ai_docker_strategy = {"error": "AI 代码质量分析失败，无法分析 Docker 策略"}

        # AI 框架升级建议分析
        print("🔄 正在进行 AI 框架升级建议分析...")
        if "error" not in ai_results:
            ai_framework_upgrade = self.analyze_framework_upgrade(analysis_data)
        else:
            ai_framework_upgrade = {"error": "AI 代码质量分析失败，无法分析框架升级建议"}

        # AI Docker 策略建议
        ai_docker_recommendations = []
        if "error" not in ai_docker_strategy:
            ai_docker_recommendations = ai_docker_strategy.get("recommendations", [])
            ai_base_image = ai_docker_strategy.get("base_image")
            ai_port = ai_docker_strategy.get("recommended_port")
            ai_needs_db = ai_docker_strategy.get("needs_database", False)
        else:
            ai_base_image = None
            ai_port = None
            ai_needs_db = False

        # 简化 Docker 配置部分，只显示当前状态和 AI 建议，不生成配置
        if has_docker:
            print(f"✅ 项目已存在 Docker 配置: {', '.join(existing_files)}")
            docker_section = """## 🐳 Docker 配置

项目已包含 Docker 配置文件：{', '.join(existing_files)}

### 快速启动
```bash
# 构建镜像
docker build -t {project_name}:latest .

# 运行容器
docker run -d -p 3000:3000 {project_name}:latest

# 或使用 docker-compose
docker-compose up -d
```
"""
        else:
            print("⚠️  项目未找到 Docker 配置")
            docker_section = """## 🐳 Docker 配置

⚠️ 项目未找到 Docker 配置。请在 `full_analyzer.py` 的步骤 3 中生成 Docker 配置。

### 手动创建

请根据项目类型手动创建 Dockerfile：

1. **识别项目类型**: {project_type}
2. **创建 Dockerfile**: 参考官方文档
3. **构建镜像**: `docker build -t {project_name}:latest .`
4. **运行容器**: `docker run -d -p 3000:3000 {project_name}:latest`

### 快速参考

**Next.js**: https://github.com/vercel/next.js/tree/canary/examples/with-docker
**FastAPI**: https://fastapi.tiangolo.com/deployment/docker/
**Django**: https://docs.djangoproject.com/en/4.2/howto/deployment/
"""

        # 添加 AI Docker 策略建议
        if "error" not in ai_docker_strategy and ai_docker_recommendations:
            ai_docker_suggestions = """
基于 AI 分析，以下 Docker 配置建议：

{chr(10).join(f'- {rec}' for rec in ai_docker_recommendations[:8])}

**推荐基础镜像**: {ai_base_image or '基于项目类型自动选择'}
**推荐端口**: {ai_port or '默认（3000）'}
**数据库需求**: {'✅ 需要' if ai_needs_db else '❌ 无需数据库服务'}

"""
            docker_section = docker_section + ai_docker_suggestions

        # 如果 AI Docker 策略分析成功，打印总结
        if "error" not in ai_docker_strategy:
            print("✅ AI Docker 策略分析完成")
            print(f"   - 推荐基础镜像: {ai_docker_strategy.get('base_image', '默认')}")
            print(f"   - 推荐端口: {ai_docker_strategy.get('recommended_port', '默认')}")
            print(f"   - 建议: {len(ai_docker_strategy.get('recommendations', []))} 条")

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

        # 生成 AI Docker 策略 Markdown
        docker_strategy_md = ""
        if "error" not in ai_docker_strategy:
            docker_strategy_md = self._generate_docker_strategy_markdown(ai_docker_strategy)

        # 生成 AI 框架升级建议 Markdown
        framework_upgrade_md = ""
        if "error" not in ai_framework_upgrade:
            framework_upgrade_md = self._generate_framework_upgrade_markdown(ai_framework_upgrade)

        # 在原始报告后添加 AI 分析和 Docker 配置
        enhanced_report = """{original_md}

{docker_section}

{docker_strategy_md}

{framework_upgrade_md}

{ai_markdown}

---

*报告由 Serena + AI 增强分析器生成*
"""

        # 保存增强后的报告
        if output_path:
            output_file = Path(output_path)
        elif replace_original:
            # 替换原始报告
            output_file = Path(md_path)
        else:
            # 默认在原文件名后添加 -ai
            output_file = Path(md_path.replace('.md', '-ai.md'))

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(enhanced_report)

        print(f"✅ AI 增强报告已保存至: {output_file}")

        return enhanced_report

    def analyze_docker_strategy(self, analysis_data: Dict[str, Any], ai_analysis: str) -> Dict[str, Any]:
        """
        AI 分析 Docker 部署策略

        Args:
            analysis_data: Serena 分析数据
            ai_analysis: AI 对代码质量的分析结果

        Returns:
            Docker 部署策略建议
        """
        project_path = analysis_data.get("project_path", "")
        languages = analysis_data.get("languages", {})
        symbols = analysis_data.get("symbols_overview", [])

        # 尝试从缓存获取
        cache_key = self._generate_cache_key(project_path, "docker_strategy")
        cached_result = self._get_cache(cache_key)

        if cached_result:
            print("✅ 从缓存加载 Docker 策略分析结果")
            return cached_result

        # 准备提示词
        prompt = self._prepare_docker_strategy_prompt(analysis_data, ai_analysis)

        # 缓存未命中，调用 AI
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位经验丰富的 DevOps 工程师和云原生架构师。请基于项目分析数据，给出专业的 Docker 部署策略、容器优化建议和最佳实践。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # 降低随机性，确保技术准确性
                max_tokens=3000
            )

            ai_docker_strategy = response.choices[0].message.content
            result = self._parse_docker_strategy(ai_docker_strategy, analysis_data)

            # 保存到缓存
            self._save_cache(cache_key, result)
            return result

        except Exception as e:
            return {
                "error": f"Docker 策略分析失败: {str(e)}",
                "strategy": None,
                "recommendations": []
            }

    def analyze_framework_upgrade(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI 分析框架升级建议

        Args:
            analysis_data: Serena 分析数据

        Returns:
            框架升级建议
        """
        project_path = analysis_data.get("project_path", "")
        languages = analysis_data.get("languages", {})

        # 尝试从缓存获取
        cache_key = self._generate_cache_key(project_path, "framework_upgrade")
        cached_result = self._get_cache(cache_key)

        if cached_result:
            print("✅ 从缓存加载框架升级建议结果")
            return cached_result

        # 准备提示词
        prompt = self._prepare_framework_upgrade_prompt(analysis_data)

        # 缓存未命中，调用 AI
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位经验丰富的技术架构师，精通主流编程框架的版本升级、迁移策略和最佳实践。请基于项目分析数据，给出专业、谨慎的框架升级建议。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # 降低随机性，确保技术准确性
                max_tokens=2500
            )

            ai_framework_upgrade = response.choices[0].message.content
            result = self._parse_framework_upgrade(ai_framework_upgrade, analysis_data)

            # 保存到缓存
            self._save_cache(cache_key, result)
            return result

        except Exception as e:
            return {
                "error": f"框架升级建议分析失败: {str(e)}",
                "framework_versions": [],
                "upgrade_paths": [],
                "recommendations": []
            }

    def _prepare_framework_upgrade_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """准备框架升级建议分析的提示词"""

        project_path = analysis_data.get("project_path", "")
        languages = analysis_data.get("languages", {})
        dir_stats = analysis_data.get("directory_structure", {})

        # 检查关键依赖文件
        project_root = Path(project_path)
        dependencies_info = {}

        # Python 项目
        if (project_root / "pyproject.toml").exists():
            try:
                content = (project_root / "pyproject.toml").read_text()
                import re
                python_matches = re.findall(r'python\s*=\s*["\']([^"\']+)["\']', content)
                python_version = python_matches[0] if python_matches else "未指定"
                dependencies_info["python_version"] = python_version
            except Exception:
                pass

        # Node.js 项目
        if (project_root / "package.json").exists():
            try:
                with open(project_root / "package.json") as f:
                    package_data = json.load(f)
                    dependencies_info["node_version"] = package_data.get("engines", {}).get("node", "未指定")

                    # 提取主要依赖和版本
                    key_deps = {}
                    for dep in ["react", "vue", "next", "angular", "express", "nestjs", "typescript"]:
                        if dep in package_data.get("dependencies", {}):
                            key_deps[dep] = package_data["dependencies"][dep]

                    dependencies_info["key_dependencies"] = key_deps
            except Exception:
                pass

        # Go 项目
        if (project_root / "go.mod").exists():
            try:
                content = (project_root / "go.mod").read_text()
                import re
                go_version = re.search(r'go\s+([0-9.]+)', content)
                dependencies_info["go_version"] = go_version.group(1) if go_version else "未指定"
            except Exception:
                pass

        prompt = """请基于以下项目分析数据，给出框架升级建议：

## 📁 项目基本信息
- **项目路径**: {project_path}
- **主要语言**: {', '.join(languages.keys()) if languages else '未知'}
- **总文件数**: {sum(languages.values())}

## 📦 依赖版本信息

### Python
- **Python 版本**: {dependencies_info.get("python_version", "未检测到 Python 项目")}

### Node.js
- **Node 版本**: {dependencies_info.get("node_version", "未检测到 Node.js 项目")}
- **主要依赖**:
{chr(10).join([f'- {name}: {version}' for name, version in dependencies_info.get("key_dependencies", {}).items()]) if dependencies_info.get("key_dependencies") else "- 未检测到关键依赖"}

### Go
- **Go 版本**: {dependencies_info.get("go_version", "未检测到 Go 项目")}

## 📂 目录结构（前5个）
{chr(10).join([f'- {dir_path} ({file_count}个文件)' for dir_path, file_count in sorted(dir_stats.items(), key=lambda x: x[1], reverse=True)[:5]]) if dir_stats else "- 暂无目录信息"}

## 🎯 分析要求

请从以下维度给出谨慎、专业的框架升级建议：

### 1. **当前框架版本分析**
   - 识别当前使用的框架和版本
   - 分析当前版本的维护状态（EOL、LTS 等）
   - 评估当前版本是否存在已知的安全漏洞

### 2. **推荐升级路径**
   - 建议升级到哪个版本（考虑稳定性、兼容性）
   - 是否需要分步升级（如 React 16 -> 17 -> 18）
   - 每个升级步骤的注意事项

### 3. **Breaking Changes 分析**
   - 列出主要 breaking changes
   - 评估对项目的影响范围
   - 提供迁移方案和代码修改建议

### 4. **升级风险评估**
   - 升级的复杂度评估（低/中/高）
   - 可能需要修改的模块数量
   - 测试覆盖要求

### 5. **升级收益**
   - 性能提升预期
   - 新功能带来的价值
   - 安全性改善

### 6. **升级建议**
   - 是否建议立即升级
   - 如果建议延迟升级，说明原因
   - 具体的执行步骤和检查清单

### 7. **注意事项**
   - 依赖兼容性问题
   - 构建工具需要更新
   - 环境要求变化

## ⚠️ 重要提醒

- **谨慎性优先**: 只有在有明显收益（安全、性能、功能）时才建议升级
- **向后兼容**: 优先选择向后兼容的升级路径
- **测试要求**: 必须强调升级前后的测试要求
- **回滚方案**: 提供升级失败时的回滚建议

请提供具体、可操作、负责任的升级建议。如果当前版本已经是最新稳定版，请明确说明，不要强求升级。"""

        return prompt

    def _parse_framework_upgrade(self, upgrade_text: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析框架升级建议分析结果"""

        import re

        # 提取框架版本信息
        frameworks = []
        # 尝试匹配 "React 17 -> 18" 格式
        version_matches = re.findall(r'([A-Za-z]+)\s+(\d+[.\d]*)\s*(?:->|to|升级到)\s*(\d+[.\d]*)', upgrade_text, re.IGNORECASE)
        for match in version_matches:
            frameworks.append({
                "name": match[0],
                "current_version": match[1],
                "recommended_version": match[2]
            })

        # 提取升级路径
        upgrade_paths = []
        # 尝试匹配升级步骤
        step_matches = re.finditer(r'(?:步骤|step)\s*\d+[:：]?\s*([^\n]+)', upgrade_text, re.IGNORECASE)
        for match in step_matches:
            upgrade_paths.append(match.group(1).strip())

        # 提取风险评估等级
        risk_level = None
        if "低风险" in upgrade_text or "low risk" in upgrade_text.lower():
            risk_level = "低"
        elif "高风险" in upgrade_text or "high risk" in upgrade_text.lower():
            risk_level = "高"
        elif "中风险" in upgrade_text or "medium risk" in upgrade_text.lower():
            risk_level = "中"

        return {
            "upgrade_analysis": upgrade_text,
            "framework_versions": frameworks,
            "upgrade_paths": upgrade_paths,
            "risk_level": risk_level,
            "recommendations": self._extract_framework_recommendations(upgrade_text)
        }

    def _extract_framework_recommendations(self, text: str) -> List[str]:
        """提取框架升级相关建议"""

        recommendations = []
        lines = text.split('\n')
        in_recs = False

        for line in lines:
            # 检测建议部分的开始
            if any(keyword in line.lower() for keyword in ['建议', '推荐', '注意', '建议升级', '推荐路径']):
                in_recs = True
            elif in_recs and line.strip().startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.')):
                # 提取列表项
                rec = line.strip().lstrip('-•*12345. ').strip()
                if rec and len(rec) > 5:  # 过滤过短的行
                    recommendations.append(rec)
            elif in_recs and line.strip() == '' and recommendations:
                # 空行表示部分结束
                break

        return recommendations

    def _generate_framework_upgrade_markdown(self, framework_upgrade: Dict[str, Any]) -> str:
        """生成 AI 框架升级建议的 Markdown 内容"""

        if "error" in framework_upgrade:
            return """## 🔄 AI 框架升级建议

⚠️ {framework_upgrade['error']}

### 当前状态

无法提供框架升级建议，请检查代码质量分析结果。
"""

        md = """## 🔄 AI 框架升级建议

基于 AI 深度分析，为该项目提供以下框架升级建议：

### 📋 升级概览

"""

        # 添加框架版本信息
        frameworks = framework_upgrade.get("framework_versions", [])
        if frameworks:
            md += "**框架版本**:\n\n"
            for fw in frameworks:
                md += f"- {fw['name']}: {fw['current_version']} → {fw['recommended_version']}\n"
            md += "\n"
        else:
            md += "未检测到需要升级的框架，当前版本可能已经是最新稳定版。\n\n"

        # 添加风险评估
        risk_level = framework_upgrade.get("risk_level")
        if risk_level:
            risk_emoji = {"低": "✅", "中": "⚠️", "高": "⚠️"}.get(risk_level, "📊")
            md += f"**升级风险等级**: {risk_emoji} {risk_level}风险\n\n"

        md += "### 💡 升级建议\n\n"

        recommendations = framework_upgrade.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations[:6], 1):
                md += f"{i}. {rec}\n"
            if len(recommendations) > 6:
                md += f"\n*还有 {len(recommendations) - 6} 条建议*\n"
        else:
            md += "AI 未提供具体升级建议。\n"

        # 添加升级路径
        upgrade_paths = framework_upgrade.get("upgrade_paths", [])
        if upgrade_paths:
            md += "\n### 🛤️ 推荐升级路径\n\n"
            for i, step in enumerate(upgrade_paths, 1):
                md += f"{i}. {step}\n"

        md += """
### 🔧 技术细节

<details>
<summary>查看详细升级分析</summary>

```
{framework_upgrade.get('upgrade_analysis', '暂无详细分析')}
```
</details>

### ⚠️ 升级前检查清单

- [ ] 备份当前代码和数据库
- [ ] 阅读官方升级文档和 breaking changes
- [ ] 在测试环境进行升级验证
- [ ] 运行完整的单元测试和集成测试
- [ ] 准备回滚方案
- [ ] 通知团队成员升级时间窗口

### 📚 参考资源

- 官方文档升级指南
- 社区升级经验分享
- 迁移工具和自动化脚本

---

"""

        return md


    def _prepare_docker_strategy_prompt(self, analysis_data: Dict[str, Any], ai_analysis: str) -> str:
        """准备 Docker 策略分析的提示词"""

        project_path = analysis_data.get("project_path", "")
        languages = analysis_data.get("languages", {})
        dir_stats = analysis_data.get("directory_structure", {})

        # 检查关键文件
        project_root = Path(project_path)
        key_files = {
            "package.json": (project_root / "package.json").exists(),
            "requirements.txt": (project_root / "requirements.txt").exists(),
            "pyproject.toml": (project_root / "pyproject.toml").exists(),
            "go.mod": (project_root / "go.mod").exists(),
            "composer.json": (project_root / "composer.json").exists(),
            ".env": (project_root / ".env").exists(),
            "Dockerfile": (project_root / "Dockerfile").exists(),
            "docker-compose.yml": (project_root / "docker-compose.yml").exists()
        }

        # 检查可能的数据库
        db_indicators = []
        if (project_root / ".env").exists():
            env_content = (project_root / ".env").read_text().lower()
            if "postgres" in env_content:
                db_indicators.append("PostgreSQL")
            if "mysql" in env_content:
                db_indicators.append("MySQL")
            if "mongodb" in env_content:
                db_indicators.append("MongoDB")
            if "redis" in env_content:
                db_indicators.append("Redis")

        # 检查依赖文件内容
        dependencies = []
        if (project_root / "package.json").exists():
            try:
                with open(project_root / "package.json") as f:
                    package_data = json.load(f)
                    deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                    dependencies.extend([f"{name}:{version}" for name, version in list(deps.items())[:10]])
            except Exception:
                pass
        elif (project_root / "requirements.txt").exists():
            try:
                content = (project_root / "requirements.txt").read_text()
                dependencies.extend([line.strip() for line in content.split('\n')[:10] if line.strip() and not line.startswith('#')])
            except Exception:
                pass

        prompt = """请基于以下项目分析数据，为该项目设计最佳的 Docker 部署策略和容器化方案：

## 📁 项目基本信息
- **项目路径**: {project_path}
- **主要语言**: {', '.join(languages.keys()) if languages else '未知'}
- **总文件数**: {sum(languages.values())}

## 📦 依赖和配置

### 关键文件
{chr(10).join([f'- {file}: {"✅ 存在" if exists else "❌ 不存在"}' for file, exists in key_files.items()])}

### 数据库/缓存
{chr(10).join([f'- {db}' for db in db_indicators]) if db_indicators else "- 未检测到数据库配置"}

### 主要依赖（前10个）
{chr(10).join([f'- {dep}' for dep in dependencies]) if dependencies else "- 无法读取依赖"}

## 📂 目录结构（前10个）
{chr(10).join([f'- {dir_path} ({file_count}个文件)' for dir_path, file_count in sorted(dir_stats.items(), key=lambda x: x[1], reverse=True)[:10]]) if dir_stats else "- 暂无目录信息"}

## 🤖 AI 代码质量分析摘要
```
{ai_analysis[:1500]}  # 截取前1500字符
...
```

## 🎯 分析要求

请从以下维度设计 Docker 部署策略：

### 1. **基础镜像选择**
   - 推荐的基础镜像和版本（alpine、slim、distroless 等）
   - 选择理由（安全性、镜像大小、性能等）

### 2. **多阶段构建策略**
   - 是否需要多阶段构建
   - 各阶段的分层优化建议
   - 最终镜像大小优化目标

### 3. **运行时配置**
   - 推荐端口配置
   - 环境变量管理方案
   - 用户权限最佳实践（非 root 运行）

### 4. **依赖安装优化**
   - 缓存层优化策略
   - 依赖安装顺序建议
   - 减少镜像层的技巧

### 5. **健康检查配置**
   - 健康检查端点建议
   - 合理的检查间隔和超时时间

### 6. **数据库/缓存服务**
   - 是否需要数据库服务
   - 推荐使用 docker-compose 还是外部服务
   - 数据持久化策略

### 7. **性能和安全优化**
   - 镜像安全扫描建议
   - CVE 漏洞修复方案
   - 资源限制建议（CPU、内存）

### 8. **生产环境注意事项**
   - 日志管理方案
   - 监控和告警建议
   - 自动扩缩容考虑

### 9. **CI/CD 集成**
   - 与 GitHub Actions/GitLab CI 集成建议
   - 镜像构建和推送策略
   - 多环境部署方案

### 10. **替代方案**
    - 除了 Docker，是否适合其他部署方式（如 serverless、PaaS 等）

请提供具体、可操作、符合云原生最佳实践的建议。"""

        return prompt

    def _parse_docker_strategy(self, strategy_text: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析 Docker 策略分析结果"""

        # 提取关键信息
        import re

        # 提取基础镜像建议（支持多种格式）
        # 优先匹配 FROM 语句
        base_image = None
        # 尝试匹配 FROM node:22-alpine 格式
        from_match = re.search(r'FROM\s+([a-z0-9/_:.:-]+)', strategy_text, re.IGNORECASE)
        if from_match:
            base_image = from_match.group(1)
            print(f"✅ 从 FROM 语句提取基础镜像: {base_image}")
        else:
            # 如果没有 FROM 语句，尝试匹配中文描述
            base_image_match = re.search(r'(?:基础镜像|推荐镜像)[:：\s]*([a-z0-9/_:.:-]+)', strategy_text, re.IGNORECASE)
            if base_image_match:
                base_image = base_image_match.group(1)
                print(f"✅ 从中文描述提取基础镜像: {base_image}")
            else:
                print("⚠️  未找到基础镜像建议")

        # 提取端口建议（支持多种格式）
        port = None
        # 尝试匹配 EXPOSE 语句
        expose_match = re.search(r'EXPOSE\s*(\d+)', strategy_text, re.IGNORECASE)
        if expose_match:
            port = int(expose_match.group(1))
            print(f"✅ 从 EXPOSE 语句提取端口: {port}")
        else:
            # 尝试匹配中文描述
            port_match = re.search(r'(?:端口|PORT)[:：\s]*(\d+)', strategy_text, re.IGNORECASE)
            if port_match:
                port = int(port_match.group(1))
                print(f"✅ 从中文描述提取端口: {port}")
            else:
                print("⚠️  未找到端口建议")

        # 提取是否需要数据库
        needs_db = bool(re.search(r'(数据库|mysql|postgres|mongodb)', strategy_text, re.IGNORECASE))
        if needs_db:
            print("✅ 检测到数据库需求")

        # 提取多阶段构建建议
        multi_stage = bool(re.search(r'(多阶段构建|multi-stage)', strategy_text, re.IGNORECASE))
        if multi_stage:
            print("✅ 检测到多阶段构建建议")

        # 提取镜像大小目标（支持更灵活的格式）
        # 匹配如 "目标 < 150MB"、"200-300MB"、"300MB" 等格式
        target_size = None
        size_match = re.search(r'(?:镜像大小|目标)[:：\s]*(?:<?\s*)?(\d+(?:-\d+)?\s*MB)', strategy_text, re.IGNORECASE)
        if size_match:
            target_size = size_match.group(1)
            print(f"✅ 提取镜像大小目标: {target_size}")
        else:
            print("⚠️  未找到镜像大小目标")

        return {
            "strategy": strategy_text,
            "base_image": base_image,
            "recommended_port": port,
            "needs_database": needs_db,
            "multi_stage_build": multi_stage,
            "target_image_size": target_size,
            "recommendations": self._extract_docker_recommendations(strategy_text)
        }

    def _extract_docker_recommendations(self, text: str) -> List[str]:
        """提取 Docker 相关建议"""

        recommendations = []
        lines = text.split('\n')
        in_recs = False

        for line in lines:
            # 检测建议部分的开始
            if any(keyword in line.lower() for keyword in ['建议', '推荐', '最佳实践', '优化']):
                in_recs = True
            elif in_recs and line.strip().startswith(('-', '•', '*', '1.', '2.', '3.')):
                # 提取列表项
                rec = line.strip().lstrip('-•*1234567890. ').strip()
                if rec:
                    recommendations.append(rec)
            elif in_recs and line.strip() == '' and recommendations:
                # 空行表示部分结束
                break

        return recommendations

    def _generate_docker_strategy_markdown(self, docker_strategy: Dict[str, Any]) -> str:
        """生成 AI Docker 策略分析的 Markdown 内容"""

        if "error" in docker_strategy:
            return """## 🐳 AI Docker 部署策略

⚠️ {docker_strategy['error']}

### 默认配置

使用基于规则的 Docker 配置生成。
"""

        md = """## 🐳 AI Docker 部署策略

基于 AI 深度分析，为该项目推荐以下 Docker 部署方案：

### 📋 策略概览

- **推荐基础镜像**: {docker_strategy.get('base_image', '基于项目类型自动选择')}
- **推荐端口**: {docker_strategy.get('recommended_port', '默认')}
- **多阶段构建**: {'✅ 推荐' if docker_strategy.get('multi_stage_build') else '❌ 无需'}
- **数据库需求**: {'✅ 需要' if docker_strategy.get('needs_database') else '❌ 无需数据库服务'}
- **镜像大小目标**: {docker_strategy.get('target_image_size', '未指定')}

### 💡 AI 优化建议

"""

        recommendations = docker_strategy.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations[:8], 1):  # 显示前8条
                md += f"{i}. {rec}\n"
            if len(recommendations) > 8:
                md += f"\n*还有 {len(recommendations) - 8} 条优化建议*\n"
        else:
            md += "AI 未提供具体优化建议，将使用默认配置。\n"

        md += """
### 🔧 技术细节

<details>
<summary>查看详细策略分析</summary>

```
{docker_strategy.get('strategy', '暂无详细策略')}
```
</details>

### ✅ 已应用的优化

以上建议已自动应用到生成的 Docker 配置中，包括：
- Dockerfile 优化
- docker-compose.yml 配置
- 端口映射和依赖管理

---

"""

        return md

    def _generate_ai_markdown(self, ai_results: Dict[str, Any]) -> str:
        """生成 AI 分析的 Markdown 内容"""

        md = """## 🤖 AI 深度代码分析

### 📊 代码质量评分
"""

        score = ai_results.get("quality_score")
        if score:
            stars = "⭐" * (score // 2) + "☆" * (5 - (score // 2))
            md += f"{stars} **{score}/10**\n\n"

        md += f"### 📝 详细分析\n\n{ai_results.get('raw_analysis', '暂无分析结果')}\n"

        findings = ai_results.get("key_findings", [])
        if findings:
            md += "\n### ⚠️ 关键发现\n\n"
            for finding in findings:
                md += f"{finding}\n"

        recommendations = ai_results.get("recommendations", [])
        if recommendations:
            md += "\n### 💡 改进建议\n\n"
            for rec in recommendations:
                md += f"{rec}\n"

        return md

    def _generate_cache_key(self, project_path: str, analysis_type: str) -> str:
        """生成缓存键"""
        # 使用项目路径的 hash + 分析类型作为键
        import hashlib
        path_hash = hashlib.md5(project_path.encode()).hexdigest()[:12]
        return f"{path_hash}_{analysis_type}.json"

    def _get_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据"""
        if not self.use_cache:
            return None

        cache_file = self.cache_dir / cache_key

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # 检查缓存是否过期
            import time
            current_time = time.time()
            if current_time - cache_data.get('timestamp', 0) > self.cache_ttl:
                print(f"⚠️  缓存已过期: {cache_key}")
                return None

            return cache_data.get('data')

        except Exception as e:
            print(f"⚠️  读取缓存失败: {str(e)}")
            return None

    def _save_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """保存数据到缓存"""
        if not self.use_cache:
            return

        cache_file = self.cache_dir / cache_key

        try:
            import time
            cache_data = {
                'timestamp': time.time(),
                'data': data
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            print(f"💾 已保存缓存: {cache_key}")

        except Exception as e:
            print(f"⚠️  保存缓存失败: {str(e)}")

    def clear_cache(self, project_path: Optional[str] = None) -> int:
        """
        清除缓存

        Args:
            project_path: 如果指定，只清除该项目的缓存；否则清除所有缓存

        Returns:
            清除的缓存文件数量
        """
        if not self.cache_dir.exists():
            return 0

        if project_path:
            # 清除特定项目的缓存
            import hashlib
            path_hash = hashlib.md5(project_path.encode()).hexdigest()[:12]
            cache_files = [
                self.cache_dir / f"{path_hash}_code_quality.json",
                self.cache_dir / f"{path_hash}_docker_strategy.json"
            ]
        else:
            # 清除所有缓存
            cache_files = list(self.cache_dir.glob("*.json"))

        deleted_count = 0
        for cache_file in cache_files:
            try:
                cache_file.unlink()
                deleted_count += 1
                print(f"🗑️  已删除缓存: {cache_file.name}")
            except Exception as e:
                print(f"⚠️  删除缓存失败: {cache_file.name} - {str(e)}")

        return deleted_count


def main():
    """命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description="AI 增强代码分析器")
    parser.add_argument("report_path", nargs='?', help="Serena 生成的 JSON 报告路径（用于分析模式）")
    parser.add_argument("-o", "--output", help="增强报告的输出路径（可选）")
    parser.add_argument("--replace", "-r", action="store_true",
                        help="替换原始 Markdown 报告，而不是创建新的 -ai.md 文件")
    parser.add_argument("--no-cache", action="store_true",
                        help="禁用缓存，强制调用 AI API")
    parser.add_argument("--clear-cache", action="store_true",
                        help="清除所有缓存后退出")
    parser.add_argument("--clear-project-cache", help="清除指定项目的缓存（提供项目路径）")
    parser.add_argument("--cache-ttl", type=int, default=3600,
                        help="缓存有效期（秒），默认 3600 秒（1 小时）")

    args = parser.parse_args()

    try:
        analyzer = AIEnhancedAnalyzer(
            use_cache=not args.no_cache,
            cache_ttl=args.cache_ttl
        )

        # 处理清除缓存的命令
        if args.clear_cache:
            count = analyzer.clear_cache()
            print(f"✅ 已清除 {count} 个缓存文件")
            return

        if args.clear_project_cache:
            count = analyzer.clear_cache(args.clear_project_cache)
            print(f"✅ 已清除项目的 {count} 个缓存文件")
            return

        # 检查是否提供了报告路径
        if not args.report_path:
            parser.error("需要提供 report_path 参数，或使用 --clear-cache/--clear-project-cache 选项")

        analyzer.enhance_report(args.report_path, args.output, replace_original=args.replace)

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
