"""
内存监控和优化
用于监控内存使用情况和优化内存占用
"""

import os
import psutil
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MemoryInfo:
    """内存信息"""
    
    rss: int = 0  # 常驻集大小（字节）
    vms: int = 0  # 虚拟内存大小（字节）
    percent: float = 0.0  # 内存占用百分比
    available: int = 0  # 可用内存（字节）
    total: int = 0  # 总内存（字节）
    timestamp: Optional[datetime] = None
    
    @property
    def rss_mb(self) -> float:
        """RSS 内存（MB）"""
        return self.rss / (1024 * 1024)
    
    @property
    def vms_mb(self) -> float:
        """VMS 内存（MB）"""
        return self.vms / (1024 * 1024)
    
    @property
    def available_mb(self) -> float:
        """可用内存（MB）"""
        return self.available / (1024 * 1024)
    
    @property
    def total_mb(self) -> float:
        """总内存（MB）"""
        return self.total / (1024 * 1024)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rss_mb": self.rss_mb,
            "vms_mb": self.vms_mb,
            "percent": self.percent,
            "available_mb": self.available_mb,
            "total_mb": self.total_mb,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class MemoryMonitor:
    """内存监控"""
    
    def __init__(self, threshold_percent: float = 80.0):
        """初始化内存监控
        
        Args:
            threshold_percent: 内存使用百分比阈值
        """
        self.threshold_percent = threshold_percent
        self.logger = logging.getLogger("ai-analyze.memory")
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self._get_memory_info()
        self.peak_memory = self.initial_memory
    
    def _get_memory_info(self) -> MemoryInfo:
        """获取内存信息"""
        try:
            proc_info = self.process.memory_info()
            mem_info = psutil.virtual_memory()
            
            return MemoryInfo(
                rss=proc_info.rss,
                vms=proc_info.vms,
                percent=self.process.memory_percent(),
                available=mem_info.available,
                total=mem_info.total,
                timestamp=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"获取内存信息失败: {e}")
            return MemoryInfo()
    
    def get_current_memory(self) -> MemoryInfo:
        """获取当前内存使用情况"""
        memory = self._get_memory_info()
        
        # 更新峰值内存
        if memory.rss > self.peak_memory.rss:
            self.peak_memory = memory
        
        return memory
    
    def check_memory(self) -> bool:
        """检查内存使用情况
        
        Returns:
            bool: 内存使用是否超过阈值
        """
        memory = self.get_current_memory()
        
        if memory.percent > self.threshold_percent:
            self.logger.warning(
                f"内存使用过高: {memory.percent:.1f}% "
                f"(RSS: {memory.rss_mb:.1f}MB, VMS: {memory.vms_mb:.1f}MB)"
            )
            return False
        
        return True
    
    def get_memory_delta(self) -> MemoryInfo:
        """获取内存变化量"""
        current = self.get_current_memory()
        
        return MemoryInfo(
            rss=current.rss - self.initial_memory.rss,
            vms=current.vms - self.initial_memory.vms,
            percent=current.percent - self.initial_memory.percent,
            available=current.available,
            total=current.total,
            timestamp=current.timestamp
        )
    
    def print_memory_info(self):
        """打印内存信息"""
        current = self.get_current_memory()
        delta = self.get_memory_delta()
        
        print("\n" + "="*60)
        print("内存使用情况")
        print("="*60)
        print(f"当前内存:")
        print(f"  RSS: {current.rss_mb:.1f}MB")
        print(f"  VMS: {current.vms_mb:.1f}MB")
        print(f"  占用: {current.percent:.1f}%")
        print(f"\n内存变化:")
        print(f"  RSS: {delta.rss_mb:+.1f}MB")
        print(f"  VMS: {delta.vms_mb:+.1f}MB")
        print(f"  占用: {delta.percent:+.1f}%")
        print(f"\n峰值内存:")
        print(f"  RSS: {self.peak_memory.rss_mb:.1f}MB")
        print(f"  VMS: {self.peak_memory.vms_mb:.1f}MB")
        print(f"\n系统内存:")
        print(f"  可用: {current.available_mb:.1f}MB")
        print(f"  总计: {current.total_mb:.1f}MB")
        print("="*60 + "\n")


class MemoryLimiter:
    """内存限制器"""
    
    def __init__(self, max_memory_mb: float = 1024.0):
        """初始化内存限制器
        
        Args:
            max_memory_mb: 最大内存限制（MB）
        """
        self.max_memory_mb = max_memory_mb
        self.logger = logging.getLogger("ai-analyze.memory")
        self.monitor = MemoryMonitor()
    
    def check_limit(self) -> bool:
        """检查是否超过内存限制
        
        Returns:
            bool: 是否超过限制
        """
        current = self.monitor.get_current_memory()
        
        if current.rss_mb > self.max_memory_mb:
            self.logger.error(
                f"内存超过限制: {current.rss_mb:.1f}MB > {self.max_memory_mb:.1f}MB"
            )
            return False
        
        return True
    
    def get_remaining_memory(self) -> float:
        """获取剩余内存（MB）"""
        current = self.monitor.get_current_memory()
        return self.max_memory_mb - current.rss_mb


class MemoryProfiler:
    """内存分析器"""
    
    def __init__(self):
        """初始化内存分析器"""
        self.logger = logging.getLogger("ai-analyze.memory")
        self.snapshots = []
    
    def take_snapshot(self, label: str = ""):
        """获取内存快照
        
        Args:
            label: 快照标签
        """
        monitor = MemoryMonitor()
        memory = monitor.get_current_memory()
        
        snapshot = {
            "label": label,
            "timestamp": memory.timestamp,
            "rss_mb": memory.rss_mb,
            "vms_mb": memory.vms_mb,
            "percent": memory.percent
        }
        
        self.snapshots.append(snapshot)
        self.logger.debug(f"内存快照 [{label}]: RSS={memory.rss_mb:.1f}MB")
    
    def print_profile(self):
        """打印内存分析结果"""
        if not self.snapshots:
            print("没有内存快照")
            return
        
        print("\n" + "="*60)
        print("内存分析结果")
        print("="*60)
        
        for i, snapshot in enumerate(self.snapshots):
            print(f"\n快照 {i+1}: {snapshot['label']}")
            print(f"  时间: {snapshot['timestamp']}")
            print(f"  RSS: {snapshot['rss_mb']:.1f}MB")
            print(f"  VMS: {snapshot['vms_mb']:.1f}MB")
            print(f"  占用: {snapshot['percent']:.1f}%")
            
            if i > 0:
                prev = self.snapshots[i-1]
                rss_delta = snapshot['rss_mb'] - prev['rss_mb']
                print(f"  变化: {rss_delta:+.1f}MB")
        
        print("\n" + "="*60 + "\n")


def get_memory_info() -> MemoryInfo:
    """获取当前内存信息"""
    monitor = MemoryMonitor()
    return monitor.get_current_memory()


def print_memory_info():
    """打印内存信息"""
    monitor = MemoryMonitor()
    monitor.print_memory_info()


if __name__ == "__main__":
    # 测试内存监控
    print("测试内存监控:")
    monitor = MemoryMonitor()
    
    # 获取初始内存
    initial = monitor.get_current_memory()
    print(f"初始内存: {initial.rss_mb:.1f}MB")
    
    # 分配一些内存
    data = [i for i in range(1000000)]
    
    # 获取当前内存
    current = monitor.get_current_memory()
    print(f"当前内存: {current.rss_mb:.1f}MB")
    
    # 打印内存信息
    monitor.print_memory_info()
    
    # 测试内存分析器
    print("\n测试内存分析器:")
    profiler = MemoryProfiler()
    profiler.take_snapshot("初始")
    
    data2 = [i for i in range(1000000)]
    profiler.take_snapshot("分配后")
    
    del data2
    profiler.take_snapshot("删除后")
    
    profiler.print_profile()
