#!/usr/bin/env python3
"""
分析 API 服务
基于 FastAPI 提供 REST API 接口
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRequest:
    """分析请求"""

    project_path: str
    analysis_types: List[str] = field(default_factory=lambda: ["all"])
    config: Dict[str, Any] = field(default_factory=dict)
    callback_url: str = ""  # Webhook 回调地址


@dataclass
class AnalysisResponse:
    """分析响应"""

    request_id: str
    status: str  # pending, running, completed, failed
    results: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status,
            "results": self.results,
            "error": self.error,
            "duration": round(self.duration, 3),
        }


class WebhookNotifier:
    """Webhook 通知器"""

    def __init__(self) -> None:
        self.logger = logging.getLogger("ai-analyze.webhook")
        self._handlers: List[Any] = []

    def add_handler(self, url: str, events: Optional[List[str]] = None) -> None:
        """添加 webhook 处理器"""
        self._handlers.append(
            {
                "url": url,
                "events": events or ["analysis_completed", "analysis_failed"],
            }
        )

    async def notify(self, event: str, data: Dict[str, Any]) -> List[bool]:
        """发送 webhook 通知"""
        results = []
        for handler in self._handlers:
            if event not in handler["events"]:
                results.append(True)
                continue
            try:
                success = await self._send(handler["url"], event, data)
                results.append(success)
            except Exception as e:
                self.logger.error("Webhook failed for %s: %s", handler["url"], e)
                results.append(False)
        return results

    async def _send(self, url: str, event: str, data: Dict[str, Any]) -> bool:
        """发送 webhook 请求"""
        try:
            import urllib.request

            payload = json.dumps(
                {
                    "event": event,
                    "timestamp": time.time(),
                    "data": data,
                }
            ).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: urllib.request.urlopen(req, timeout=10),
            )
            return response.status < 400
        except Exception as e:
            self.logger.error("Webhook send failed: %s", e)
            return False


class AnalysisAPIService:
    """分析 API 服务

    提供同步和异步分析接口，支持 Webhook 回调。
    可集成到 FastAPI 应用中。
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("ai-analyze.api_service")
        self.webhook = WebhookNotifier()
        self._request_counter = 0

    def _generate_request_id(self) -> str:
        self._request_counter += 1
        return f"req_{int(time.time())}_{self._request_counter}"

    async def analyze_project(self, request: AnalysisRequest) -> AnalysisResponse:
        """执行项目分析"""
        request_id = self._generate_request_id()
        response = AnalysisResponse(request_id=request_id, status="running")

        start = time.time()
        try:
            results: Dict[str, Any] = {}
            analysis_types = request.analysis_types

            if "all" in analysis_types:
                analysis_types = [
                    "security",
                    "performance",
                    "tech_debt",
                    "dependency",
                    "quality",
                ]

            # 按需加载和执行各分析模块
            files = self._load_project_files(request.project_path)

            if "security" in analysis_types:
                from src.security_scanner import SecurityScanner

                scanner = SecurityScanner()
                results["security"] = scanner.scan_project(files).to_dict()

            if "performance" in analysis_types:
                from src.performance_analyzer import PerformanceAnalyzer

                analyzer = PerformanceAnalyzer()
                results["performance"] = analyzer.analyze_project(files).to_dict()

            if "tech_debt" in analysis_types:
                from src.tech_debt import TechDebtAnalyzer

                analyzer = TechDebtAnalyzer()
                results["tech_debt"] = analyzer.analyze_project(files).to_dict()

            if "dependency" in analysis_types:
                from src.dependency_graph import DependencyAnalyzer

                analyzer = DependencyAnalyzer(request.project_path)
                results["dependency"] = analyzer.analyze_project(files).to_dict()

            if "quality" in analysis_types:
                from src.quality_score import QualityScorer, QualityMetrics

                scorer = QualityScorer()
                metrics = QualityMetrics(
                    lines_of_code=sum(len(c.split("\n")) for c in files.values()),
                )
                results["quality"] = scorer.calculate_score(metrics)

            response.results = results
            response.status = "completed"
            response.duration = time.time() - start

            # Webhook 通知
            if request.callback_url:
                self.webhook.add_handler(request.callback_url)
                await self.webhook.notify("analysis_completed", response.to_dict())

        except Exception as e:
            response.status = "failed"
            response.error = str(e)
            response.duration = time.time() - start
            self.logger.error("Analysis failed: %s", e)

            if request.callback_url:
                self.webhook.add_handler(request.callback_url)
                await self.webhook.notify("analysis_failed", response.to_dict())

        return response

    def _load_project_files(self, project_path: str, max_files: int = 500) -> Dict[str, str]:
        """加载项目文件"""
        import os

        files: Dict[str, str] = {}
        supported_ext = {".py", ".js", ".ts", ".go", ".java"}

        for root, dirs, filenames in os.walk(project_path):
            # 跳过常见忽略目录
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".venv", "venv"}]
            for filename in filenames:
                ext = os.path.splitext(filename)[1]
                if ext not in supported_ext:
                    continue
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        files[filepath] = f.read()
                except OSError:
                    continue
                if len(files) >= max_files:
                    break

        return files

    def create_fastapi_app(self) -> Any:
        """创建 FastAPI 应用"""
        try:
            from fastapi import FastAPI
            from pydantic import BaseModel
        except ImportError:
            raise ImportError("FastAPI not installed. Run: pip install fastapi uvicorn")

        app = FastAPI(
            title="AI-Analyze API",
            version="0.2.0",
            description="Code analysis API service",
        )
        service = self

        class AnalyzeRequest(BaseModel):
            project_path: str
            analysis_types: List[str] = ["all"]
            config: Dict[str, Any] = {}
            callback_url: str = ""

        @app.get("/health")
        async def health() -> Dict[str, str]:
            return {"status": "ok"}

        @app.post("/analyze")
        async def analyze(req: AnalyzeRequest) -> Dict[str, Any]:
            request = AnalysisRequest(
                project_path=req.project_path,
                analysis_types=req.analysis_types,
                config=req.config,
                callback_url=req.callback_url,
            )
            response = await service.analyze_project(request)
            return response.to_dict()

        @app.get("/analysis-types")
        async def list_types() -> Dict[str, List[str]]:
            return {
                "types": [
                    "security",
                    "performance",
                    "tech_debt",
                    "dependency",
                    "quality",
                    "all",
                ]
            }

        return app
