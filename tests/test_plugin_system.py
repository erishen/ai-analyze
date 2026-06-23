#!/usr/bin/env python3
"""Tests for plugin_system module"""

import sys
import tempfile
from pathlib import Path

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.tools.plugin_system import (  # noqa: E402
    PluginContext, PluginManager, PluginResult,
    PluginInfo, ComplexityHotspotPlugin, FileStatsPlugin,
)


class TestPluginInfo:
    def test_to_dict(self):
        info = PluginInfo(name="test", version="1.0")
        d = info.to_dict()
        assert d["name"] == "test"
        assert d["version"] == "1.0"


class TestPluginContext:
    def test_shared_data(self):
        ctx = PluginContext(project_path="/test")
        ctx.set_shared("key1", "value1")
        assert ctx.get_shared("key1") == "value1"
        assert ctx.get_shared("missing", "default") == "default"

    def test_to_dict(self):
        ctx = PluginContext(project_path="/test", files={"a.py": "code"})
        d = ctx.to_dict()
        assert d["project_path"] == "/test"
        assert d["total_files"] == 1


class TestPluginResult:
    def test_success_result(self):
        result = PluginResult(plugin_name="test", success=True, data={"x": 1})
        d = result.to_dict()
        assert d["success"] is True
        assert d["data"]["x"] == 1

    def test_failed_result(self):
        result = PluginResult(plugin_name="test", success=False, error="boom")
        d = result.to_dict()
        assert d["success"] is False
        assert d["error"] == "boom"


class TestComplexityHotspotPlugin:
    def test_analyze(self):
        plugin = ComplexityHotspotPlugin()
        ctx = PluginContext(
            project_path="/test",
            files={"complex.py": "if a:\n  if b:\n    if c:\n      for i in x:\n        while y:\n          pass\n"},
        )
        result = plugin.analyze(ctx)
        assert "total_hotspots" in result
        assert ctx.get_shared("complexity_hotspots") is not None

    def test_info(self):
        plugin = ComplexityHotspotPlugin()
        assert plugin.info.name == "complexity_hotspot"


class TestFileStatsPlugin:
    def test_analyze(self):
        plugin = FileStatsPlugin()
        ctx = PluginContext(
            project_path="/test",
            files={"a.py": "x = 1\n", "b.js": "var x = 1;\n"},
        )
        result = plugin.analyze(ctx)
        assert result["total_files"] == 2
        assert result["total_lines"] >= 2
        assert ".py" in result["by_extension"]
        assert ".js" in result["by_extension"]


class TestPluginManager:
    def test_register_and_execute(self):
        manager = PluginManager()
        plugin = FileStatsPlugin()
        manager.register(plugin)
        assert "file_stats" in manager.plugin_names

        ctx = PluginContext(project_path="/test", files={"a.py": "x=1\n"})
        result = manager.execute("file_stats", ctx)
        assert result.success is True
        assert result.data["total_files"] == 1

    def test_execute_nonexistent(self):
        manager = PluginManager()
        ctx = PluginContext(project_path="/test")
        result = manager.execute("missing", ctx)
        assert result.success is False
        assert "not found" in result.error

    def test_unregister(self):
        manager = PluginManager()
        manager.register(FileStatsPlugin())
        assert "file_stats" in manager.plugin_names
        manager.unregister("file_stats")
        assert "file_stats" not in manager.plugin_names

    def test_execute_all(self):
        manager = PluginManager()
        manager.register(FileStatsPlugin())
        manager.register(ComplexityHotspotPlugin())
        ctx = PluginContext(
            project_path="/test",
            files={"a.py": "if x:\n  for i in range(100):\n    pass\n"},
        )
        results = manager.execute_all(ctx)
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_hooks(self):
        manager = PluginManager()
        called = []
        manager.add_hook("on_complete", lambda **kw: called.append(kw))
        manager.trigger_hook("on_complete", result="ok")
        assert len(called) == 1
        assert called[0]["result"] == "ok"

    def test_discover_plugins(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_code = (
                "from src.tools.plugin_system import AnalysisPlugin, PluginContext\n"
                "from typing import Any, Dict\n\n"
                "class DemoPlugin(AnalysisPlugin):\n"
                "    plugin_name = 'demo'\n"
                "    plugin_version = '1.0'\n\n"
                "    def analyze(self, context: PluginContext) -> Dict[str, Any]:\n"
                "        return {'demo': True}\n"
            )
            plugin_path = Path(tmpdir) / "demo_plugin.py"
            plugin_path.write_text(plugin_code)

            manager = PluginManager(plugin_dirs=[tmpdir])
            loaded = manager.discover_plugins()
            assert "demo" in loaded

    def test_to_dict(self):
        manager = PluginManager()
        manager.register(FileStatsPlugin())
        d = manager.to_dict()
        assert d["total_plugins"] == 1
