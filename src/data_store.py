#!/usr/bin/env python3
"""
数据持久化模块
基于 SQLite 存储分析结果，支持查询和聚合
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AnalysisStore:
    """分析结果存储"""

    def __init__(self, db_path: str = ".analysis_data/analysis.db") -> None:
        self.db_path = db_path
        self.logger = logging.getLogger("ai-analyze.data_store")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库"""
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    project_path TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    duration REAL DEFAULT 0.0,
                    metadata_json TEXT DEFAULT '{}'
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_project_name
                ON analysis_results(project_name)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON analysis_results(timestamp)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_analysis_type
                ON analysis_results(analysis_type)
            """
            )

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def save(
        self,
        project_name: str,
        project_path: str,
        analysis_type: str,
        result: Dict[str, Any],
        duration: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """保存分析结果

        Returns:
            记录 ID
        """
        timestamp = datetime.now().isoformat()
        result_json = json.dumps(result, ensure_ascii=False)
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False)

        with self._conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO analysis_results
                    (project_name, project_path, analysis_type,
                     result_json, timestamp, duration, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_name,
                    project_path,
                    analysis_type,
                    result_json,
                    timestamp,
                    duration,
                    metadata_json,
                ),
            )
            record_id = cursor.lastrowid
            self.logger.info(
                "Saved %s analysis for %s (id=%d)",
                analysis_type,
                project_name,
                record_id,
            )
            return record_id

    def get_latest(
        self,
        project_name: str,
        analysis_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """获取最新分析结果"""
        with self._conn() as conn:
            if analysis_type:
                rows = conn.execute(
                    """
                    SELECT id, project_name, project_path, analysis_type,
                           result_json, timestamp, duration, metadata_json
                    FROM analysis_results
                    WHERE project_name = ? AND analysis_type = ?
                    ORDER BY timestamp DESC LIMIT ?
                    """,
                    (project_name, analysis_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, project_name, project_path, analysis_type,
                           result_json, timestamp, duration, metadata_json
                    FROM analysis_results
                    WHERE project_name = ?
                    ORDER BY timestamp DESC LIMIT ?
                    """,
                    (project_name, limit),
                ).fetchall()

        return [self._row_to_dict(row) for row in rows]

    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """按 ID 获取"""
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT id, project_name, project_path, analysis_type,
                       result_json, timestamp, duration, metadata_json
                FROM analysis_results WHERE id = ?
                """,
                (record_id,),
            ).fetchone()

        if row is None:
            return None
        return self._row_to_dict(row)

    def list_projects(self) -> List[Dict[str, Any]]:
        """列出所有项目及其分析统计"""
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT project_name, project_path,
                       COUNT(*) as total_analyses,
                       MIN(timestamp) as first_analysis,
                       MAX(timestamp) as last_analysis
                FROM analysis_results
                GROUP BY project_name, project_path
                ORDER BY last_analysis DESC
                """
            ).fetchall()

        return [
            {
                "project_name": row[0],
                "project_path": row[1],
                "total_analyses": row[2],
                "first_analysis": row[3],
                "last_analysis": row[4],
            }
            for row in rows
        ]

    def get_trend(
        self,
        project_name: str,
        analysis_type: str,
        metric_path: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """获取指标趋势数据"""
        records = self.get_latest(project_name, analysis_type, limit)
        trend = []
        for record in reversed(records):
            value = self._extract_metric(record["result"], metric_path)
            if value is not None:
                trend.append(
                    {
                        "timestamp": record["timestamp"],
                        "value": float(value),
                    }
                )
        return trend

    def delete_old(self, days: int = 90) -> int:
        """删除旧记录"""
        cutoff = datetime.now().timestamp() - (days * 86400)
        cutoff_str = datetime.fromtimestamp(cutoff).isoformat()

        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM analysis_results WHERE timestamp < ?",
                (cutoff_str,),
            )
            deleted = cursor.rowcount
            if deleted > 0:
                self.logger.info("Deleted %d old records (older than %d days)", deleted, days)
            return deleted

    def _row_to_dict(self, row: tuple) -> Dict[str, Any]:
        return {
            "id": row[0],
            "project_name": row[1],
            "project_path": row[2],
            "analysis_type": row[3],
            "result": json.loads(row[4]),
            "timestamp": row[5],
            "duration": row[6],
            "metadata": json.loads(row[7]),
        }

    @staticmethod
    def _extract_metric(data: Dict[str, Any], path: str) -> Any:
        """从嵌套字典中提取值"""
        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
