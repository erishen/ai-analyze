"""Tests for logger module - UnifiedLogger and LoggerConfig"""

import logging


from src.logger import UnifiedLogger, LoggerConfig


class TestLoggerConfig:
    def test_log_dir_is_path(self):
        assert LoggerConfig.LOG_DIR is not None

    def test_log_file_is_path(self):
        assert LoggerConfig.LOG_FILE is not None

    def test_error_log_file_is_path(self):
        assert LoggerConfig.ERROR_LOG_FILE is not None


class TestUnifiedLogger:
    def setup_method(self):
        """Reset singleton"""
        UnifiedLogger._instance = None

    def test_singleton(self):
        l1 = UnifiedLogger()
        l2 = UnifiedLogger()
        assert l1 is l2

    def test_get_logger(self):
        logger = UnifiedLogger().get_logger("test")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_different_names(self):
        ul = UnifiedLogger()
        l1 = ul.get_logger("module1")
        l2 = ul.get_logger("module2")
        assert l1.name != l2.name

    def test_get_logger_same_name_returns_same(self):
        ul = UnifiedLogger()
        l1 = ul.get_logger("test")
        l2 = ul.get_logger("test")
        assert l1 is l2
