#!/usr/bin/env python3
"""
PR Diff 分析测试
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from src.tools.pr_diff import (
    parse_git_diff,
    DiffHunk,
    FileDiff,
    _assess_risk,
    _generate_recommendation,
)


class TestParseGitDiff:
    """git diff 解析测试"""

    def test_parse_modified_file(self):
        diff = """diff --git a/src/main.py b/src/main.py
index abc1234..def5678 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,7 +10,8 @@ class MyClass:
     def hello(self):
-        print("old")
+        print("new")
+        return True
"""
        file_diffs = parse_git_diff(diff)
        assert len(file_diffs) == 1
        assert file_diffs[0].file_path == "src/main.py"
        assert file_diffs[0].change_type == "modified"
        assert file_diffs[0].additions == 2
        assert file_diffs[0].deletions == 1
        assert len(file_diffs[0].hunks) == 1
        assert file_diffs[0].hunks[0].old_start == 10
        assert file_diffs[0].hunks[0].new_start == 10

    def test_parse_new_file(self):
        diff = """diff --git a/src/new.py b/src/new.py
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/src/new.py
@@ -0,0 +1,5 @@
+def hello():
+    print("hello")
+    return True
"""
        file_diffs = parse_git_diff(diff)
        assert len(file_diffs) == 1
        assert file_diffs[0].change_type == "added"
        assert file_diffs[0].additions == 3

    def test_parse_deleted_file(self):
        diff = """diff --git a/src/old.py b/src/old.py
deleted file mode 100644
index abc1234..0000000
--- a/src/old.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def old():
-    pass
"""
        file_diffs = parse_git_diff(diff)
        assert len(file_diffs) == 1
        assert file_diffs[0].change_type == "deleted"
        assert file_diffs[0].deletions == 2

    def test_parse_multiple_files(self):
        diff = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,2 +1,3 @@
+new line
diff --git a/b.js b/b.js
--- a/b.js
+++ b/b.js
@@ -1,2 +1,2 @@
-old line
+new line
"""
        file_diffs = parse_git_diff(diff)
        assert len(file_diffs) == 2

    def test_parse_empty_diff(self):
        file_diffs = parse_git_diff("")
        assert len(file_diffs) == 0


class TestRiskAssessment:
    """风险评估测试"""

    def test_low_risk(self):
        assert _assess_risk(0, 5, 100) == "low"

    def test_medium_risk(self):
        assert _assess_risk(5, 15, 100) == "medium"

    def test_high_risk(self):
        assert _assess_risk(10, 30, 100) == "high"

    def test_zero_additions(self):
        assert _assess_risk(0, 0, 0) == "low"


class TestRecommendation:
    """审查建议测试"""

    def test_no_smells(self):
        rec = _generate_recommendation(0, 0, 100)
        assert "No code smells" in rec

    def test_minor_issues(self):
        rec = _generate_recommendation(2, 1, 100)
        assert "Minor issues" in rec

    def test_significant_issues(self):
        rec = _generate_recommendation(10, 3, 100)
        assert "Significant issues" in rec

    def test_large_pr(self):
        rec = _generate_recommendation(0, 0, 600)
        assert "Large PR" in rec

    def test_zero_additions(self):
        rec = _generate_recommendation(0, 0, 0)
        assert "No code additions" in rec
