"""Tests for analysis_integration module - comprehensive"""

import json

import pytest

from src.analysis_integration import IntegratedAnalysisResult, AnalysisIntegrator


class TestIntegratedAnalysisResult:
    def test_creation(self):
        result = IntegratedAnalysisResult(
            project_path="/tmp/test", unified_analysis={}, similarity_analysis={}, quality_scores={}
        )
        assert result.project_path == "/tmp/test"

    def test_to_dict(self):
        result = IntegratedAnalysisResult(
            project_path="/tmp/test",
            unified_analysis={"files": 5},
            similarity_analysis={"duplicates": 0},
            quality_scores={"overall": 85.0},
        )
        d = result.to_dict()
        assert d["project_path"] == "/tmp/test"
        assert "timestamp" in d
        assert d["quality_scores"]["overall"] == 85.0

    def test_to_json(self):
        result = IntegratedAnalysisResult(
            project_path="/tmp/test", unified_analysis={}, similarity_analysis={}, quality_scores={}
        )
        j = result.to_json()
        data = json.loads(j)
        assert data["project_path"] == "/tmp/test"

    def test_custom_timestamp(self):
        result = IntegratedAnalysisResult(
            project_path="/tmp/test",
            unified_analysis={},
            similarity_analysis={},
            quality_scores={},
            timestamp="2024-01-01T00:00:00",
            analysis_date="2024-01-01",
        )
        d = result.to_dict()
        assert d["timestamp"] == "2024-01-01T00:00:00"
        assert d["analysis_date"] == "2024-01-01"


class TestAnalysisIntegrator:
    def test_init(self):
        integrator = AnalysisIntegrator(project_path="/tmp/test")
        assert integrator.project_path == "/tmp/test"
        assert integrator.similarity_detector is not None
        assert integrator.quality_scorer is not None

    @pytest.mark.asyncio
    async def test_integrate_analysis(self):
        integrator = AnalysisIntegrator(project_path="/tmp/test")
        unified = {"files": [], "summary": {}}
        result = await integrator.integrate_analysis(unified)
        assert isinstance(result, IntegratedAnalysisResult)
        assert result.project_path == "/tmp/test"
        assert "similarity_analysis" in result.to_dict()
        assert "quality_scores" in result.to_dict()

    @pytest.mark.asyncio
    async def test_integrate_with_source_files(self):
        integrator = AnalysisIntegrator(project_path="/tmp/test")
        unified = {"files": [], "summary": {}}
        source_files = {"test.py": "def foo():\n    pass\n"}
        result = await integrator.integrate_analysis(unified, source_files=source_files)
        assert isinstance(result, IntegratedAnalysisResult)
