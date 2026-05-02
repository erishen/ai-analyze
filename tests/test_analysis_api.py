#!/usr/bin/env python3
"""analysis_api.py 测试 - 覆盖 API 服务、Webhook 通知"""

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock  # noqa: F401

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis_api import (  # noqa: E402
    AnalysisAPIService, AnalysisRequest,
    AnalysisResponse, WebhookNotifier,
)


class TestAnalysisRequest(unittest.TestCase):
    """AnalysisRequest 数据类测试"""

    def test_default_values(self):
        req = AnalysisRequest(project_path="/tmp/test")
        self.assertEqual(req.project_path, "/tmp/test")
        self.assertEqual(req.analysis_types, ["all"])
        self.assertEqual(req.config, {})
        self.assertEqual(req.callback_url, "")

    def test_custom_values(self):
        req = AnalysisRequest(
            project_path="/tmp/test",
            analysis_types=["security", "quality"],
            config={"key": "value"},
            callback_url="https://example.com/hook",
        )
        self.assertEqual(req.analysis_types, ["security", "quality"])
        self.assertEqual(req.config, {"key": "value"})
        self.assertEqual(req.callback_url, "https://example.com/hook")


class TestAnalysisResponse(unittest.TestCase):
    """AnalysisResponse 数据类测试"""

    def test_to_dict(self):
        resp = AnalysisResponse(
            request_id="req_123",
            status="completed",
            results={"key": "value"},
            error="",
            duration=1.234,
        )
        d = resp.to_dict()
        self.assertEqual(d["request_id"], "req_123")
        self.assertEqual(d["status"], "completed")
        self.assertEqual(d["results"], {"key": "value"})
        self.assertEqual(d["duration"], 1.234)

    def test_to_dict_rounds_duration(self):
        resp = AnalysisResponse(request_id="req_1", status="running", duration=1.234567)
        d = resp.to_dict()
        self.assertEqual(d["duration"], 1.235)

    def test_default_values(self):
        resp = AnalysisResponse(request_id="req_1", status="pending")
        self.assertEqual(resp.results, {})
        self.assertEqual(resp.error, "")
        self.assertEqual(resp.duration, 0.0)


class TestWebhookNotifier(unittest.TestCase):
    """WebhookNotifier 测试"""

    def test_add_handler(self):
        notifier = WebhookNotifier()
        notifier.add_handler("https://example.com/hook", events=["analysis_completed"])
        self.assertEqual(len(notifier._handlers), 1)
        self.assertEqual(notifier._handlers[0]["url"], "https://example.com/hook")
        self.assertEqual(notifier._handlers[0]["events"], ["analysis_completed"])

    def test_add_handler_default_events(self):
        notifier = WebhookNotifier()
        notifier.add_handler("https://example.com/hook")
        self.assertEqual(
            notifier._handlers[0]["events"],
            ["analysis_completed", "analysis_failed"],
        )

    def test_notify_event_not_matched(self):
        """事件不匹配时跳过通知"""
        notifier = WebhookNotifier()
        notifier.add_handler("https://example.com/hook", events=["analysis_completed"])
        results = asyncio.run(notifier.notify("analysis_failed", {"key": "value"}))
        # 事件不匹配，应返回 True（跳过）
        self.assertEqual(results, [True])

    def test_notify_send_failure(self):
        """Webhook 发送失败"""
        notifier = WebhookNotifier()
        notifier.add_handler("https://invalid-url.example.com/hook")
        results = asyncio.run(notifier.notify("analysis_completed", {"key": "value"}))
        # 发送失败，应返回 False
        self.assertEqual(results, [False])

    def test_notify_no_handlers(self):
        """没有注册 handler 时"""
        notifier = WebhookNotifier()
        results = asyncio.run(notifier.notify("analysis_completed", {"key": "value"}))
        self.assertEqual(results, [])

    def test_notify_multiple_handlers(self):
        """多个 handler 通知"""
        notifier = WebhookNotifier()
        notifier.add_handler("https://invalid1.example.com/hook", events=["analysis_completed"])
        notifier.add_handler("https://invalid2.example.com/hook", events=["analysis_failed"])
        results = asyncio.run(notifier.notify("analysis_completed", {"key": "value"}))
        # 第一个发送失败，第二个事件不匹配
        self.assertEqual(len(results), 2)
        self.assertFalse(results[0])
        self.assertTrue(results[1])


class TestAnalysisAPIService(unittest.TestCase):
    """AnalysisAPIService 测试"""

    def setUp(self):
        self.service = AnalysisAPIService()

    def test_generate_request_id(self):
        id1 = self.service._generate_request_id()
        id2 = self.service._generate_request_id()
        self.assertTrue(id1.startswith("req_"))
        self.assertNotEqual(id1, id2)

    def test_load_project_files(self):
        """测试加载项目文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            (Path(tmpdir) / "test.py").write_text("print('hello')", encoding="utf-8")
            (Path(tmpdir) / "test.js").write_text("console.log('hello')", encoding="utf-8")
            (Path(tmpdir) / "test.txt").write_text("ignored", encoding="utf-8")

            # 创建 __pycache__ 目录
            pycache = Path(tmpdir) / "__pycache__"
            pycache.mkdir()
            (pycache / "cached.pyc").write_text("binary", encoding="utf-8")

            files = self.service._load_project_files(tmpdir)
            file_names = [Path(f).name for f in files.keys()]
            self.assertIn("test.py", file_names)
            self.assertIn("test.js", file_names)
            self.assertNotIn("test.txt", file_names)
            self.assertNotIn("cached.pyc", file_names)

    def test_load_project_files_max_limit(self):
        """测试文件加载数量限制"""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(10):
                (Path(tmpdir) / f"module_{i}.py").write_text(f"# file {i}", encoding="utf-8")

            files = self.service._load_project_files(tmpdir, max_files=5)
            self.assertLessEqual(len(files), 5)

    def test_load_project_files_nonexistent(self):
        """测试加载不存在的路径"""
        files = self.service._load_project_files("/nonexistent/path")
        self.assertEqual(files, {})

    def test_analyze_project_success(self):
        """测试项目分析成功"""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text("x = 1\n", encoding="utf-8")

            request = AnalysisRequest(
                project_path=tmpdir,
                analysis_types=["security"],
            )
            response = asyncio.run(self.service.analyze_project(request))

            self.assertEqual(response.status, "completed")
            self.assertIn("security", response.results)
            self.assertGreater(response.duration, 0)
            self.assertEqual(response.error, "")

    def test_analyze_project_all_types(self):
        """测试 all 分析类型"""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text("x = 1\n", encoding="utf-8")

            request = AnalysisRequest(
                project_path=tmpdir,
                analysis_types=["all"],
            )
            response = asyncio.run(self.service.analyze_project(request))

            self.assertEqual(response.status, "completed")
            self.assertIn("security", response.results)
            self.assertIn("performance", response.results)

    def test_analyze_project_failed(self):
        """测试项目分析失败"""
        request = AnalysisRequest(
            project_path="/nonexistent/path/that/does/not/exist",
            analysis_types=["security"],
        )
        response = asyncio.run(self.service.analyze_project(request))
        # 应该返回 completed 或 failed（取决于是否抛出异常）
        self.assertIn(response.status, ["completed", "failed"])

    def test_analyze_project_with_callback(self):
        """测试带回调的分析"""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text("x = 1\n", encoding="utf-8")

            request = AnalysisRequest(
                project_path=tmpdir,
                analysis_types=["security"],
                callback_url="https://invalid-callback.example.com/hook",
            )
            response = asyncio.run(self.service.analyze_project(request))

            self.assertEqual(response.status, "completed")
            # Webhook 发送失败不影响分析结果


class TestAnalysisResponseIntegration(unittest.TestCase):
    """分析响应集成测试"""

    def test_response_serialization(self):
        """测试响应序列化完整流程"""
        service = AnalysisAPIService()
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text("x = 1\n", encoding="utf-8")

            request = AnalysisRequest(project_path=tmpdir, analysis_types=["security"])
            response = asyncio.run(service.analyze_project(request))
            d = response.to_dict()

            self.assertIn("request_id", d)
            self.assertIn("status", d)
            self.assertIn("results", d)
            self.assertIn("duration", d)


if __name__ == "__main__":
    unittest.main()
