"""
代码质量评分系统
用于计算和评估代码质量
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging


@dataclass
class QualityMetrics:
    """质量指标"""
    
    # 复杂度指标
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    
    # 代码坏味道
    code_smells: int = 0
    
    # 重复代码
    duplication_ratio: float = 0.0
    
    # 测试覆盖率
    test_coverage: float = 0.0
    
    # 文档覆盖率
    documentation_ratio: float = 0.0
    
    # 代码行数
    lines_of_code: int = 0
    
    # 注释行数
    comment_lines: int = 0
    
    # 空行数
    blank_lines: int = 0
    
    # 其他指标
    maintainability_index: float = 0.0
    technical_debt: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "cognitive_complexity": self.cognitive_complexity,
            "code_smells": self.code_smells,
            "duplication_ratio": self.duplication_ratio,
            "test_coverage": self.test_coverage,
            "documentation_ratio": self.documentation_ratio,
            "lines_of_code": self.lines_of_code,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
            "maintainability_index": self.maintainability_index,
            "technical_debt": self.technical_debt
        }


@dataclass
class QualityScore:
    """质量评分"""
    
    overall_score: float = 0.0  # 0-100
    complexity_score: float = 0.0  # 0-100
    maintainability_score: float = 0.0  # 0-100
    reliability_score: float = 0.0  # 0-100
    security_score: float = 0.0  # 0-100
    
    # 评级
    grade: str = "F"  # A, B, C, D, F
    
    # 详细指标
    metrics: QualityMetrics = field(default_factory=QualityMetrics)
    
    # 建议
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "overall_score": self.overall_score,
            "complexity_score": self.complexity_score,
            "maintainability_score": self.maintainability_score,
            "reliability_score": self.reliability_score,
            "security_score": self.security_score,
            "grade": self.grade,
            "metrics": self.metrics.to_dict(),
            "recommendations": self.recommendations
        }


class QualityScorer:
    """质量评分器"""
    
    def __init__(self):
        """初始化质量评分器"""
        self.logger = logging.getLogger("ai-analyze.quality")
    
    def calculate_score(self, metrics: QualityMetrics) -> QualityScore:
        """计算质量评分
        
        Args:
            metrics: 质量指标
        
        Returns:
            质量评分
        """
        score = QualityScore(metrics=metrics)
        
        # 计算各个维度的评分
        score.complexity_score = self._calculate_complexity_score(metrics)
        score.maintainability_score = self._calculate_maintainability_score(metrics)
        score.reliability_score = self._calculate_reliability_score(metrics)
        score.security_score = self._calculate_security_score(metrics)
        
        # 计算总体评分
        score.overall_score = (
            score.complexity_score * 0.25 +
            score.maintainability_score * 0.35 +
            score.reliability_score * 0.25 +
            score.security_score * 0.15
        )
        
        # 确定评级
        score.grade = self._get_grade(score.overall_score)
        
        # 生成建议
        score.recommendations = self._generate_recommendations(metrics, score)
        
        return score
    
    def _calculate_complexity_score(self, metrics: QualityMetrics) -> float:
        """计算复杂度评分"""
        # 圈复杂度评分
        if metrics.cyclomatic_complexity <= 5:
            cc_score = 100
        elif metrics.cyclomatic_complexity <= 10:
            cc_score = 80
        elif metrics.cyclomatic_complexity <= 15:
            cc_score = 60
        else:
            cc_score = max(0, 100 - (metrics.cyclomatic_complexity - 15) * 5)
        
        # 认知复杂度评分
        if metrics.cognitive_complexity <= 10:
            cog_score = 100
        elif metrics.cognitive_complexity <= 20:
            cog_score = 80
        elif metrics.cognitive_complexity <= 30:
            cog_score = 60
        else:
            cog_score = max(0, 100 - (metrics.cognitive_complexity - 30) * 2)
        
        return (cc_score + cog_score) / 2
    
    def _calculate_maintainability_score(self, metrics: QualityMetrics) -> float:
        """计算可维护性评分"""
        # 代码坏味道评分
        smell_score = max(0, 100 - metrics.code_smells * 5)
        
        # 重复代码评分
        dup_score = max(0, 100 - metrics.duplication_ratio * 100)
        
        # 文档覆盖率评分
        doc_score = metrics.documentation_ratio * 100
        
        # 可维护性指数评分
        mi_score = metrics.maintainability_index
        
        return (smell_score * 0.3 + dup_score * 0.3 + doc_score * 0.2 + mi_score * 0.2)
    
    def _calculate_reliability_score(self, metrics: QualityMetrics) -> float:
        """计算可靠性评分"""
        # 测试覆盖率评分
        coverage_score = metrics.test_coverage * 100
        
        # 技术债务评分
        debt_score = max(0, 100 - metrics.technical_debt * 10)
        
        return (coverage_score * 0.6 + debt_score * 0.4)
    
    def _calculate_security_score(self, metrics: QualityMetrics) -> float:
        """计算安全性评分"""
        # 简化版本：基于代码坏味道和复杂度
        # 实际应该使用专门的安全分析工具
        
        # 代码坏味道中可能包含安全问题
        security_issues = metrics.code_smells // 2
        
        return max(0, 100 - security_issues * 10)
    
    def _get_grade(self, score: float) -> str:
        """获取评级
        
        Args:
            score: 评分
        
        Returns:
            评级 (A-F)
        """
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _generate_recommendations(
        self,
        metrics: QualityMetrics,
        score: QualityScore
    ) -> List[str]:
        """生成建议
        
        Args:
            metrics: 质量指标
            score: 质量评分
        
        Returns:
            建议列表
        """
        recommendations = []
        
        # 复杂度建议
        if metrics.cyclomatic_complexity > 10:
            recommendations.append(
                f"圈复杂度过高 ({metrics.cyclomatic_complexity:.1f})，"
                "建议重构函数，拆分为更小的函数"
            )
        
        if metrics.cognitive_complexity > 20:
            recommendations.append(
                f"认知复杂度过高 ({metrics.cognitive_complexity:.1f})，"
                "建议简化逻辑，提高代码可读性"
            )
        
        # 代码坏味道建议
        if metrics.code_smells > 5:
            recommendations.append(
                f"发现 {metrics.code_smells} 个代码坏味道，"
                "建议进行代码审查和重构"
            )
        
        # 重复代码建议
        if metrics.duplication_ratio > 0.1:
            recommendations.append(
                f"重复代码比例过高 ({metrics.duplication_ratio:.1%})，"
                "建议提取公共代码到共享模块"
            )
        
        # 测试覆盖率建议
        if metrics.test_coverage < 0.7:
            recommendations.append(
                f"测试覆盖率不足 ({metrics.test_coverage:.1%})，"
                "建议增加单元测试"
            )
        
        # 文档覆盖率建议
        if metrics.documentation_ratio < 0.5:
            recommendations.append(
                f"文档覆盖率不足 ({metrics.documentation_ratio:.1%})，"
                "建议添加更多代码注释和文档"
            )
        
        # 技术债务建议
        if metrics.technical_debt > 0.5:
            recommendations.append(
                f"技术债务较高 ({metrics.technical_debt:.1f})，"
                "建议优先处理高优先级的技术债务"
            )
        
        return recommendations
    
    def print_score(self, score: QualityScore):
        """打印评分
        
        Args:
            score: 质量评分
        """
        print("\n" + "="*80)
        print("代码质量评分")
        print("="*80)
        
        print(f"\n总体评分: {score.overall_score:.1f}/100 [{score.grade}]")
        print(f"  复杂度评分: {score.complexity_score:.1f}/100")
        print(f"  可维护性评分: {score.maintainability_score:.1f}/100")
        print(f"  可靠性评分: {score.reliability_score:.1f}/100")
        print(f"  安全性评分: {score.security_score:.1f}/100")
        
        print(f"\n详细指标:")
        print(f"  圈复杂度: {score.metrics.cyclomatic_complexity:.1f}")
        print(f"  认知复杂度: {score.metrics.cognitive_complexity:.1f}")
        print(f"  代码坏味道: {score.metrics.code_smells}")
        print(f"  重复代码比例: {score.metrics.duplication_ratio:.1%}")
        print(f"  测试覆盖率: {score.metrics.test_coverage:.1%}")
        print(f"  文档覆盖率: {score.metrics.documentation_ratio:.1%}")
        print(f"  代码行数: {score.metrics.lines_of_code}")
        print(f"  注释行数: {score.metrics.comment_lines}")
        print(f"  空行数: {score.metrics.blank_lines}")
        print(f"  可维护性指数: {score.metrics.maintainability_index:.1f}")
        print(f"  技术债务: {score.metrics.technical_debt:.1f}")
        
        if score.recommendations:
            print(f"\n建议:")
            for i, rec in enumerate(score.recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    # 测试质量评分
    print("测试代码质量评分:")
    
    # 创建测试指标
    metrics = QualityMetrics(
        cyclomatic_complexity=8.5,
        cognitive_complexity=15.2,
        code_smells=3,
        duplication_ratio=0.08,
        test_coverage=0.75,
        documentation_ratio=0.6,
        lines_of_code=500,
        comment_lines=50,
        blank_lines=30,
        maintainability_index=75.0,
        technical_debt=0.3
    )
    
    # 创建评分器
    scorer = QualityScorer()
    
    # 计算评分
    score = scorer.calculate_score(metrics)
    
    # 打印评分
    scorer.print_score(score)
