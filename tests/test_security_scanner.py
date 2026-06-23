#!/usr/bin/env python3
"""Tests for security_scanner module"""

import sys
from pathlib import Path

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.analyzers.security_scanner import (  # noqa: E402
    SecurityScanner,
    SeverityLevel,
    VulnerabilityCategory,
    VulnerabilityFinding,
    SecurityScanResult,
)


class TestSecurityScanner:
    def setup_method(self):
        self.scanner = SecurityScanner()

    def test_builtin_rules_count(self):
        assert len(self.scanner._rules) >= 12

    def test_scan_file_hardcoded_secret(self):
        code = 'password = "my_secret_123"\napi_key = "sk-abc123def456"\n'
        findings = self.scanner.scan_file("config.py", code)
        assert len(findings) >= 1
        assert any(f.rule_id == "SEC002" for f in findings)

    def test_scan_file_pickle_usage(self):
        code = "import pickle\ndata = pickle.loads(raw)\n"
        findings = self.scanner.scan_file("loader.py", code)
        assert len(findings) >= 1
        assert any(f.rule_id == "SEC003" for f in findings)

    def test_scan_file_command_injection(self):
        code = "import subprocess\nsubprocess.run(cmd, shell=True)\n"
        findings = self.scanner.scan_file("runner.py", code)
        assert len(findings) >= 1
        assert any(f.rule_id == "SEC004" for f in findings)

    def test_scan_file_weak_crypto(self):
        code = "import hashlib\nh = hashlib.md5(data)\n"
        findings = self.scanner.scan_file("hash.py", code)
        assert len(findings) >= 1
        assert any(f.rule_id == "SEC005" for f in findings)

    def test_scan_file_debug_mode(self):
        code = "DEBUG = True\n"
        findings = self.scanner.scan_file("settings.py", code)
        assert len(findings) >= 1

    def test_scan_file_clean(self):
        code = "def hello():\n    return 'world'\n"
        findings = self.scanner.scan_file("clean.py", code)
        assert len(findings) == 0

    def test_scan_project(self):
        files = {
            "config.py": 'password = "secret"\n',
            "clean.py": "x = 1\n",
        }
        result = self.scanner.scan_project(files)
        assert result.total_files_scanned == 2
        assert len(result.findings) >= 1

    def test_scan_result_risk_score(self):
        result = SecurityScanResult()
        assert result.risk_score == 0.0
        assert result.is_safe is True

    def test_scan_result_with_findings(self):
        finding = VulnerabilityFinding(
            rule_id="SEC001",
            rule_name="Test",
            category=VulnerabilityCategory.INJECTION,
            severity=SeverityLevel.HIGH,
            file_path="test.py",
            line_number=1,
            line_content="test",
            description="test",
        )
        result = SecurityScanResult(findings=[finding])
        assert result.high_count == 1
        assert result.risk_score > 0
        assert result.is_safe is False

    def test_enable_disable_rule(self):
        self.scanner.disable_rule("SEC001")
        rules = self.scanner.rules
        assert not any(r.id == "SEC001" for r in rules)
        self.scanner.enable_rule("SEC001")
        rules = self.scanner.rules
        assert any(r.id == "SEC001" for r in rules)

    def test_max_findings_limit(self):
        code = 'password = "a"\nsecret = "b"\napi_key = "c"\nprivate_key = "d"\n'
        files = {f"file{i}.py": code for i in range(10)}
        result = self.scanner.scan_project(files, max_findings=5)
        assert len(result.findings) <= 5

    def test_finding_to_dict(self):
        finding = VulnerabilityFinding(
            rule_id="SEC001",
            rule_name="Test",
            category=VulnerabilityCategory.INJECTION,
            severity=SeverityLevel.HIGH,
            file_path="test.py",
            line_number=1,
            line_content="test",
            description="test",
        )
        d = finding.to_dict()
        assert d["severity"] == "high"
        assert d["category"] == "injection"

    def test_js_eval_detection(self):
        code = "eval(userInput);\n"
        findings = self.scanner.scan_file("app.js", code)
        assert any(f.rule_id == "SEC011" for f in findings)

    def test_js_innerhtml_detection(self):
        code = "element.innerHTML = userInput;\n"
        findings = self.scanner.scan_file("dom.js", code)
        assert any(f.rule_id == "SEC012" for f in findings)
