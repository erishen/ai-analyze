#!/usr/bin/env python3
"""Tests for data_store module"""

import os
import sys
import tempfile
from pathlib import Path

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.tools.data_store import AnalysisStore  # noqa: E402


class TestAnalysisStore:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(self.tmpdir, "test.db")
        self.store = AnalysisStore(db_path=db_path)

    def test_save_and_get(self):
        rid = self.store.save(
            "test_project", "/path/to/project",
            "security", {"risk_score": 30.0},
        )
        assert rid > 0
        record = self.store.get_by_id(rid)
        assert record is not None
        assert record["project_name"] == "test_project"
        assert record["result"]["risk_score"] == 30.0

    def test_get_latest(self):
        self.store.save("proj", "/p", "security", {"score": 70})
        self.store.save("proj", "/p", "performance", {"score": 80})
        records = self.store.get_latest("proj")
        assert len(records) == 2

    def test_get_latest_by_type(self):
        self.store.save("proj", "/p", "security", {"score": 70})
        self.store.save("proj", "/p", "performance", {"score": 80})
        records = self.store.get_latest("proj", analysis_type="security")
        assert len(records) == 1
        assert records[0]["analysis_type"] == "security"

    def test_list_projects(self):
        self.store.save("proj_a", "/a", "security", {})
        self.store.save("proj_b", "/b", "security", {})
        projects = self.store.list_projects()
        assert len(projects) == 2
        names = [p["project_name"] for p in projects]
        assert "proj_a" in names
        assert "proj_b" in names

    def test_get_trend(self):
        self.store.save("proj", "/p", "security", {"risk_score": 30.0})
        self.store.save("proj", "/p", "security", {"risk_score": 20.0})
        trend = self.store.get_trend("proj", "security", "risk_score")
        assert len(trend) == 2
        assert trend[0]["value"] == 30.0
        assert trend[1]["value"] == 20.0

    def test_get_by_id_nonexistent(self):
        record = self.store.get_by_id(9999)
        assert record is None

    def test_delete_old(self):
        self.store.save("proj", "/p", "security", {})
        deleted = self.store.delete_old(days=0)
        assert deleted >= 1

    def test_save_with_metadata(self):
        rid = self.store.save(
            "proj", "/p", "security", {"score": 50},
            duration=1.5, metadata={"version": "0.2.0"},
        )
        record = self.store.get_by_id(rid)
        assert record["duration"] == 1.5
        assert record["metadata"]["version"] == "0.2.0"
