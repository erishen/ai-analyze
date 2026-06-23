#!/usr/bin/env python3
"""
缓存预热模块
在项目分析前预加载常用数据到缓存，减少首次分析延迟
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class WarmupTask:
    """预热任务"""

    name: str
    key: str
    compute_fn: Callable[[], Any]
    ttl: int = 3600
    priority: int = 0  # 0 最高优先级
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WarmupResult:
    """预热结果"""

    task_name: str
    success: bool
    duration_ms: float
    cache_hit: bool  # 是否已存在缓存
    error: Optional[str] = None


class CacheWarmer:
    """
    缓存预热器
    在分析开始前，并行预加载高频访问数据到缓存
    """

    def __init__(self, cache, max_workers: int = 4):
        """
        Args:
            cache: MultiLevelCache 实例
            max_workers: 并行预热线程数
        """
        self._cache = cache
        self._max_workers = max_workers
        self._tasks: List[WarmupTask] = []
        self._results: List[WarmupResult] = []

    def add_task(
        self,
        name: str,
        key: str,
        compute_fn: Callable[[], Any],
        ttl: int = 3600,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """添加预热任务"""
        self._tasks.append(
            WarmupTask(
                name=name,
                key=key,
                compute_fn=compute_fn,
                ttl=ttl,
                priority=priority,
                metadata=metadata or {},
            )
        )

    def add_project_warmup_tasks(
        self,
        project_path: str,
        file_patterns: Optional[List[str]] = None,
    ) -> None:
        """
        为项目添加标准预热任务集
        包括：项目结构、语言统计、依赖信息等
        """
        project_path = str(Path(project_path).resolve())

        # 任务 1: 项目文件列表
        self.add_task(
            name="project_files",
            key=self._cache.make_key("project_files", project_path),
            compute_fn=lambda: self._scan_project_files(project_path, file_patterns),
            ttl=1800,  # 30 分钟
            priority=0,
        )

        # 任务 2: 语言统计
        self.add_task(
            name="language_stats",
            key=self._cache.make_key("language_stats", project_path),
            compute_fn=lambda: self._compute_language_stats(project_path),
            ttl=3600,
            priority=1,
        )

        # 任务 3: 项目元信息
        self.add_task(
            name="project_meta",
            key=self._cache.make_key("project_meta", project_path),
            compute_fn=lambda: self._get_project_meta(project_path),
            ttl=7200,  # 2 小时
            priority=0,
        )

        # 任务 4: 依赖信息
        self.add_task(
            name="dependencies",
            key=self._cache.make_key("dependencies", project_path),
            compute_fn=lambda: self._scan_dependencies(project_path),
            ttl=3600,
            priority=2,
        )

        logger.info(f"已添加 4 个项目预热任务: {project_path}")

    def warmup(self, skip_existing: bool = True) -> List[WarmupResult]:
        """
        执行缓存预热

        Args:
            skip_existing: 是否跳过已缓存的任务

        Returns:
            预热结果列表
        """
        if not self._tasks:
            logger.info("没有预热任务")
            return []

        # 按优先级排序
        sorted_tasks = sorted(self._tasks, key=lambda t: t.priority)
        self._results = []

        # 过滤已缓存的任务
        if skip_existing:
            pending = []
            for task in sorted_tasks:
                if self._cache.exists(task.key):
                    self._results.append(
                        WarmupResult(
                            task_name=task.name,
                            success=True,
                            duration_ms=0,
                            cache_hit=True,
                        )
                    )
                    logger.debug(f"预热跳过（已缓存）: {task.name}")
                else:
                    pending.append(task)
            sorted_tasks = pending

        if not sorted_tasks:
            logger.info("所有预热任务已缓存，跳过")
            return self._results

        logger.info(f"开始预热 {len(sorted_tasks)} 个任务...")

        # 并行执行
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {executor.submit(self._execute_task, task): task for task in sorted_tasks}
            for future in as_completed(futures):
                result = future.result()
                self._results.append(result)

        # 统计
        success_count = sum(1 for r in self._results if r.success)
        total_count = len(self._results)
        logger.info(f"预热完成: {success_count}/{total_count} 成功")

        return self._results

    def _execute_task(self, task: WarmupTask) -> WarmupResult:
        """执行单个预热任务"""
        start = time.time()
        try:
            value = task.compute_fn()
            duration_ms = (time.time() - start) * 1000

            self._cache.set(
                key=task.key,
                value=value,
                ttl=task.ttl,
                metadata={
                    "warmer": True,
                    "task_name": task.name,
                    **task.metadata,
                },
            )

            logger.debug(f"预热成功: {task.name} ({duration_ms:.1f}ms)")
            return WarmupResult(
                task_name=task.name,
                success=True,
                duration_ms=duration_ms,
                cache_hit=False,
            )
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.warning(f"预热失败: {task.name} - {e}")
            return WarmupResult(
                task_name=task.name,
                success=False,
                duration_ms=duration_ms,
                cache_hit=False,
                error=str(e),
            )

    @staticmethod
    def _scan_project_files(
        project_path: str,
        file_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """扫描项目文件"""
        project_dir = Path(project_path)
        patterns = file_patterns or [
            "*.py",
            "*.js",
            "*.ts",
            "*.go",
            "*.java",
            "*.jsx",
            "*.tsx",
            "*.rs",
            "*.cpp",
            "*.c",
            "*.rb",
            "*.php",
        ]

        # 排除目录
        exclude_dirs = {
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
            ".cache",
            ".mypy_cache",
            ".tox",
        }

        files = []
        for pattern in patterns:
            for f in project_dir.rglob(pattern):
                if not any(part in exclude_dirs for part in f.parts):
                    try:
                        stat = f.stat()
                        files.append(
                            {
                                "path": str(f.relative_to(project_dir)),
                                "size": stat.st_size,
                                "modified": stat.st_mtime,
                            }
                        )
                    except Exception:
                        pass

        return {
            "project_path": project_path,
            "file_count": len(files),
            "files": files,
            "scanned_at": time.time(),
        }

    @staticmethod
    def _compute_language_stats(project_path: str) -> Dict[str, Any]:
        """计算语言统计"""
        ext_to_lang = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".go": "Go",
            ".java": "Java",
            ".jsx": "JSX",
            ".tsx": "TSX",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
            ".rb": "Ruby",
            ".php": "PHP",
            ".html": "HTML",
            ".css": "CSS",
            ".sql": "SQL",
        }

        project_dir = Path(project_path)
        stats: Dict[str, int] = {}
        total_lines = 0

        for f in project_dir.rglob("*"):
            if f.is_file() and (lang := ext_to_lang.get(f.suffix.lower())):
                try:
                    stats[lang] = stats.get(lang, 0) + 1
                    with open(f, "r", encoding="utf-8", errors="replace") as fh:
                        total_lines += sum(1 for _ in fh)
                except Exception:
                    pass

        return {
            "project_path": project_path,
            "languages": stats,
            "total_files": sum(stats.values()),
            "total_lines": total_lines,
        }

    @staticmethod
    def _get_project_meta(project_path: str) -> Dict[str, Any]:
        """获取项目元信息"""
        project_dir = Path(project_path)
        meta = {"project_path": project_path}

        # 检测项目类型
        if (project_dir / "pyproject.toml").exists():
            meta["type"] = "python"
            meta["build_system"] = "pyproject.toml"
        elif (project_dir / "package.json").exists():
            meta["type"] = "node"
            meta["build_system"] = "package.json"
        elif (project_dir / "go.mod").exists():
            meta["type"] = "go"
            meta["build_system"] = "go.mod"
        elif (project_dir / "pom.xml").exists():
            meta["type"] = "java-maven"
            meta["build_system"] = "pom.xml"
        elif (project_dir / "Cargo.toml").exists():
            meta["type"] = "rust"
            meta["build_system"] = "Cargo.toml"
        else:
            meta["type"] = "unknown"

        # 检测框架
        if (project_dir / "requirements.txt").exists():
            meta["has_requirements"] = "true"
        if (project_dir / "Dockerfile").exists():
            meta["has_dockerfile"] = "true"
        if (project_dir / ".github").exists():
            meta["has_ci"] = "true"

        return meta

    @staticmethod
    def _scan_dependencies(project_path: str) -> Dict[str, Any]:
        """扫描项目依赖"""
        project_dir = Path(project_path)
        deps: Dict[str, Any] = {"project_path": project_path, "dependencies": {}}

        # Python 依赖
        req_file = project_dir / "requirements.txt"
        if req_file.exists():
            python_deps = []
            for line in req_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    python_deps.append(line)
            deps["dependencies"]["python"] = python_deps

        # Node 依赖
        pkg_file = project_dir / "package.json"
        if pkg_file.exists():
            try:
                pkg = json.loads(pkg_file.read_text())
                node_deps = list(
                    set(list(pkg.get("dependencies", {}).keys()) + list(pkg.get("devDependencies", {}).keys()))
                )
                deps["dependencies"]["node"] = node_deps
            except Exception:
                pass

        return deps

    def get_results_summary(self) -> Dict[str, Any]:
        """获取预热结果摘要"""
        if not self._results:
            return {"total": 0, "success": 0, "failed": 0, "skipped": 0}

        success = sum(1 for r in self._results if r.success and not r.cache_hit)
        skipped = sum(1 for r in self._results if r.cache_hit)
        failed = sum(1 for r in self._results if not r.success)
        total_time = sum(r.duration_ms for r in self._results)

        return {
            "total": len(self._results),
            "success": success,
            "failed": failed,
            "skipped": skipped,
            "total_time_ms": total_time,
            "tasks": [
                {
                    "name": r.task_name,
                    "success": r.success,
                    "duration_ms": r.duration_ms,
                    "cache_hit": r.cache_hit,
                    "error": r.error,
                }
                for r in self._results
            ],
        }
