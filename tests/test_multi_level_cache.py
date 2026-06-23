#!/usr/bin/env python3
"""
多级缓存系统单元测试
"""

import sys
import tempfile
import time
from pathlib import Path

# 添加项目根目录到路径，使用包导入
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.infrastructure.multi_level_cache import (  # noqa: E402
    CacheEntry,
    MemoryCacheBackend,
    FileCacheBackend,
    MultiLevelCache,
)


# ==================== CacheEntry 测试 ====================


def test_cache_entry_not_expired():
    """测试未过期的缓存条目"""
    entry = CacheEntry(key="k1", value="v1", created_at=time.time(), ttl=3600)
    assert not entry.is_expired


def test_cache_entry_expired():
    """测试已过期的缓存条目"""
    entry = CacheEntry(key="k1", value="v1", created_at=time.time() - 4000, ttl=3600)
    assert entry.is_expired


def test_cache_entry_no_ttl():
    """测试永不过期的缓存条目"""
    entry = CacheEntry(key="k1", value="v1", created_at=time.time() - 999999, ttl=0)
    assert not entry.is_expired


def test_cache_entry_serialization():
    """测试缓存条目序列化/反序列化"""
    entry = CacheEntry(key="k1", value={"a": 1}, created_at=1000.0, ttl=3600, metadata={"tag": "test"})
    d = entry.to_dict()
    restored = CacheEntry.from_dict(d)
    assert restored.key == "k1"
    assert restored.value == {"a": 1}
    assert restored.ttl == 3600
    assert restored.metadata == {"tag": "test"}


# ==================== MemoryCacheBackend 测试 ====================


def test_memory_set_get():
    """测试内存缓存读写"""
    backend = MemoryCacheBackend(max_size=100)
    entry = CacheEntry(key="k1", value="hello", created_at=time.time(), ttl=3600)
    assert backend.set(entry)
    result = backend.get("k1")
    assert result is not None
    assert result.value == "hello"


def test_memory_miss():
    """测试内存缓存未命中"""
    backend = MemoryCacheBackend()
    assert backend.get("nonexistent") is None


def test_memory_delete():
    """测试内存缓存删除"""
    backend = MemoryCacheBackend()
    entry = CacheEntry(key="k1", value="v1", created_at=time.time(), ttl=3600)
    backend.set(entry)
    assert backend.delete("k1")
    assert backend.get("k1") is None


def test_memory_exists():
    """测试内存缓存存在性检查"""
    backend = MemoryCacheBackend()
    entry = CacheEntry(key="k1", value="v1", created_at=time.time(), ttl=3600)
    backend.set(entry)
    assert backend.exists("k1")
    assert not backend.exists("k2")


def test_memory_expired_auto_delete():
    """测试内存缓存自动过期"""
    backend = MemoryCacheBackend()
    entry = CacheEntry(key="k1", value="v1", created_at=time.time() - 10, ttl=5)
    backend.set(entry)
    # 过期后 get 返回 None 并自动删除
    assert backend.get("k1") is None


def test_memory_clear():
    """测试内存缓存清空"""
    backend = MemoryCacheBackend()
    for i in range(10):
        backend.set(CacheEntry(key=f"k{i}", value=f"v{i}", created_at=time.time(), ttl=3600))
    count = backend.clear()
    assert count == 10
    assert backend.get("k0") is None


def test_memory_lru_eviction():
    """测试内存缓存 LRU 淘汰"""
    backend = MemoryCacheBackend(max_size=3)
    for i in range(5):
        backend.set(CacheEntry(key=f"k{i}", value=f"v{i}", created_at=time.time(), ttl=3600))
    # max_size=3，k0 和 k1 应该被淘汰
    assert backend.get("k0") is None
    assert backend.get("k1") is None
    assert backend.get("k2") is not None
    assert backend.get("k3") is not None
    assert backend.get("k4") is not None


def test_memory_stats():
    """测试内存缓存统计"""
    backend = MemoryCacheBackend()
    backend.set(CacheEntry(key="k1", value="v1", created_at=time.time(), ttl=3600))
    backend.get("k1")  # hit
    backend.get("k2")  # miss
    stats = backend.stats()
    assert stats["backend"] == "memory"
    assert stats["hits"] == 1
    assert stats["misses"] == 1


# ==================== FileCacheBackend 测试 ====================


def test_file_set_get():
    """测试文件缓存读写"""
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = FileCacheBackend(cache_dir=tmpdir)
        entry = CacheEntry(key="k1", value="file_val", created_at=time.time(), ttl=3600)
        assert backend.set(entry)
        result = backend.get("k1")
        assert result is not None
        assert result.value == "file_val"


def test_file_miss():
    """测试文件缓存未命中"""
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = FileCacheBackend(cache_dir=tmpdir)
        assert backend.get("nonexistent") is None


def test_file_delete():
    """测试文件缓存删除"""
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = FileCacheBackend(cache_dir=tmpdir)
        entry = CacheEntry(key="k1", value="v1", created_at=time.time(), ttl=3600)
        backend.set(entry)
        assert backend.delete("k1")
        assert backend.get("k1") is None


def test_file_expired_auto_delete():
    """测试文件缓存自动过期"""
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = FileCacheBackend(cache_dir=tmpdir)
        entry = CacheEntry(key="k1", value="v1", created_at=time.time() - 10, ttl=5)
        backend.set(entry)
        assert backend.get("k1") is None


def test_file_clear():
    """测试文件缓存清空"""
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = FileCacheBackend(cache_dir=tmpdir)
        for i in range(5):
            backend.set(CacheEntry(key=f"k{i}", value=f"v{i}", created_at=time.time(), ttl=3600))
        count = backend.clear()
        assert count == 5


def test_file_stats():
    """测试文件缓存统计"""
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = FileCacheBackend(cache_dir=tmpdir)
        backend.set(CacheEntry(key="k1", value="v1", created_at=time.time(), ttl=3600))
        stats = backend.stats()
        assert stats["backend"] == "file"
        assert stats["file_count"] == 1


# ==================== MultiLevelCache 测试 ====================


def test_multi_level_basic():
    """测试多级缓存基本读写"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = MultiLevelCache(
            default_ttl=3600,
            enable_memory=True,
            enable_file=True,
            enable_redis=False,
            file_cache_dir=tmpdir,
        )
        cache.set("key1", {"data": "hello"})
        result = cache.get("key1")
        assert result is not None
        assert result["data"] == "hello"


def test_multi_level_miss():
    """测试多级缓存未命中"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = MultiLevelCache(enable_memory=True, enable_file=True, enable_redis=False, file_cache_dir=tmpdir)
        assert cache.get("nonexistent") is None


def test_multi_level_delete():
    """测试多级缓存删除"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = MultiLevelCache(enable_memory=True, enable_file=True, enable_redis=False, file_cache_dir=tmpdir)
        cache.set("key1", "value1")
        assert cache.delete("key1")
        assert cache.get("key1") is None


def test_multi_level_exists():
    """测试多级缓存存在性"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = MultiLevelCache(enable_memory=True, enable_file=True, enable_redis=False, file_cache_dir=tmpdir)
        cache.set("key1", "value1")
        assert cache.exists("key1")
        assert not cache.exists("key2")


def test_multi_level_backfill():
    """测试多级缓存回填：L2 命中后回填到 L1"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = MultiLevelCache(
            default_ttl=3600,
            enable_memory=True,
            enable_file=True,
            enable_redis=False,
            file_cache_dir=tmpdir,
        )
        cache.set("key1", "value1")

        # 手动删除 L1 中的缓存，模拟 L1 miss
        cache._backends[0].delete("key1")

        # 从 L2 读取应回填到 L1
        result = cache.get("key1")
        assert result == "value1"

        # 验证 L1 已回填
        l1_entry = cache._backends[0].get("key1")
        assert l1_entry is not None
        assert l1_entry.value == "value1"


def test_multi_level_clear():
    """测试多级缓存清空"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = MultiLevelCache(enable_memory=True, enable_file=True, enable_redis=False, file_cache_dir=tmpdir)
        for i in range(5):
            cache.set(f"key{i}", f"value{i}")
        results = cache.clear()
        assert "memory" in results
        assert "file" in results


def test_multi_level_make_key():
    """测试缓存键生成"""
    key1 = MultiLevelCache.make_key("project", "path1")
    key2 = MultiLevelCache.make_key("project", "path2")
    key3 = MultiLevelCache.make_key("project", "path1")
    assert key1 != key2
    assert key1 == key3


def test_multi_level_stats():
    """测试多级缓存统计"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = MultiLevelCache(enable_memory=True, enable_file=True, enable_redis=False, file_cache_dir=tmpdir)
        cache.set("k1", "v1")
        stats = cache.stats()
        assert "levels" in stats
        assert "memory" in stats["levels"]
        assert "file" in stats["levels"]


def test_multi_level_get_or_compute():
    """测试缓存穿透模式"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = MultiLevelCache(enable_memory=True, enable_file=True, enable_redis=False, file_cache_dir=tmpdir)
        call_count = 0

        def compute():
            nonlocal call_count
            call_count += 1
            return "computed_value"

        # 首次调用：缓存 miss，执行 compute
        result1 = cache.get_or_compute("key1", compute)
        assert result1 == "computed_value"
        assert call_count == 1

        # 二次调用：缓存 hit，不执行 compute
        result2 = cache.get_or_compute("key1", compute)
        assert result2 == "computed_value"
        assert call_count == 1


def test_multi_level_invalidate_pattern():
    """测试模式匹配失效"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = MultiLevelCache(enable_memory=True, enable_file=True, enable_redis=False, file_cache_dir=tmpdir)
        cache.set("project:abc:files", "data1")
        cache.set("project:abc:stats", "data2")
        cache.set("project:xyz:files", "data3")

        count = cache.invalidate_pattern("project:abc")
        assert count >= 1


def test_memory_only_mode():
    """测试仅内存缓存模式"""
    cache = MultiLevelCache(enable_memory=True, enable_file=False, enable_redis=False)
    cache.set("k1", "v1")
    assert cache.get("k1") == "v1"
    assert len(cache._backends) == 1
    assert cache._backend_names == ["memory"]


def test_file_only_mode():
    """测试仅文件缓存模式"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = MultiLevelCache(enable_memory=False, enable_file=True, enable_redis=False, file_cache_dir=tmpdir)
        cache.set("k1", "v1")
        assert cache.get("k1") == "v1"
        assert len(cache._backends) == 1


# ==================== 运行所有测试 ====================


def run_all_tests():
    """运行所有测试"""
    tests = [
        test_cache_entry_not_expired,
        test_cache_entry_expired,
        test_cache_entry_no_ttl,
        test_cache_entry_serialization,
        test_memory_set_get,
        test_memory_miss,
        test_memory_delete,
        test_memory_exists,
        test_memory_expired_auto_delete,
        test_memory_clear,
        test_memory_lru_eviction,
        test_memory_stats,
        test_file_set_get,
        test_file_miss,
        test_file_delete,
        test_file_expired_auto_delete,
        test_file_clear,
        test_file_stats,
        test_multi_level_basic,
        test_multi_level_miss,
        test_multi_level_delete,
        test_multi_level_exists,
        test_multi_level_backfill,
        test_multi_level_clear,
        test_multi_level_make_key,
        test_multi_level_stats,
        test_multi_level_get_or_compute,
        test_multi_level_invalidate_pattern,
        test_memory_only_mode,
        test_file_only_mode,
    ]

    print("🧪 开始运行多级缓存系统测试...\n")
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
