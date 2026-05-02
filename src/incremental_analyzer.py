#!/usr/bin/env python3
"""
增量分析器 - 支持增量分析，加速 CI/CD
缓存分析结果，只分析修改的文件
支持多级缓存（内存 + 文件 + Redis）
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .multi_level_cache import MultiLevelCache

logger = logging.getLogger(__name__)


@dataclass
class FileHash:
    """文件哈希信息"""

    file_path: str
    hash: str
    modified_time: float


@dataclass
class CacheMetadata:
    """缓存元数据"""

    project_path: str
    created_at: str
    updated_at: str
    file_count: int
    total_complexity: float
    file_hashes: Dict[str, str]  # file_path -> hash


class IncrementalAnalyzer:
    """增量分析器，支持多级缓存"""

    def __init__(
        self,
        cache_dir: str = ".ai-analyze-cache",
        use_multi_level: bool = True,
        cache_ttl: int = 3600,
        enable_redis: bool = False,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_password: Optional[str] = None,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self._use_multi_level = use_multi_level
        self._cache: Optional[MultiLevelCache] = None
        self._file_result_cache: Dict[str, Any] = {}  # 文件级别结果对象缓存

        if use_multi_level:
            self._cache = MultiLevelCache(
                default_ttl=cache_ttl,
                enable_memory=True,
                enable_file=True,
                enable_redis=enable_redis,
                file_cache_dir=str(self.cache_dir / "mlc"),
                redis_host=redis_host,
                redis_port=redis_port,
                redis_password=redis_password or None,
            )
            logger.info(f"增量分析器已启用多级缓存 (TTL={cache_ttl}s)")
        else:
            self._cache = None
            logger.info(f"增量分析器使用传统文件缓存: {self.cache_dir}")

    def get_file_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"计算文件哈希失败 {file_path}: {e}")
            return ""

    def get_project_hash(self, project_path: str) -> str:
        """计算项目哈希"""
        return hashlib.md5(project_path.encode()).hexdigest()[:12]

    def get_cache_path(self, project_path: str) -> Path:
        """获取缓存文件路径"""
        project_hash = self.get_project_hash(project_path)
        return self.cache_dir / f"{project_hash}_cache.json"

    def load_cache(self, project_path: str) -> Optional[Dict[str, Any]]:
        """加载缓存（优先多级缓存，回退到传统文件缓存）"""
        # 多级缓存
        if self._use_multi_level and self._cache:
            cache_key = self._cache.make_key("analysis", project_path)
            result = self._cache.get(cache_key)
            if result is not None:
                logger.info(f"✅ 多级缓存命中: {project_path}")
                return result

        # 回退到传统文件缓存
        cache_path = self.get_cache_path(project_path)

        if not cache_path.exists():
            logger.info(f"缓存不存在: {cache_path}")
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            logger.info(f"✅ 加载缓存: {cache_path.name}")

            # 如果启用了多级缓存，回填到多级缓存
            if self._use_multi_level and self._cache:
                cache_key = self._cache.make_key("analysis", project_path)
                self._cache.set(cache_key, cache_data)

            return cache_data
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
            return None

    def save_cache(self, project_path: str, analysis_result: Dict[str, Any], file_hashes: Dict[str, str]) -> None:
        """保存缓存（同时写入多级缓存和传统文件缓存）"""
        cache_data = {
            "metadata": {
                "project_path": project_path,
                "created_at": analysis_result.get("generated_at", datetime.now().isoformat()),
                "updated_at": datetime.now().isoformat(),
                "file_count": len(file_hashes),
                "total_complexity": analysis_result.get("summary", {}).get("total_complexity", 0),
                "file_hashes": file_hashes,
            },
            "analysis": analysis_result,
        }

        # 保存到多级缓存
        if self._use_multi_level and self._cache:
            cache_key = self._cache.make_key("analysis", project_path)
            self._cache.set(cache_key, cache_data)
            logger.info(f"💾 多级缓存已保存: {project_path}")

        # 保存到传统文件缓存（兼容性）
        cache_path = self.get_cache_path(project_path)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 保存缓存: {cache_path.name}")
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")

    def get_changed_files(
        self, project_path: str, current_files: List[str], cached_data: Optional[Dict[str, Any]]
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        获取修改的文件

        Returns:
            (modified_files, new_files, deleted_files)
        """
        if not cached_data:
            # 没有缓存，所有文件都是新的
            return [], current_files, []

        cached_hashes = cached_data.get("metadata", {}).get("file_hashes", {})
        current_set = set(current_files)
        cached_set = set(cached_hashes.keys())

        # 修改的文件
        modified = []
        for file_path in current_set & cached_set:
            current_hash = self.get_file_hash(file_path)
            cached_hash = cached_hashes.get(file_path, "")
            if current_hash != cached_hash:
                modified.append(file_path)

        # 新增的文件
        new_files = list(current_set - cached_set)

        # 删除的文件
        deleted = list(cached_set - current_set)

        return modified, new_files, deleted

    def should_reanalyze(
        self, project_path: str, current_files: List[str], cached_data: Optional[Dict[str, Any]]
    ) -> bool:
        """判断是否需要重新分析"""
        if not cached_data:
            return True

        modified, new_files, deleted = self.get_changed_files(project_path, current_files, cached_data)

        # 如果有任何变化，需要重新分析
        return len(modified) > 0 or len(new_files) > 0 or len(deleted) > 0

    def get_analysis_status(
        self, project_path: str, current_files: List[str], cached_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """获取分析状态"""
        if not cached_data:
            return {
                "status": "no_cache",
                "message": "没有缓存，需要完整分析",
                "modified_files": [],
                "new_files": current_files,
                "deleted_files": [],
                "total_changes": len(current_files),
            }

        modified, new_files, deleted = self.get_changed_files(project_path, current_files, cached_data)

        total_changes = len(modified) + len(new_files) + len(deleted)

        if total_changes == 0:
            return {
                "status": "no_changes",
                "message": "没有文件变化，可以使用缓存",
                "modified_files": [],
                "new_files": [],
                "deleted_files": [],
                "total_changes": 0,
            }
        else:
            return {
                "status": "has_changes",
                "message": f"检测到 {total_changes} 个文件变化",
                "modified_files": modified,
                "new_files": new_files,
                "deleted_files": deleted,
                "total_changes": total_changes,
                "change_percentage": (total_changes / len(current_files) * 100) if current_files else 0,
            }

    def merge_analysis_results(
        self, cached_analysis: Dict[str, Any], new_analysis: Dict[str, Any], changed_files: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        融合缓存的分析结果和新的分析结果

        Args:
            cached_analysis: 缓存的分析结果
            new_analysis: 新的分析结果
            changed_files: 变化的文件信息

        Returns:
            融合后的分析结果
        """
        # 获取缓存中未修改的文件
        cached_files = {f["file_path"]: f for f in cached_analysis.get("files", [])}
        new_files = {f["file_path"]: f for f in new_analysis.get("files", [])}

        # 构建融合结果
        merged_files = []

        # 添加未修改的文件（优先使用内存缓存，避免重复反序列化）
        for file_path, file_data in cached_files.items():
            if file_path not in changed_files.get("modified_files", []) and file_path not in changed_files.get(
                "deleted_files", []
            ):
                # 尝试从内存缓存获取
                cached_result = self._file_result_cache.get(file_path)
                if cached_result is not None:
                    merged_files.append(cached_result)
                else:
                    merged_files.append(file_data)
                    self._file_result_cache[file_path] = file_data

        # 添加新分析的文件
        for fp, fd in new_files.items():
            merged_files.append(fd)
            self._file_result_cache[fp] = fd

        # 重新计算摘要
        total_complexity = 0.0
        total_code_smells = 0
        total_quality = 0.0
        language_stats: Dict[str, int] = {}

        for file_data in merged_files:
            language = file_data.get("language", "unknown")
            language_stats[language] = language_stats.get(language, 0) + 1

            # 累计复杂度
            if file_data.get("overall_complexity"):
                cc = file_data["overall_complexity"].get("cyclomatic_complexity", 0)
                total_complexity += cc

            # 累计代码坏味道
            total_code_smells += len(file_data.get("code_smells", []))

            # 累计质量分数
            for symbol in file_data.get("symbols", []):
                total_quality += symbol.get("quality_score", 0)

        # 计算平均质量分数
        total_symbols = sum(len(f.get("symbols", [])) for f in merged_files)
        avg_quality = (total_quality / total_symbols) if total_symbols > 0 else 100.0

        return {
            "project_path": new_analysis.get("project_path"),
            "generated_at": datetime.now().isoformat(),
            "files": merged_files,
            "summary": {
                "language_stats": language_stats,
                "total_complexity": total_complexity,
                "total_code_smells": total_code_smells,
                "quality_score": avg_quality,
                "incremental": True,
                "merged_from_cache": True,
            },
        }

    def clear_cache(self, project_path: Optional[str] = None) -> int:
        """
        清除缓存

        Args:
            project_path: 如果指定，只清除该项目的缓存；否则清除所有缓存

        Returns:
            清除的缓存文件数量
        """
        count = 0

        # 清除多级缓存
        if self._use_multi_level and self._cache:
            if project_path:
                cache_key = self._cache.make_key("analysis", project_path)
                if self._cache.delete(cache_key):
                    count += 1
            else:
                results = self._cache.clear()
                count = sum(results.values())

        # 清除传统文件缓存
        if not self.cache_dir.exists():
            return count

        if project_path:
            cache_path = self.get_cache_path(project_path)
            if cache_path.exists():
                try:
                    cache_path.unlink()
                    logger.info(f"🗑️  已删除缓存: {cache_path.name}")
                    count += 1
                except Exception as e:
                    logger.warning(f"删除缓存失败: {e}")
        else:
            cache_files = list(self.cache_dir.glob("*_cache.json"))
            for cache_file in cache_files:
                try:
                    cache_file.unlink()
                    logger.info(f"🗑️  已删除缓存: {cache_file.name}")
                    count += 1
                except Exception as e:
                    logger.warning(f"删除缓存失败: {cache_file.name} - {e}")

        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        stats: Dict[str, Any] = {
            "cache_dir": str(self.cache_dir),
            "multi_level_enabled": self._use_multi_level,
        }

        # 传统文件缓存统计
        if self.cache_dir.exists():
            cache_files = list(self.cache_dir.glob("*_cache.json"))
            total_size = sum(f.stat().st_size for f in cache_files)
            stats["traditional"] = {
                "cache_files": len(cache_files),
                "total_size": total_size,
                "size_mb": total_size / (1024 * 1024),
            }

        # 多级缓存统计
        if self._use_multi_level and self._cache:
            stats["multi_level"] = self._cache.stats()

        return stats
