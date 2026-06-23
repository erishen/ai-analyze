"""Tests for config module - AnalysisConfig and ConfigManager"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from src.infrastructure.config import AnalysisConfig, ConfigManager
from src.infrastructure.exceptions import InvalidConfigException


class TestAnalysisConfig:
    """AnalysisConfig dataclass tests"""

    def test_default_values(self):
        config = AnalysisConfig()
        assert config.project_path == ""
        assert config.serena_dir == ""
        assert config.ast_enabled is True
        assert config.ast_max_depth == 10
        assert config.ai_enabled is True
        assert config.docker_enabled is True
        assert config.cache_enabled is True
        assert config.cache_ttl == 3600
        assert config.log_level == "INFO"
        assert config.output_format == "json"

    def test_post_init_defaults(self):
        config = AnalysisConfig()
        assert config.ast_languages == ["python", "javascript", "go", "java"]
        assert config.ast_rules_disabled == []
        assert config.ast_rules_thresholds == {}
        assert config.ast_rules_severities == {}
        assert config.ast_rules_custom == []

    def test_custom_values(self):
        config = AnalysisConfig(
            project_path="/tmp/test",
            ast_enabled=False,
            cache_ttl=7200,
        )
        assert config.project_path == "/tmp/test"
        assert config.ast_enabled is False
        assert config.cache_ttl == 7200

    def test_to_dict(self):
        config = AnalysisConfig(project_path="/tmp/test")
        d = config.to_dict()
        assert isinstance(d, dict)
        assert d["project_path"] == "/tmp/test"
        assert d["ast_enabled"] is True

    def test_to_json(self):
        config = AnalysisConfig(project_path="/tmp/test")
        j = config.to_json()
        data = json.loads(j)
        assert data["project_path"] == "/tmp/test"

    def test_from_dict(self):
        data = {"project_path": "/tmp/test", "cache_ttl": 7200}
        config = AnalysisConfig.from_dict(data)
        assert config.project_path == "/tmp/test"
        assert config.cache_ttl == 7200

    def test_from_json(self):
        j = json.dumps({"project_path": "/tmp/test", "ai_enabled": False})
        config = AnalysisConfig.from_json(j)
        assert config.project_path == "/tmp/test"
        assert config.ai_enabled is False

    def test_cache_config_defaults(self):
        config = AnalysisConfig()
        assert config.cache_memory_enabled is True
        assert config.cache_file_enabled is True
        assert config.cache_redis_enabled is False
        assert config.cache_memory_max_size == 512
        assert config.cache_redis_host == "localhost"
        assert config.cache_redis_port == 6379
        assert config.cache_warmup_enabled is True

    def test_ast_rules_config_custom(self):
        config = AnalysisConfig(
            ast_rules_disabled=["COMPLEX001"],
            ast_rules_thresholds={"COMPLEX002": 20},
            ast_rules_severities={"DESIGN001": "critical"},
        )
        assert config.ast_rules_disabled == ["COMPLEX001"]
        assert config.ast_rules_thresholds == {"COMPLEX002": 20}
        assert config.ast_rules_severities == {"DESIGN001": "critical"}


class TestConfigManager:
    """ConfigManager singleton tests"""

    def setup_method(self):
        """Reset singleton between tests"""
        ConfigManager._instance = None

    def test_singleton(self):
        m1 = ConfigManager()
        m2 = ConfigManager()
        assert m1 is m2

    def test_get_config(self):
        manager = ConfigManager()
        config = manager.get_config()
        assert isinstance(config, AnalysisConfig)

    def test_set_config(self):
        manager = ConfigManager()
        manager.set_config(project_path="/tmp/test", cache_ttl=7200)
        config = manager.get_config()
        assert config.project_path == "/tmp/test"
        assert config.cache_ttl == 7200

    def test_set_config_unknown_key(self):
        manager = ConfigManager()
        # Should not raise, just log warning
        manager.set_config(nonexistent_key="value")

    def test_validate_no_project_path(self):
        manager = ConfigManager()
        # Reset project_path to empty to trigger validation failure
        manager.config.project_path = ""
        manager.config.ai_enabled = False
        # But if project_path is empty and AI is off, it should still fail
        # because project_path is required
        manager.config.ai_enabled = True
        manager.config.openai_api_key = ""
        with pytest.raises(InvalidConfigException):
            manager.validate()

    def test_validate_ai_enabled_no_key(self):
        manager = ConfigManager()
        manager.set_config(project_path="/tmp/test", ai_enabled=True, openai_api_key="")
        with pytest.raises(InvalidConfigException):
            manager.validate()

    def test_validate_success(self):
        manager = ConfigManager()
        manager.set_config(
            project_path="/tmp/test",
            ai_enabled=False,
        )
        assert manager.validate() is True

    def test_save_and_load_config(self):
        ConfigManager._instance = None
        manager = ConfigManager()
        manager.set_config(project_path="/tmp/test", cache_ttl=9999)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            manager.save_to_file(filepath)

            ConfigManager._instance = None
            manager2 = ConfigManager()
            manager2.load_from_file(filepath)
            config = manager2.get_config()
            assert config.project_path == "/tmp/test"
            assert config.cache_ttl == 9999
        finally:
            os.unlink(filepath)

    def test_load_from_env(self):
        ConfigManager._instance = None
        with patch.dict(
            os.environ,
            {
                "PROJECT_PATH": "/env/test",
                "OPENAI_API_KEY": "sk-test-key",
                "LOG_LEVEL": "DEBUG",
            },
        ):
            manager = ConfigManager()
            config = manager.get_config()
            assert config.project_path == "/env/test"
            assert config.openai_api_key == "sk-test-key"
            assert config.log_level == "DEBUG"

    def test_print_config(self, capsys):
        manager = ConfigManager()
        manager.print_config()
        captured = capsys.readouterr()
        assert "当前配置" in captured.out
