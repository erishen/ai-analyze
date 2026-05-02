"""Tests for quality_score module"""


from src.quality_score import QualityMetrics, QualityScore, QualityScorer


class TestQualityMetrics:
    def test_default_values(self):
        m = QualityMetrics()
        assert m.cyclomatic_complexity == 0.0
        assert m.code_smells == 0
        assert m.test_coverage == 0.0

    def test_to_dict(self):
        m = QualityMetrics(cyclomatic_complexity=5, code_smells=2)
        d = m.to_dict()
        assert d["cyclomatic_complexity"] == 5
        assert d["code_smells"] == 2


class TestQualityScore:
    def test_default_values(self):
        s = QualityScore()
        assert s.overall_score == 0.0
        assert s.grade == "F"

    def test_to_dict(self):
        s = QualityScore(overall_score=85.0, grade="A")
        d = s.to_dict()
        assert d["overall_score"] == 85.0
        assert d["grade"] == "A"


class TestQualityScorer:
    def test_calculate_score_returns_quality_score(self):
        scorer = QualityScorer()
        metrics = QualityMetrics(
            cyclomatic_complexity=5,
            cognitive_complexity=10,
            code_smells=0,
            duplication_ratio=0.0,
            test_coverage=80.0,
            documentation_ratio=50.0,
        )
        score = scorer.calculate_score(metrics)
        assert isinstance(score, QualityScore)
        assert 0 <= score.overall_score <= 100
        assert score.complexity_score <= 100
        assert score.maintainability_score <= 100
        assert score.reliability_score <= 100
        assert score.security_score <= 100

    def test_high_quality_has_high_score(self):
        scorer = QualityScorer()
        metrics = QualityMetrics(
            cyclomatic_complexity=3,
            cognitive_complexity=5,
            code_smells=0,
            duplication_ratio=0.0,
            test_coverage=90.0,
            documentation_ratio=80.0,
        )
        score = scorer.calculate_score(metrics)
        assert score.complexity_score > 50
        assert score.overall_score <= 100

    def test_low_complexity_score(self):
        scorer = QualityScorer()
        metrics = QualityMetrics(
            cyclomatic_complexity=30,
            cognitive_complexity=50,
        )
        score = scorer.calculate_score(metrics)
        assert score.complexity_score < 50
        assert score.overall_score <= 100

    def test_score_never_exceeds_100(self):
        """Regression: overall_score must never exceed 100"""
        scorer = QualityScorer()
        metrics = QualityMetrics(
            cyclomatic_complexity=1,
            cognitive_complexity=1,
            code_smells=0,
            duplication_ratio=0.0,
            test_coverage=1.0,
            documentation_ratio=1.0,
            maintainability_index=100.0,
        )
        score = scorer.calculate_score(metrics)
        assert score.overall_score <= 100
