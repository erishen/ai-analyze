"""
分析集成模块
将相似性检测和质量评分集成到完整分析流程中
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .similarity import SimilarityDetector, CodeBlock
from .quality_score import QualityScorer, QualityMetrics


@dataclass
class IntegratedAnalysisResult:
    """集成分析结果"""

    project_path: str
    unified_analysis: Dict[str, Any]
    similarity_analysis: Dict[str, Any]
    quality_scores: Dict[str, Any]
    timestamp: Optional[str] = None
    analysis_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        from datetime import datetime

        now = datetime.now()
        timestamp = self.timestamp or now.isoformat()
        analysis_date = self.analysis_date or now.strftime("%Y-%m-%d %H:%M:%S")

        return {
            "project_path": self.project_path,
            "timestamp": timestamp,
            "analysis_date": analysis_date,
            "unified_analysis": self.unified_analysis,
            "similarity_analysis": self.similarity_analysis,
            "quality_scores": self.quality_scores,
        }

    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class AnalysisIntegrator:
    """分析集成器"""

    def __init__(self, project_path: str):
        """初始化分析集成器

        Args:
            project_path: 项目路径
        """
        self.project_path = project_path
        self.logger = logging.getLogger("ai-analyze.integration")
        self.similarity_detector = SimilarityDetector()
        self.quality_scorer = QualityScorer()

    async def integrate_analysis(
        self, unified_analysis: Dict[str, Any], source_files: Optional[Dict[str, str]] = None
    ) -> IntegratedAnalysisResult:
        """集成分析结果

        Args:
            unified_analysis: 统一分析结果
            source_files: 源代码文件（可选）

        Returns:
            集成分析结果
        """
        self.logger.info("开始集成分析...")

        # 1. 相似性检测
        similarity_analysis = await self._analyze_similarity(unified_analysis, source_files)

        # 2. 质量评分
        quality_scores = await self._analyze_quality(unified_analysis)

        # 3. 创建集成结果
        result = IntegratedAnalysisResult(
            project_path=self.project_path,
            unified_analysis=unified_analysis,
            similarity_analysis=similarity_analysis,
            quality_scores=quality_scores,
        )

        self.logger.info("集成分析完成")
        return result

    async def _analyze_similarity(
        self, unified_analysis: Dict[str, Any], source_files: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """分析代码相似性

        Args:
            unified_analysis: 统一分析结果
            source_files: 源代码文件

        Returns:
            相似性分析结果
        """
        self.logger.info("分析代码相似性...")

        try:
            # 从统一分析结果中提取代码块
            code_blocks = self._extract_code_blocks(unified_analysis)

            # 添加代码块到检测器
            self.similarity_detector.add_code_blocks(code_blocks)

            # 检测相似性
            duplicates = self.similarity_detector.detect_duplicates()
            similar = self.similarity_detector.detect_similar(threshold=0.7)

            # 统计信息
            total_blocks = len(self.similarity_detector.code_blocks)
            duplicate_pairs = len(duplicates)
            similar_pairs = len(similar)

            # 计算重复代码比例
            duplicate_lines = sum(d.block1.line_count + d.block2.line_count for d in duplicates)
            total_lines = sum(b.line_count for b in code_blocks)
            duplication_ratio = duplicate_lines / total_lines if total_lines > 0 else 0

            result = {
                "total_blocks": total_blocks,
                "duplicate_pairs": duplicate_pairs,
                "similar_pairs": similar_pairs,
                "duplication_ratio": duplication_ratio,
                "duplicates": [
                    {
                        "file1": d.block1.file_path,
                        "line1": d.block1.start_line,
                        "file2": d.block2.file_path,
                        "line2": d.block2.start_line,
                        "lines": d.block1.line_count,
                        "similarity": d.similarity,
                    }
                    for d in duplicates[:10]  # 只保存前 10 个
                ],
                "similar": [
                    {
                        "file1": s.block1.file_path,
                        "line1": s.block1.start_line,
                        "file2": s.block2.file_path,
                        "line2": s.block2.start_line,
                        "similarity": s.similarity,
                    }
                    for s in similar[:10]  # 只保存前 10 个
                ],
            }

            self.logger.info(f"相似性分析完成: {duplicate_pairs} 个重复, " f"{similar_pairs} 个相似, 重复率 {duplication_ratio:.1%}")

            return result

        except Exception as e:
            self.logger.error(f"相似性分析失败: {e}")
            return {
                "error": str(e),
                "total_blocks": 0,
                "duplicate_pairs": 0,
                "similar_pairs": 0,
                "duplication_ratio": 0,
            }

    async def _analyze_quality(self, unified_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """分析代码质量

        Args:
            unified_analysis: 统一分析结果

        Returns:
            质量评分结果
        """
        self.logger.info("分析代码质量...")

        try:
            # 从统一分析结果中提取指标
            metrics = self._extract_metrics(unified_analysis)

            # 计算质量评分
            score = self.quality_scorer.calculate_score(metrics)

            result = {
                "overall_score": score.overall_score,
                "complexity_score": score.complexity_score,
                "maintainability_score": score.maintainability_score,
                "reliability_score": score.reliability_score,
                "security_score": score.security_score,
                "grade": score.grade,
                "metrics": score.metrics.to_dict(),
                "recommendations": score.recommendations,
            }

            self.logger.info(f"质量评分完成: {score.overall_score:.1f}/100 [{score.grade}]")

            return result

        except Exception as e:
            self.logger.error(f"质量评分失败: {e}")
            return {"error": str(e), "overall_score": 0, "grade": "F"}

    def _extract_code_blocks(self, unified_analysis: Dict[str, Any]) -> List[CodeBlock]:
        """从统一分析结果中提取代码块

        Args:
            unified_analysis: 统一分析结果

        Returns:
            代码块列表
        """
        blocks = []

        try:
            files = unified_analysis.get("files", [])

            for file_data in files:
                file_path = file_data.get("file_path", "")

                # 从函数中提取代码块
                functions = file_data.get("functions", [])
                for func in functions:
                    block = CodeBlock(
                        file_path=file_path,
                        start_line=func.get("start_line", 0),
                        end_line=func.get("end_line", 0),
                        content=func.get("content", ""),
                        language=file_data.get("language", "unknown"),
                    )
                    blocks.append(block)

                # 从类中提取代码块
                classes = file_data.get("classes", [])
                for cls in classes:
                    block = CodeBlock(
                        file_path=file_path,
                        start_line=cls.get("start_line", 0),
                        end_line=cls.get("end_line", 0),
                        content=cls.get("content", ""),
                        language=file_data.get("language", "unknown"),
                    )
                    blocks.append(block)

        except Exception as e:
            self.logger.warning(f"提取代码块失败: {e}")

        return blocks

    def _extract_metrics(self, unified_analysis: Dict[str, Any]) -> QualityMetrics:
        """从统一分析结果中提取质量指标

        Args:
            unified_analysis: 统一分析结果

        Returns:
            质量指标
        """
        metrics = QualityMetrics()

        try:
            # 计算平均复杂度
            files = unified_analysis.get("files", [])
            complexities = []
            code_smells_list = []
            total_lines = 0

            for file_data in files:
                # 收集复杂度
                functions = file_data.get("functions", [])
                for func in functions:
                    cc = func.get("cyclomatic_complexity", 0)
                    if cc > 0:
                        complexities.append(cc)

                # 收集代码坏味道
                smells = file_data.get("code_smells", 0)
                code_smells_list.append(smells)

                # 统计代码行数
                total_lines += file_data.get("lines_of_code", 0)

            # 计算平均值
            if complexities:
                metrics.cyclomatic_complexity = sum(complexities) / len(complexities)

            if code_smells_list:
                metrics.code_smells = sum(code_smells_list)

            metrics.lines_of_code = total_lines

            # 从统一分析结果中获取其他指标
            metrics.duplication_ratio = unified_analysis.get("duplication_ratio", 0)
            metrics.test_coverage = unified_analysis.get("test_coverage", 0)
            metrics.documentation_ratio = unified_analysis.get("documentation_ratio", 0)
            metrics.maintainability_index = unified_analysis.get("maintainability_index", 75)
            metrics.technical_debt = unified_analysis.get("technical_debt", 0)

        except Exception as e:
            self.logger.warning(f"提取指标失败: {e}")

        return metrics

    def save_results(self, result: IntegratedAnalysisResult, output_dir: Optional[Path] = None) -> Path:
        """保存分析结果

        Args:
            result: 集成分析结果
            output_dir: 输出目录

        Returns:
            保存的文件路径
        """
        if output_dir is None:
            output_dir = Path(self.project_path) / "reports"

        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存集成分析结果
        # 从项目路径提取项目名
        project_name = Path(self.project_path).name or "project"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"integrated_analysis_{project_name}_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.to_json())

        self.logger.info(f"分析结果已保存: {output_file}")

        return output_file
