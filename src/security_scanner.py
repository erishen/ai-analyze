#!/usr/bin/env python3
"""
安全漏洞扫描模块
基于 AST 和模式匹配识别潜在安全漏洞
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """漏洞严重程度"""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def weight(self) -> float:
        """严重程度权重"""
        weights = {
            SeverityLevel.INFO: 0.1,
            SeverityLevel.LOW: 0.25,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.HIGH: 0.75,
            SeverityLevel.CRITICAL: 1.0,
        }
        return weights[self]


class VulnerabilityCategory(Enum):
    """漏洞类别"""

    INJECTION = "injection"
    AUTHENTICATION = "authentication"
    SENSITIVE_DATA = "sensitive_data"
    MISCONFIGURATION = "misconfiguration"
    CRYPTO = "crypto"
    DEPENDENCY = "dependency"
    INPUT_VALIDATION = "input_validation"
    ERROR_HANDLING = "error_handling"
    CONCURRENCY = "concurrency"


@dataclass
class VulnerabilityRule:
    """漏洞检测规则"""

    id: str
    name: str
    description: str
    category: VulnerabilityCategory
    severity: SeverityLevel
    patterns: List[str]
    file_patterns: List[str] = field(default_factory=lambda: [".*"])
    languages: List[str] = field(default_factory=lambda: ["all"])
    remediation: str = ""
    references: List[str] = field(default_factory=list)
    enabled: bool = True

    def matches_file(self, file_path: str) -> bool:
        """检查规则是否适用于指定文件"""
        import os

        ext = os.path.splitext(file_path)[1].lstrip(".")
        if "all" in self.languages:
            return True
        return ext in self.languages


@dataclass
class VulnerabilityFinding:
    """漏洞发现"""

    rule_id: str
    rule_name: str
    category: VulnerabilityCategory
    severity: SeverityLevel
    file_path: str
    line_number: int
    line_content: str
    description: str
    remediation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category.value,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "line_content": self.line_content,
            "description": self.description,
            "remediation": self.remediation,
        }


@dataclass
class SecurityScanResult:
    """安全扫描结果"""

    findings: List[VulnerabilityFinding] = field(default_factory=list)
    total_files_scanned: int = 0
    scan_duration: float = 0.0

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SeverityLevel.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SeverityLevel.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SeverityLevel.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SeverityLevel.LOW)

    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SeverityLevel.INFO)

    @property
    def risk_score(self) -> float:
        """计算风险评分 (0-100)"""
        if not self.findings:
            return 0.0
        weighted_sum = sum(f.severity.weight for f in self.findings)
        # 最多 10 个严重漏洞即满分
        raw_score = min(100, (weighted_sum / 10.0) * 100)
        return round(raw_score, 1)

    @property
    def is_safe(self) -> bool:
        """是否安全（无高危及以上漏洞）"""
        return self.critical_count == 0 and self.high_count == 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_findings": len(self.findings),
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "info_count": self.info_count,
            "risk_score": self.risk_score,
            "is_safe": self.is_safe,
            "total_files_scanned": self.total_files_scanned,
            "scan_duration": round(self.scan_duration, 3),
            "findings": [f.to_dict() for f in self.findings],
        }


class SecurityScanner:
    """安全漏洞扫描器"""

    def __init__(self, custom_rules: Optional[List[VulnerabilityRule]] = None):
        self.logger = logging.getLogger("ai-analyze.security_scanner")
        self._rules: List[VulnerabilityRule] = self._builtin_rules()
        if custom_rules:
            self._rules.extend(custom_rules)

    @property
    def rules(self) -> List[VulnerabilityRule]:
        """获取所有规则"""
        return [r for r in self._rules if r.enabled]

    def enable_rule(self, rule_id: str) -> None:
        """启用规则"""
        for rule in self._rules:
            if rule.id == rule_id:
                rule.enabled = True
                return

    def disable_rule(self, rule_id: str) -> None:
        """禁用规则"""
        for rule in self._rules:
            if rule.id == rule_id:
                rule.enabled = False
                return

    def scan_file(self, file_path: str, content: str) -> List[VulnerabilityFinding]:
        """扫描单个文件"""
        findings: List[VulnerabilityFinding] = []
        lines = content.split("\n")

        for rule in self.rules:
            if not rule.matches_file(file_path):
                continue

            for pattern in rule.patterns:
                try:
                    compiled = re.compile(pattern)
                except re.error:
                    self.logger.warning("Invalid regex pattern in rule %s: %s", rule.id, pattern)
                    continue

                for line_num, line in enumerate(lines, 1):
                    if compiled.search(line):
                        findings.append(
                            VulnerabilityFinding(
                                rule_id=rule.id,
                                rule_name=rule.name,
                                category=rule.category,
                                severity=rule.severity,
                                file_path=file_path,
                                line_number=line_num,
                                line_content=line.strip(),
                                description=rule.description,
                                remediation=rule.remediation,
                            )
                        )

        return findings

    def scan_project(
        self, files: Dict[str, str], max_findings: int = 500
    ) -> SecurityScanResult:
        """扫描项目

        Args:
            files: 文件路径到内容的映射
            max_findings: 最大发现数限制
        """
        import time

        start = time.time()
        all_findings: List[VulnerabilityFinding] = []

        for file_path, content in files.items():
            if len(all_findings) >= max_findings:
                self.logger.info("Reached max_findings limit: %d", max_findings)
                break

            findings = self.scan_file(file_path, content)
            all_findings.extend(findings)

        # 按严重程度排序
        severity_order = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 3,
            SeverityLevel.INFO: 4,
        }
        all_findings.sort(key=lambda f: severity_order.get(f.severity, 99))

        duration = time.time() - start
        return SecurityScanResult(
            findings=all_findings[:max_findings],
            total_files_scanned=len(files),
            scan_duration=duration,
        )

    def _builtin_rules(self) -> List[VulnerabilityRule]:
        """内置安全检测规则"""
        return [
            # SQL 注入
            VulnerabilityRule(
                id="SEC001",
                name="SQL Injection Risk",
                description="Potential SQL injection: string formatting/concatenation in SQL queries",
                category=VulnerabilityCategory.INJECTION,
                severity=SeverityLevel.HIGH,
                patterns=[
                    r'execute\s*\(\s*f["\'].*SELECT',
                    r'execute\s*\(\s*f["\'].*INSERT',
                    r'execute\s*\(\s*f["\'].*UPDATE',
                    r'execute\s*\(\s*f["\'].*DELETE',
                    r'execute\s*\(\s*["\'].*%s',
                    r'execute\s*\(\s*["\'].*\+',
                ],
                languages=["py"],
                remediation="Use parameterized queries instead of string formatting",
                references=["https://owasp.org/www-community/attacks/SQL_Injection"],
            ),
            # 硬编码密码
            VulnerabilityRule(
                id="SEC002",
                name="Hardcoded Secret",
                description="Possible hardcoded password/secret in source code",
                category=VulnerabilityCategory.SENSITIVE_DATA,
                severity=SeverityLevel.HIGH,
                patterns=[
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']',
                    r'api_key\s*=\s*["\'][^"\']+["\']',
                    r'private_key\s*=\s*["\'][^"\']+["\']',
                    r'token\s*=\s*["\'][^"\']{20,}["\']',
                ],
                languages=["all"],
                remediation="Use environment variables or secret management tools",
            ),
            # 不安全的反序列化
            VulnerabilityRule(
                id="SEC003",
                name="Insecure Deserialization",
                description="Use of pickle/yaml.load can lead to arbitrary code execution",
                category=VulnerabilityCategory.INJECTION,
                severity=SeverityLevel.CRITICAL,
                patterns=[
                    r'pickle\.loads?\(',
                    r'yaml\.load\(',
                    r'marshal\.loads?\(',
                    r'shelve\.open\(',
                ],
                languages=["py"],
                remediation="Use yaml.safe_load() or json for safe deserialization",
            ),
            # 命令注入
            VulnerabilityRule(
                id="SEC004",
                name="Command Injection",
                description="Potential command injection via shell=True or unsanitized input",
                category=VulnerabilityCategory.INJECTION,
                severity=SeverityLevel.CRITICAL,
                patterns=[
                    r'subprocess\.\w+\(.*shell\s*=\s*True',
                    r'os\.system\s*\(',
                    r'os\.popen\s*\(',
                    r'eval\s*\(',
                    r'exec\s*\(',
                ],
                languages=["py"],
                remediation="Avoid shell=True; use subprocess with argument lists",
            ),
            # 弱加密
            VulnerabilityRule(
                id="SEC005",
                name="Weak Cryptography",
                description="Use of weak hash algorithms or encryption",
                category=VulnerabilityCategory.CRYPTO,
                severity=SeverityLevel.MEDIUM,
                patterns=[
                    r'hashlib\.md5\s*\(',
                    r'hashlib\.sha1\s*\(',
                    r'DES\.new\s*\(',
                    r'ARC4\.new\s*\(',
                ],
                languages=["py"],
                remediation="Use SHA-256+ for hashing, AES for encryption",
            ),
            # 不安全的 HTTP 请求
            VulnerabilityRule(
                id="SEC006",
                name="Insecure HTTP",
                description="HTTP connection without TLS",
                category=VulnerabilityCategory.MISCONFIGURATION,
                severity=SeverityLevel.MEDIUM,
                patterns=[
                    r'requests\.(get|post|put|delete|patch)\s*\(\s*["\']http://',
                    r'urllib\.request\.urlopen\s*\(\s*["\']http://',
                ],
                languages=["py"],
                remediation="Use HTTPS instead of HTTP for all external requests",
            ),
            # 调试模式
            VulnerabilityRule(
                id="SEC007",
                name="Debug Mode Enabled",
                description="Debug mode should be disabled in production",
                category=VulnerabilityCategory.MISCONFIGURATION,
                severity=SeverityLevel.MEDIUM,
                patterns=[
                    r'DEBUG\s*=\s*True',
                    r'app\.debug\s*=\s*True',
                    r'app\.run\s*\([^)]*debug\s*=\s*True',
                ],
                languages=["py"],
                remediation="Set DEBUG=False in production environments",
            ),
            # 异常信息泄露
            VulnerabilityRule(
                id="SEC008",
                name="Error Information Disclosure",
                description="Stack trace or error details exposed to user",
                category=VulnerabilityCategory.ERROR_HANDLING,
                severity=SeverityLevel.LOW,
                patterns=[
                    r'traceback\.print_exc\s*\(\s*\)',
                    r'raise\s+\w+.*\n.*return\s+str\(',
                    r'return\s+str\(e\)',
                ],
                languages=["py"],
                remediation="Return generic error messages; log details server-side",
            ),
            # 不安全的文件操作
            VulnerabilityRule(
                id="SEC009",
                name="Path Traversal Risk",
                description="File path may be user-controlled without validation",
                category=VulnerabilityCategory.INPUT_VALIDATION,
                severity=SeverityLevel.HIGH,
                patterns=[
                    r'open\s*\(\s*[^)]*\+\s*',
                    r'os\.path\.join\s*\([^)]*request',
                    r'open\s*\(\s*request\.',
                ],
                languages=["py"],
                remediation="Validate and sanitize all file paths; use allowlists",
            ),
            # 不安全的 CORS
            VulnerabilityRule(
                id="SEC010",
                name="Insecure CORS",
                description="CORS configured to allow all origins",
                category=VulnerabilityCategory.MISCONFIGURATION,
                severity=SeverityLevel.MEDIUM,
                patterns=[
                    r'CORS.*\*',
                    r'Access-Control-Allow-Origin.*\*',
                    r'allow_origins.*\*',
                ],
                languages=["py", "js", "ts"],
                remediation="Restrict CORS to specific trusted domains",
            ),
            # eval 在 JavaScript 中
            VulnerabilityRule(
                id="SEC011",
                name="JavaScript eval Usage",
                description="eval() can execute arbitrary code",
                category=VulnerabilityCategory.INJECTION,
                severity=SeverityLevel.HIGH,
                patterns=[
                    r'\beval\s*\(',
                    r'new\s+Function\s*\(',
                ],
                languages=["js", "ts"],
                remediation="Avoid eval(); use JSON.parse() or other safe alternatives",
            ),
            # innerHTML 风险
            VulnerabilityRule(
                id="SEC012",
                name="XSS via innerHTML",
                description="innerHTML assignment may lead to XSS",
                category=VulnerabilityCategory.INPUT_VALIDATION,
                severity=SeverityLevel.HIGH,
                patterns=[
                    r'\.innerHTML\s*=',
                    r'\.outerHTML\s*=',
                    r'document\.write\s*\(',
                ],
                languages=["js", "ts"],
                remediation="Use textContent or DOM API to prevent XSS",
            ),
        ]
