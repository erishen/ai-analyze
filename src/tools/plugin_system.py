#!/usr/bin/env python3
"""
插件化架构
支持动态加载、注册、执行分析插件
"""

import importlib
import inspect
import logging
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """插件元信息"""

    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
        }


class AnalysisPlugin(ABC):
    """分析插件基类

    所有自定义插件必须继承此类并实现 analyze 方法。
    """

    # 子类应覆盖这些属性
    plugin_name: str = "unnamed"
    plugin_version: str = "0.1.0"
    plugin_description: str = ""
    plugin_author: str = ""

    @abstractmethod
    def analyze(self, context: "PluginContext") -> Dict[str, Any]:
        """执行分析

        Args:
            context: 插件执行上下文，包含项目信息和共享数据

        Returns:
            分析结果字典
        """

    def setup(self) -> None:
        """插件初始化（可选覆盖）"""

    def teardown(self) -> None:
        """插件清理（可选覆盖）"""

    @property
    def info(self) -> PluginInfo:
        """插件元信息"""
        return PluginInfo(
            name=self.plugin_name,
            version=self.plugin_version,
            description=self.plugin_description,
            author=self.plugin_author,
        )


@dataclass
class PluginContext:
    """插件执行上下文"""

    project_path: str
    files: Dict[str, str] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    shared_data: Dict[str, Any] = field(default_factory=dict)

    def get_shared(self, key: str, default: Any = None) -> Any:
        """获取共享数据"""
        return self.shared_data.get(key, default)

    def set_shared(self, key: str, value: Any) -> None:
        """设置共享数据（供其他插件使用）"""
        self.shared_data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "total_files": len(self.files),
            "config_keys": list(self.config.keys()),
            "shared_keys": list(self.shared_data.keys()),
        }


@dataclass
class PluginResult:
    """插件执行结果"""

    plugin_name: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_name": self.plugin_name,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "duration": round(self.duration, 3),
        }


class PluginManager:
    """插件管理器"""

    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        self.logger = logging.getLogger("ai-analyze.plugin_manager")
        self._plugins: Dict[str, AnalysisPlugin] = {}
        self._plugin_dirs: List[str] = plugin_dirs or []
        self._hooks: Dict[str, List[Callable]] = {}

    @property
    def plugins(self) -> Dict[str, AnalysisPlugin]:
        """获取所有已注册插件"""
        return dict(self._plugins)

    @property
    def plugin_names(self) -> List[str]:
        """获取插件名称列表"""
        return list(self._plugins.keys())

    def register(self, plugin: AnalysisPlugin) -> None:
        """注册插件"""
        name = plugin.plugin_name
        if name in self._plugins:
            self.logger.warning("Plugin '%s' already registered, overwriting", name)
        self._plugins[name] = plugin
        plugin.setup()
        self.logger.info("Plugin registered: %s v%s", name, plugin.plugin_version)

    def unregister(self, name: str) -> None:
        """卸载插件"""
        if name in self._plugins:
            self._plugins[name].teardown()
            del self._plugins[name]
            self.logger.info("Plugin unregistered: %s", name)

    def add_plugin_dir(self, directory: str) -> None:
        """添加插件搜索目录"""
        if directory not in self._plugin_dirs:
            self._plugin_dirs.append(directory)

    def discover_plugins(self) -> List[str]:
        """从插件目录发现并加载插件

        Returns:
            新加载的插件名称列表
        """
        loaded = []
        for plugin_dir in self._plugin_dirs:
            dir_path = Path(plugin_dir)
            if not dir_path.exists():
                continue

            for py_file in dir_path.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue

                module_name = f"ai_analyze_plugin_{py_file.stem}"
                try:
                    spec = importlib.util.spec_from_file_location(module_name, str(py_file))
                    if spec is None or spec.loader is None:
                        continue
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    # 查找 AnalysisPlugin 子类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if inspect.isclass(attr) and issubclass(attr, AnalysisPlugin) and attr is not AnalysisPlugin:
                            plugin = attr()
                            self.register(plugin)
                            loaded.append(plugin.plugin_name)

                except Exception as e:
                    self.logger.error("Failed to load plugin from %s: %s", py_file, e)

        return loaded

    def execute(
        self,
        plugin_name: str,
        context: PluginContext,
    ) -> PluginResult:
        """执行指定插件

        Args:
            plugin_name: 插件名称
            context: 执行上下文

        Returns:
            插件执行结果
        """
        import time

        if plugin_name not in self._plugins:
            return PluginResult(
                plugin_name=plugin_name,
                success=False,
                error=f"Plugin '{plugin_name}' not found",
            )

        plugin = self._plugins[plugin_name]
        start = time.time()

        try:
            data = plugin.analyze(context)
            duration = time.time() - start
            return PluginResult(
                plugin_name=plugin_name,
                success=True,
                data=data,
                duration=duration,
            )
        except Exception as e:
            duration = time.time() - start
            self.logger.error("Plugin '%s' failed: %s", plugin_name, e)
            return PluginResult(
                plugin_name=plugin_name,
                success=False,
                error=str(e),
                duration=duration,
            )

    def execute_all(self, context: PluginContext) -> List[PluginResult]:
        """执行所有已注册插件"""
        results = []
        for name in list(self._plugins.keys()):
            result = self.execute(name, context)
            results.append(result)
        return results

    def add_hook(self, event: str, callback: Callable) -> None:
        """注册事件钩子"""
        self._hooks.setdefault(event, []).append(callback)

    def trigger_hook(self, event: str, **kwargs: Any) -> None:
        """触发事件钩子"""
        for callback in self._hooks.get(event, []):
            try:
                callback(**kwargs)
            except Exception as e:
                self.logger.error("Hook '%s' callback failed: %s", event, e)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_plugins": len(self._plugins),
            "plugin_names": self.plugin_names,
            "plugin_dirs": self._plugin_dirs,
            "plugins": {n: p.info.to_dict() for n, p in self._plugins.items()},
        }


# ==================== 示例插件 ====================


class ComplexityHotspotPlugin(AnalysisPlugin):
    """复杂度热点分析示例插件"""

    plugin_name = "complexity_hotspot"
    plugin_version = "1.0.0"
    plugin_description = "Identify top complexity hotspots in the project"
    plugin_author = "ai-analyze"

    def analyze(self, context: PluginContext) -> Dict[str, Any]:
        import re

        hotspots = []
        for file_path, content in context.files.items():
            if not file_path.endswith(".py"):
                continue
            # 简单启发式：计算 if/for/while 数量作为复杂度代理
            complexity = len(re.findall(r"\b(if|elif|for|while|except|with|and|or)\b", content))
            lines = len(content.split("\n"))
            if complexity > 10 or (lines > 0 and complexity / lines > 0.1):
                hotspots.append(
                    {
                        "file": file_path,
                        "estimated_complexity": complexity,
                        "lines": lines,
                        "density": round(complexity / max(lines, 1), 3),
                    }
                )

        hotspots.sort(key=lambda x: x["estimated_complexity"], reverse=True)

        # 将结果共享给其他插件
        context.set_shared("complexity_hotspots", hotspots[:10])

        return {
            "total_hotspots": len(hotspots),
            "top_5": hotspots[:5],
        }


class FileStatsPlugin(AnalysisPlugin):
    """文件统计示例插件"""

    plugin_name = "file_stats"
    plugin_version = "1.0.0"
    plugin_description = "Collect basic file statistics"
    plugin_author = "ai-analyze"

    def analyze(self, context: PluginContext) -> Dict[str, Any]:
        ext_counts: Dict[str, int] = {}
        total_lines = 0
        total_size = 0

        for file_path, content in context.files.items():
            ext = os.path.splitext(file_path)[1] or "(no ext)"
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
            total_lines += len(content.split("\n"))
            total_size += len(content.encode("utf-8"))

        context.set_shared(
            "file_stats",
            {
                "total_files": len(context.files),
                "total_lines": total_lines,
                "total_size_bytes": total_size,
            },
        )

        return {
            "total_files": len(context.files),
            "total_lines": total_lines,
            "total_size_bytes": total_size,
            "by_extension": ext_counts,
        }
