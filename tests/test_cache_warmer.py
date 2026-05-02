#!/usr/bin/env python3
"""
缓存预热模块单元测试
"""

import json
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径，使用包导入
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.multi_level_cache import MultiLevelCache  # noqa: E402
from src.cache_warmer import CacheWarmer, WarmupTask, WarmupResult  # noqa: E402


# ==================== WarmupTask 测试 ====================


def test_warmup_task_creation():
    """测试预热任务创建"""
    task = WarmupTask(
        name="test_task",
        key="cache_key_1",
        compute_fn=lambda: "result",
        ttl=1800,
        priority=1,
    )
    assert task.name == "test_task"
    assert task.key == "cache_key_1"
    assert task.ttl == 1800
    assert task.priority == 1


# ==================== WarmupResult 测试 ====================


def test_warmup_result_success():
    """测试预热结果 - 成功"""
    result = WarmupResult(
        task_name="task1",
        success=True,
        duration_ms=100.0,
        cache_hit=False,
    )
    assert result.success
    assert not result.cache_hit
    assert result.error is None


def test_warmup_result_failure():
    """测试预热结果 - 失败"""
    result = WarmupResult(
        task_name="task1",
        success=False,
        duration_ms=50.0,
        cache_hit=False,
        error="connection timeout",
    )
    assert not result.success
    assert result.error == "connection timeout"


def test_warmup_result_cache_hit():
    """测试预热结果 - 缓存命中"""
    result = WarmupResult(
        task_name="task1",
        success=True,
        duration_ms=0,
        cache_hit=True,
    )
    assert result.cache_hit


# ==================== CacheWarmer 核心测试 ====================


def _create_cache(tmpdir: str) -> MultiLevelCache:
    """创建测试用缓存实例"""
    return MultiLevelCache(
        default_ttl=3600,
        enable_memory=True,
        enable_file=True,
        enable_redis=False,
        file_cache_dir=tmpdir,
    )


def test_warmer_add_task():
    """测试添加预热任务"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = _create_cache(tmpdir)
        warmer = CacheWarmer(cache)
        warmer.add_task(
            name="task1",
            key="k1",
            compute_fn=lambda: {"data": 1},
            ttl=3600,
        )
        assert len(warmer._tasks) == 1
        assert warmer._tasks[0].name == "task1"


def test_warmer_add_multiple_tasks():
    """测试添加多个预热任务"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = _create_cache(tmpdir)
        warmer = CacheWarmer(cache)
        warmer.add_task(name="task1", key="k1", compute_fn=lambda: "v1", priority=2)
        warmer.add_task(name="task2", key="k2", compute_fn=lambda: "v2", priority=0)
        warmer.add_task(name="task3", key="k3", compute_fn=lambda: "v3", priority=1)
        assert len(warmer._tasks) == 3


def test_warmer_execute():
    """测试预热执行"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = _create_cache(tmpdir)
        warmer = CacheWarmer(cache)
        warmer.add_task(name="task1", key="k1", compute_fn=lambda: "result1")
        warmer.add_task(name="task2", key="k2", compute_fn=lambda: {"val": 42})

        results = warmer.warmup()
        assert len(results) >= 2

        # 验证缓存已写入
        assert cache.get("k1") == "result1"
        assert cache.get("k2") == {"val": 42}


def test_warmer_skip_existing():
    """测试预热跳过已有缓存"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = _create_cache(tmpdir)
        # 预先写入缓存
        cache.set("k1", "existing_value")

        warmer = CacheWarmer(cache)
        warmer.add_task(name="task1", key="k1", compute_fn=lambda: "new_value")

        results = warmer.warmup(skip_existing=True)
        # 应该跳过已有缓存
        assert any(r.cache_hit for r in results)

        # 缓存值不变
        assert cache.get("k1") == "existing_value"


def test_warmer_no_skip_existing():
    """测试预热不跳过已有缓存"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = _create_cache(tmpdir)
        cache.set("k1", "old_value")

        warmer = CacheWarmer(cache)
        warmer.add_task(name="task1", key="k1", compute_fn=lambda: "new_value")

        warmer.warmup(skip_existing=False)
        # 不跳过，应该重新计算
        # 新值会覆盖旧值
        assert cache.get("k1") == "new_value"


def test_warmer_compute_failure():
    """测试预热计算失败"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = _create_cache(tmpdir)
        warmer = CacheWarmer(cache)

        def failing_compute():
            raise RuntimeError("compute failed")

        warmer.add_task(name="fail_task", key="k1", compute_fn=failing_compute)
        results = warmer.warmup()

        # 应有失败的记录
        failed = [r for r in results if not r.success]
        assert len(failed) > 0
        assert failed[0].error is not None


def test_warmer_priority_order():
    """测试预热按优先级执行"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = _create_cache(tmpdir)
        warmer = CacheWarmer(cache)

        execution_order = []

        def make_fn(tag):
            def fn():
                execution_order.append(tag)
                return tag

            return fn

        warmer.add_task(name="low", key="k3", compute_fn=make_fn("low"), priority=2)
        warmer.add_task(name="high", key="k1", compute_fn=make_fn("high"), priority=0)
        warmer.add_task(name="mid", key="k2", compute_fn=make_fn("mid"), priority=1)

        warmer.warmup(skip_existing=False)
        # 高优先级（数值小）应先执行
        assert execution_order[0] == "high"


def test_warmer_no_tasks():
    """测试没有预热任务"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = _create_cache(tmpdir)
        warmer = CacheWarmer(cache)
        results = warmer.warmup()
        assert results == []


# ==================== 项目预热任务测试 ====================


def test_project_warmup_tasks():
    """测试项目标准预热任务集"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建模拟项目
        project_dir = Path(tmpdir) / "test_project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text("[project]\nname='test'\n")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "main.py").write_text("print('hello')\n")
        (project_dir / "requirements.txt").write_text("python-dotenv>=1.0.0\n")

        cache = _create_cache(str(Path(tmpdir) / "cache"))
        warmer = CacheWarmer(cache)
        warmer.add_project_warmup_tasks(str(project_dir))

        assert len(warmer._tasks) == 4
        task_names = [t.name for t in warmer._tasks]
        assert "project_files" in task_names
        assert "language_stats" in task_names
        assert "project_meta" in task_names
        assert "dependencies" in task_names


def test_project_warmup_execution():
    """测试项目预热完整执行"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建模拟项目
        project_dir = Path(tmpdir) / "test_project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text("[project]\nname='test'\n")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "app.py").write_text("def main(): pass\n")
        (project_dir / "requirements.txt").write_text("flask>=2.0\n")

        cache = _create_cache(str(Path(tmpdir) / "cache"))
        warmer = CacheWarmer(cache)
        warmer.add_project_warmup_tasks(str(project_dir))

        results = warmer.warmup()
        success_count = sum(1 for r in results if r.success)
        assert success_count >= 3  # 至少 3 个成功


def test_warmer_results_summary():
    """测试预热结果摘要"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = _create_cache(tmpdir)
        warmer = CacheWarmer(cache)
        warmer.add_task(name="task1", key="k1", compute_fn=lambda: "v1")
        warmer.add_task(name="task2", key="k2", compute_fn=lambda: "v2")
        warmer.warmup()

        summary = warmer.get_results_summary()
        assert "total" in summary
        assert "success" in summary
        assert "failed" in summary
        assert summary["total"] >= 2


def test_warmer_empty_summary():
    """测试空预热结果摘要"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = _create_cache(tmpdir)
        warmer = CacheWarmer(cache)
        summary = warmer.get_results_summary()
        assert summary["total"] == 0


# ==================== 静态辅助方法测试 ====================


def test_scan_project_files():
    """测试项目文件扫描"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        (project_dir / "main.py").write_text("pass")
        (project_dir / "utils.js").write_text("// js")

        result = CacheWarmer._scan_project_files(str(project_dir))
        assert "file_count" in result
        assert "files" in result
        assert result["file_count"] >= 2


def test_compute_language_stats():
    """测试语言统计计算"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        (project_dir / "a.py").write_text("print(1)\nprint(2)\n")
        (project_dir / "b.js").write_text("console.log(1);\n")

        result = CacheWarmer._compute_language_stats(str(project_dir))
        assert "languages" in result
        assert "Python" in result["languages"]
        assert "JavaScript" in result["languages"]


def test_get_project_meta():
    """测试项目元信息获取"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        (project_dir / "pyproject.toml").write_text("[project]\n")

        result = CacheWarmer._get_project_meta(str(project_dir))
        assert result["type"] == "python"
        assert result["build_system"] == "pyproject.toml"


def test_get_project_meta_node():
    """测试 Node 项目元信息"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        (project_dir / "package.json").write_text('{"name":"test"}')

        result = CacheWarmer._get_project_meta(str(project_dir))
        assert result["type"] == "node"


def test_scan_dependencies():
    """测试依赖扫描"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        (project_dir / "requirements.txt").write_text("flask>=2.0\nrequests\n")

        result = CacheWarmer._scan_dependencies(str(project_dir))
        assert "dependencies" in result
        assert "python" in result["dependencies"]
        assert "flask>=2.0" in result["dependencies"]["python"]


def test_scan_dependencies_node():
    """测试 Node 依赖扫描"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        pkg = {"dependencies": {"express": "^4.18.0"}, "devDependencies": {"jest": "^29.0.0"}}
        (project_dir / "package.json").write_text(json.dumps(pkg))

        result = CacheWarmer._scan_dependencies(str(project_dir))
        assert "node" in result["dependencies"]
        assert "express" in result["dependencies"]["node"]


# ==================== 运行所有测试 ====================


def run_all_tests():
    """运行所有测试"""
    tests = [
        test_warmup_task_creation,
        test_warmup_result_success,
        test_warmup_result_failure,
        test_warmup_result_cache_hit,
        test_warmer_add_task,
        test_warmer_add_multiple_tasks,
        test_warmer_execute,
        test_warmer_skip_existing,
        test_warmer_no_skip_existing,
        test_warmer_compute_failure,
        test_warmer_priority_order,
        test_warmer_no_tasks,
        test_project_warmup_tasks,
        test_project_warmup_execution,
        test_warmer_results_summary,
        test_warmer_empty_summary,
        test_scan_project_files,
        test_compute_language_stats,
        test_get_project_meta,
        test_get_project_meta_node,
        test_scan_dependencies,
        test_scan_dependencies_node,
    ]

    print("🧪 开始运行缓存预热模块测试...\n")
    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            print(f"  ✅ {test_fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {test_fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ {test_fn.__name__}: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print(f"\n📊 结果: {passed} 通过, {failed} 失败, 共 {len(tests)} 个测试")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
