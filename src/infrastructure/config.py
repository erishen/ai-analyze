"""
配置管理系统
支持环境变量、配置文件、默认值的优先级管理
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

from .exceptions import (
    ConfigException,
    InvalidConfigException,
)


@dataclass
class AnalysisConfig:
    """分析配置"""

    # 项目路径
    project_path: str = ""

    # Serena 配置
    serena_dir: str = ""

    # AST 配置
    ast_enabled: bool = True
    ast_max_depth: int = 10
    ast_languages: Optional[list] = None

    # AST 规则引擎配置
    ast_rules_config_file: str = ""  # 规则配置文件路径（空则用默认）
    ast_rules_disabled: Optional[list] = None  # 禁用的规则 ID 列表
    ast_rules_thresholds: Optional[dict] = None  # 自定义规则阈值 {rule_id: threshold}
    ast_rules_severities: Optional[dict] = None  # 自定义规则严重程度 {rule_id: severity}
    ast_rules_custom: Optional[list] = None  # 自定义规则列表

    # AI 配置
    ai_enabled: bool = True
    openai_api_key: str = ""
    openai_model: str = "openai/gpt-4"
    ai_timeout: int = 30
    ai_max_retries: int = 3

    # Docker 配置
    docker_enabled: bool = True
    docker_base_image: str = "python:3.11-slim"

    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 小时
    cache_dir: str = ".cache"

    # 多级缓存配置
    cache_memory_enabled: bool = True  # L1 内存缓存
    cache_file_enabled: bool = True  # L2 文件缓存
    cache_redis_enabled: bool = False  # L3 Redis 缓存（默认关闭）
    cache_memory_max_size: int = 512  # 内存缓存最大条目数
    cache_file_max_size_mb: int = 500  # 文件缓存最大容量 MB
    cache_redis_host: str = "localhost"  # Redis 主机
    cache_redis_port: int = 6379  # Redis 端口
    cache_redis_password: str = ""  # Redis 密码
    cache_warmup_enabled: bool = True  # 缓存预热
    cache_warmup_max_workers: int = 4  # 预热并行线程数

    # 增量分析配置
    incremental_enabled: bool = True

    # 日志配置
    log_level: str = "INFO"
    log_dir: str = "logs"

    # 输出配置
    output_dir: str = "reports"
    output_format: str = "json"  # json, markdown, html

    def __post_init__(self):
        """初始化后处理"""
        if self.ast_languages is None:
            self.ast_languages = ["python", "javascript", "go", "java"]
        if self.ast_rules_disabled is None:
            self.ast_rules_disabled = []
        if self.ast_rules_thresholds is None:
            self.ast_rules_thresholds = {}
        if self.ast_rules_severities is None:
            self.ast_rules_severities = {}
        if self.ast_rules_custom is None:
            self.ast_rules_custom = []

    # 敏感字段列表
    _SENSITIVE_KEYS = {"openai_api_key", "cache_redis_password"}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（敏感字段脱敏）"""
        data = asdict(self)
        for key in self._SENSITIVE_KEYS:
            if key in data and data[key]:
                data[key] = "***"
        return data

    def to_json(self) -> str:
        """转换为 JSON 字符串（敏感字段脱敏）"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def to_dict_raw(self) -> Dict[str, Any]:
        """转换为字典（包含敏感字段，仅内部使用）"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisConfig":
        """从字典创建配置"""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "AnalysisConfig":
        """从 JSON 字符串创建配置"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class ConfigManager:
    """配置管理器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.logger = logging.getLogger("ai-analyze.config")
        self.config = AnalysisConfig()
        self._load_config()

    def _load_config(self):
        """加载配置"""
        # 1. 加载默认配置
        self._load_defaults()

        # 2. 加载配置文件
        self._load_from_file()

        # 3. 加载环境变量
        self._load_from_env()

    def _load_defaults(self):
        """加载默认配置"""
        self.config = AnalysisConfig()
        self.logger.debug("已加载默认配置")

    def _load_from_file(self):
        """从配置文件加载"""
        config_file = Path(".env.json")
        if not config_file.exists():
            config_file = Path("config.json")

        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 更新配置
                for key, value in data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)

                self.logger.info(f"已从 {config_file} 加载配置")
            except Exception as e:
                self.logger.warning(f"加载配置文件失败: {e}")

    def _load_from_env(self):
        """从环境变量加载"""
        # 项目路径
        if project_path := os.getenv("PROJECT_PATH"):
            self.config.project_path = project_path

        # Serena 目录
        if serena_dir := os.getenv("SERENA_DIR"):
            self.config.serena_dir = serena_dir

        # AI 配置
        if api_key := os.getenv("OPENAI_API_KEY"):
            self.config.openai_api_key = api_key

        if model := os.getenv("OPENAI_MODEL"):
            self.config.openai_model = model

        # 日志级别
        if log_level := os.getenv("LOG_LEVEL"):
            self.config.log_level = log_level

        self.logger.debug("已从环境变量加载配置")

    def get_config(self) -> AnalysisConfig:
        """获取配置"""
        return self.config

    def set_config(self, **kwargs):
        """设置配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.debug(f"设置配置: {key}={value}")
            else:
                self.logger.warning(f"未知配置项: {key}")

    def validate(self) -> bool:
        """验证配置"""
        errors = []

        # 检查必需的配置
        if not self.config.project_path:
            errors.append("PROJECT_PATH 未设置")

        if self.config.ai_enabled and not self.config.openai_api_key:
            errors.append("AI 已启用但 OPENAI_API_KEY 未设置")

        if errors:
            error_msg = "; ".join(errors)
            self.logger.error(f"配置验证失败: {error_msg}")
            raise InvalidConfigException(error_msg)

        self.logger.info("配置验证通过")
        return True

    def save_to_file(self, filepath: str = "config.json"):
        """保存配置到文件"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.config.to_json())
            self.logger.info(f"配置已保存到 {filepath}")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            raise ConfigException(f"保存配置失败: {e}")

    def load_from_file(self, filepath: str):
        """从文件加载配置"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.config = AnalysisConfig.from_dict(data)
            self.logger.info(f"配置已从 {filepath} 加载")
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            raise ConfigException(f"加载配置失败: {e}")

    def print_config(self):
        """打印配置"""
        print("\n" + "=" * 60)
        print("📋 当前配置")
        print("=" * 60)
        for key, value in self.config.to_dict().items():
            if "key" in key.lower() or "password" in key.lower():
                # 隐藏敏感信息
                value = "***" if value else ""
            print(f"  {key}: {value}")
        print("=" * 60 + "\n")


# 全局配置管理器实例
_config_manager = ConfigManager()


def get_config() -> AnalysisConfig:
    """获取全局配置"""
    return _config_manager.get_config()


def set_config(**kwargs):
    """设置全局配置"""
    _config_manager.set_config(**kwargs)


def validate_config() -> bool:
    """验证全局配置"""
    return _config_manager.validate()


def save_config(filepath: str = "config.json"):
    """保存全局配置"""
    _config_manager.save_to_file(filepath)


def load_config(filepath: str):
    """加载全局配置"""
    _config_manager.load_from_file(filepath)


def print_config():
    """打印全局配置"""
    _config_manager.print_config()


if __name__ == "__main__":
    # 测试配置系统
    config = get_config()
    print(f"项目路径: {config.project_path}")
    print(f"AI 启用: {config.ai_enabled}")
    print(f"缓存启用: {config.cache_enabled}")

    # 打印所有配置
    print_config()
