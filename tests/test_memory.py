"""Tests for memory module - MemoryInfo, MemoryMonitor, MemoryLimiter"""

from datetime import datetime
from unittest.mock import patch, MagicMock

from src.memory import MemoryInfo, MemoryMonitor, MemoryLimiter


class TestMemoryInfo:
    def test_default_values(self):
        info = MemoryInfo()
        assert info.rss == 0
        assert info.vms == 0
        assert info.percent == 0.0

    def test_rss_mb(self):
        info = MemoryInfo(rss=1024 * 1024 * 100)
        assert abs(info.rss_mb - 100.0) < 0.01

    def test_vms_mb(self):
        info = MemoryInfo(vms=1024 * 1024 * 200)
        assert abs(info.vms_mb - 200.0) < 0.01

    def test_available_mb(self):
        info = MemoryInfo(available=1024 * 1024 * 500)
        assert abs(info.available_mb - 500.0) < 0.01

    def test_total_mb(self):
        info = MemoryInfo(total=1024 * 1024 * 1024 * 8)
        assert abs(info.total_mb - 8192.0) < 0.01

    def test_to_dict(self):
        info = MemoryInfo(rss=1024 * 1024, vms=1024 * 1024 * 2, percent=50.0, timestamp=datetime.now())
        d = info.to_dict()
        assert "rss_mb" in d
        assert "vms_mb" in d
        assert d["percent"] == 50.0

    def test_to_dict_no_timestamp(self):
        info = MemoryInfo()
        d = info.to_dict()
        assert d["timestamp"] is None


class TestMemoryMonitor:
    def test_init(self):
        monitor = MemoryMonitor(threshold_percent=90.0)
        assert monitor.threshold_percent == 90.0

    @patch("src.memory.psutil.Process")
    def test_get_current_memory(self, mock_process_cls):
        mock_proc = MagicMock()
        mock_mem = MagicMock()
        mock_mem.rss = 100 * 1024 * 1024
        mock_mem.vms = 200 * 1024 * 1024
        mock_proc.memory_info.return_value = mock_mem
        mock_proc.memory_percent.return_value = 5.0
        mock_process_cls.return_value = mock_proc

        monitor = MemoryMonitor()
        with patch("src.memory.psutil.virtual_memory") as mock_vm:
            mock_vm.return_value = MagicMock(available=500 * 1024 * 1024, total=1024 * 1024 * 1024 * 8)
            info = monitor.get_current_memory()
            assert isinstance(info, MemoryInfo)
            assert info.rss == 100 * 1024 * 1024

    @patch("src.memory.psutil.Process")
    def test_check_memory(self, mock_process_cls):
        mock_proc = MagicMock()
        mock_mem = MagicMock()
        mock_mem.rss = 100 * 1024 * 1024
        mock_mem.vms = 200 * 1024 * 1024
        mock_proc.memory_info.return_value = mock_mem
        mock_proc.memory_percent.return_value = 5.0
        mock_process_cls.return_value = mock_proc

        monitor = MemoryMonitor(threshold_percent=90.0)
        with patch("src.memory.psutil.virtual_memory") as mock_vm:
            mock_vm.return_value = MagicMock(available=500 * 1024 * 1024, total=1024 * 1024 * 1024 * 8)
            result = monitor.check_memory()
            assert isinstance(result, bool)


class TestMemoryLimiter:
    def test_init(self):
        limiter = MemoryLimiter(max_memory_mb=512.0)
        assert limiter.max_memory_mb == 512.0

    @patch("src.memory.psutil.Process")
    def test_check_limit(self, mock_process_cls):
        mock_proc = MagicMock()
        mock_mem = MagicMock()
        mock_mem.rss = 100 * 1024 * 1024
        mock_mem.vms = 200 * 1024 * 1024
        mock_proc.memory_info.return_value = mock_mem
        mock_proc.memory_percent.return_value = 5.0
        mock_process_cls.return_value = mock_proc

        limiter = MemoryLimiter(max_memory_mb=1024.0)
        with patch("src.memory.psutil.virtual_memory") as mock_vm:
            mock_vm.return_value = MagicMock(available=500 * 1024 * 1024, total=1024 * 1024 * 1024 * 8)
            result = limiter.check_limit()
            assert isinstance(result, bool)
