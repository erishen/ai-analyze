#!/usr/bin/env python3
"""
多级缓存系统
支持 L1 内存缓存 + L2 文件缓存 + L3 Redis 缓存
智能缓存失效策略，TTL 管理，缓存预热
"""

import hashlib
import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    created_at: float
    ttl: int  # 秒，0 表示永不过期
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if self.ttl == 0:
            return False
        return (time.time() - self.created_at) > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "ttl": self.ttl,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        return cls(
            key=data["key"],
            value=data["value"],
            created_at=data["created_at"],
            ttl=data["ttl"],
            metadata=data.get("metadata", {}),
        )


class CacheBackend(ABC):
    """缓存后端基类"""

    @abstractmethod
    def get(self, key: str) -> Optional[CacheEntry]:
        pass

    @abstractmethod
    def set(self, entry: CacheEntry) -> bool:
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def clear(self) -> int:
        pass

    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        pass


class MemoryCacheBackend(CacheBackend):
    """L1 内存缓存 - 基于 LRU 策略"""

    def __init__(self, max_size: int = 512, max_memory_mb: int = 100):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._max_memory_bytes = max_memory_mb * 1024 * 1024
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[CacheEntry]:
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.is_expired:
                    del self._cache[key]
                    self._misses += 1
                    return None
                # LRU: 移到末尾
                self._cache.move_to_end(key)
                self._hits += 1
                return entry
            self._misses += 1
            return None

    def set(self, entry: CacheEntry) -> bool:
        with self._lock:
            if entry.key in self._cache:
                del self._cache[entry.key]
            self._cache[entry.key] = entry
            self._cache.move_to_end(entry.key)
            self._evict_if_needed()
            return True

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                return not self._cache[key].is_expired
            return False

    def clear(self) -> int:
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._hits + self._misses
            return {
                "backend": "memory",
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": (self._hits / total * 100) if total > 0 else 0,
            }

    def _evict_if_needed(self):
        """LRU 淘汰"""
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)


class FileCacheBackend(CacheBackend):
    """L2 文件缓存"""

    def __init__(self, cache_dir: str = ".cache", max_size_mb: int = 500):
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._hits = 0
        self._misses = 0

    def _key_to_path(self, key: str) -> Path:
        """缓存键转文件路径"""
        safe_key = hashlib.sha256(key.encode()).hexdigest()[:32]
        return self._cache_dir / f"{safe_key}.cache"

    def get(self, key: str) -> Optional[CacheEntry]:
        path = self._key_to_path(key)
        if not path.exists():
            self._misses += 1
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            entry = CacheEntry.from_dict(data)
            if entry.is_expired:
                path.unlink(missing_ok=True)
                self._misses += 1
                return None
            self._hits += 1
            return entry
        except Exception as e:
            logger.warning(f"文件缓存读取失败 {key}: {e}")
            self._misses += 1
            return None

    def set(self, entry: CacheEntry) -> bool:
        path = self._key_to_path(entry.key)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entry.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.warning(f"文件缓存写入失败 {entry.key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        path = self._key_to_path(key)
        if path.exists():
            try:
                path.unlink()
                return True
            except Exception as e:
                logger.warning(f"文件缓存删除失败 {key}: {e}")
        return False

    def exists(self, key: str) -> bool:
        entry = self.get(key)
        return entry is not None

    def clear(self) -> int:
        count = 0
        for f in self._cache_dir.glob("*.cache"):
            try:
                f.unlink()
                count += 1
            except Exception:
                pass
        return count

    def stats(self) -> Dict[str, Any]:
        files = list(self._cache_dir.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in files)
        total = self._hits + self._misses
        return {
            "backend": "file",
            "cache_dir": str(self._cache_dir),
            "file_count": len(files),
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_mb": self._max_size_bytes / (1024 * 1024),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": (self._hits / total * 100) if total > 0 else 0,
        }


class RedisCacheBackend(CacheBackend):
    """L3 Redis 缓存（可选）"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "ai-analyze:",
    ):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._prefix = prefix
        self._client = None
        self._hits = 0
        self._misses = 0
        self._connect()

    def _connect(self):
        """连接 Redis"""
        try:
            import redis

            self._client = redis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            self._client.ping()
            logger.info(f"Redis 缓存已连接: {self._host}:{self._port}")
        except ImportError:
            logger.warning("redis 库未安装，Redis 缓存不可用。安装: pip install redis")
            self._client = None
        except Exception as e:
            logger.warning(f"Redis 连接失败: {e}，Redis 缓存不可用")
            self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def _prefixed_key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get(self, key: str) -> Optional[CacheEntry]:
        if not self._client:
            self._misses += 1
            return None
        try:
            data = self._client.get(self._prefixed_key(key))
            if data is None:
                self._misses += 1
                return None
            entry = CacheEntry.from_dict(json.loads(data))
            if entry.is_expired:
                self._client.delete(self._prefixed_key(key))
                self._misses += 1
                return None
            self._hits += 1
            return entry
        except Exception as e:
            logger.warning(f"Redis 缓存读取失败 {key}: {e}")
            self._misses += 1
            return None

    def set(self, entry: CacheEntry) -> bool:
        if not self._client:
            return False
        try:
            ttl = entry.ttl if entry.ttl > 0 else None
            self._client.set(
                self._prefixed_key(entry.key),
                json.dumps(entry.to_dict(), ensure_ascii=False),
                ex=ttl,
            )
            return True
        except Exception as e:
            logger.warning(f"Redis 缓存写入失败 {entry.key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        if not self._client:
            return False
        try:
            return self._client.delete(self._prefixed_key(key)) > 0
        except Exception as e:
            logger.warning(f"Redis 缓存删除失败 {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        if not self._client:
            return False
        try:
            return self._client.exists(self._prefixed_key(key)) > 0
        except Exception:
            return False

    def clear(self) -> int:
        if not self._client:
            return 0
        try:
            keys = self._client.keys(f"{self._prefix}*")
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception:
            return 0

    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        result = {
            "backend": "redis",
            "available": self.available,
            "host": self._host,
            "port": self._port,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": (self._hits / total * 100) if total > 0 else 0,
        }
        if self._client:
            try:
                info = self._client.info("memory")
                result["used_memory_mb"] = info.get("used_memory", 0) / (1024 * 1024)
                keys = self._client.keys(f"{self._prefix}*")
                result["key_count"] = len(keys)
            except Exception:
                pass
        return result


class MultiLevelCache:
    """
    多级缓存系统
    L1 内存 -> L2 文件 -> L3 Redis
    读取时自动回填，写入时逐级写入
    """

    def __init__(
        self,
        default_ttl: int = 3600,
        enable_memory: bool = True,
        enable_file: bool = True,
        enable_redis: bool = False,
        memory_max_size: int = 512,
        file_cache_dir: str = ".cache",
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_password: Optional[str] = None,
    ):
        self._default_ttl = default_ttl
        self._backends: List[CacheBackend] = []
        self._backend_names: List[str] = []

        if enable_memory:
            mem_backend = MemoryCacheBackend(max_size=memory_max_size)
            self._backends.append(mem_backend)
            self._backend_names.append("memory")

        if enable_file:
            file_backend = FileCacheBackend(cache_dir=file_cache_dir)
            self._backends.append(file_backend)
            self._backend_names.append("file")

        if enable_redis:
            redis_backend = RedisCacheBackend(host=redis_host, port=redis_port, password=redis_password)
            if redis_backend.available:
                self._backends.append(redis_backend)
                self._backend_names.append("redis")
            else:
                logger.info("Redis 缓存不可用，跳过")

        logger.info(f"多级缓存已初始化: {' -> '.join(self._backend_names)} (TTL={default_ttl}s)")

    @staticmethod
    def make_key(*parts: str) -> str:
        """生成缓存键"""
        combined = ":".join(str(p) for p in parts)
        return hashlib.sha256(combined.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        多级读取，自动回填
        优先从 L1 读取，miss 时逐级查找并回填
        """
        for i, backend in enumerate(self._backends):
            entry = backend.get(key)
            if entry is not None:
                # 回填到更高级别缓存
                if i > 0:
                    self._backfill(key, entry, target_levels=list(range(i)))
                logger.debug(f"缓存命中 [{self._backend_names[i]}]: {key[:16]}...")
                return entry.value
        logger.debug(f"缓存未命中: {key[:16]}...")
        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """写入所有缓存级别"""
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            ttl=ttl or self._default_ttl,
            metadata=metadata or {},
        )
        success = True
        for backend in self._backends:
            if not backend.set(entry):
                success = False
        return success

    def delete(self, key: str) -> bool:
        """从所有缓存级别删除"""
        results = [backend.delete(key) for backend in self._backends]
        return any(results)

    def exists(self, key: str) -> bool:
        """检查任意级别是否存在"""
        return any(backend.exists(key) for backend in self._backends)

    def clear(self) -> Dict[str, int]:
        """清除所有缓存"""
        results = {}
        for name, backend in zip(self._backend_names, self._backends):
            results[name] = backend.clear()
        return results

    def stats(self) -> Dict[str, Any]:
        """获取所有级别统计"""
        return {
            "levels": self._backend_names,
            "backends": {name: backend.stats() for name, backend in zip(self._backend_names, self._backends)},
        }

    def _backfill(self, key: str, entry: CacheEntry, target_levels: List[int]) -> None:
        """回填到更高级别缓存"""
        for level in target_levels:
            try:
                self._backends[level].set(entry)
            except Exception as e:
                logger.warning(f"回填缓存失败 [L{level}]: {e}")

    def invalidate_pattern(self, pattern: str) -> int:
        """
        按模式使缓存失效
        支持 project:xxx:* 形式的模式
        """
        count = 0
        for backend in self._backends:
            if isinstance(backend, FileCacheBackend):
                # 文件缓存：遍历查找匹配
                for f in backend._cache_dir.glob("*.cache"):
                    try:
                        with open(f, "r", encoding="utf-8") as fh:
                            data = json.load(fh)
                        if pattern in data.get("key", ""):
                            f.unlink()
                            count += 1
                    except Exception:
                        pass
            elif isinstance(backend, MemoryCacheBackend):
                keys_to_delete = [k for k in backend._cache if pattern in k]
                for k in keys_to_delete:
                    backend.delete(k)
                    count += 1
            elif isinstance(backend, RedisCacheBackend) and backend.available and backend._client is not None:
                try:
                    keys = backend._client.keys(f"{backend._prefix}*{pattern}*")  # type: ignore[union-attr]
                    if keys:
                        count += backend._client.delete(*keys)  # type: ignore[union-attr]
                except Exception:
                    pass
        return count

    def get_or_compute(
        self,
        key: str,
        compute_fn,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        缓存穿透模式：先查缓存，miss 则计算并缓存
        """
        value = self.get(key)
        if value is not None:
            return value
        value = compute_fn()
        self.set(key, value, ttl=ttl, metadata=metadata)
        return value
