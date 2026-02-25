"""
进度条和性能监控
用于显示分析进度和性能指标
"""

import time
import sys
from typing import Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import logging


@dataclass
class ProgressMetrics:
    """进度指标"""
    
    total: int = 0
    current: int = 0
    start_time: float = 0.0
    end_time: Optional[float] = None
    
    @property
    def elapsed(self) -> float:
        """已用时间（秒）"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    @property
    def percentage(self) -> float:
        """完成百分比"""
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100
    
    @property
    def eta(self) -> float:
        """预计剩余时间（秒）"""
        if self.current == 0:
            return 0.0
        rate = self.current / self.elapsed
        remaining = self.total - self.current
        return remaining / rate if rate > 0 else 0.0
    
    @property
    def rate(self) -> float:
        """处理速率（项/秒）"""
        if self.elapsed == 0:
            return 0.0
        return self.current / self.elapsed


class ProgressBar:
    """进度条"""
    
    def __init__(
        self,
        total: int,
        title: str = "Progress",
        width: int = 50,
        show_percentage: bool = True,
        show_eta: bool = True,
        show_rate: bool = True
    ):
        """初始化进度条
        
        Args:
            total: 总项数
            title: 进度条标题
            width: 进度条宽度
            show_percentage: 是否显示百分比
            show_eta: 是否显示预计剩余时间
            show_rate: 是否显示处理速率
        """
        self.metrics = ProgressMetrics(total=total, start_time=time.time())
        self.title = title
        self.width = width
        self.show_percentage = show_percentage
        self.show_eta = show_eta
        self.show_rate = show_rate
        self.logger = logging.getLogger("ai-analyze.progress")
    
    def update(self, current: int):
        """更新进度
        
        Args:
            current: 当前项数
        """
        self.metrics.current = current
        self._display()
    
    def increment(self, amount: int = 1):
        """增加进度
        
        Args:
            amount: 增加的项数
        """
        self.metrics.current += amount
        self._display()
    
    def finish(self):
        """完成进度条"""
        self.metrics.current = self.metrics.total
        self.metrics.end_time = time.time()
        self._display()
        print()  # 换行
    
    def _display(self):
        """显示进度条"""
        percentage = self.metrics.percentage
        filled = int(self.width * percentage / 100)
        bar = "█" * filled + "░" * (self.width - filled)
        
        # 构建进度条字符串
        progress_str = f"\r{self.title}: |{bar}|"
        
        # 添加百分比
        if self.show_percentage:
            progress_str += f" {percentage:.1f}%"
        
        # 添加进度
        progress_str += f" ({self.metrics.current}/{self.metrics.total})"
        
        # 添加已用时间
        elapsed = self.metrics.elapsed
        progress_str += f" [{self._format_time(elapsed)}"
        
        # 添加预计剩余时间
        if self.show_eta and self.metrics.current > 0:
            eta = self.metrics.eta
            progress_str += f"<{self._format_time(eta)}"
        
        progress_str += "]"
        
        # 添加处理速率
        if self.show_rate and self.metrics.current > 0:
            rate = self.metrics.rate
            progress_str += f" {rate:.1f}项/s"
        
        # 输出进度条
        sys.stdout.write(progress_str)
        sys.stdout.flush()
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """格式化时间
        
        Args:
            seconds: 秒数
        
        Returns:
            格式化的时间字符串
        """
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"


class PerformanceMonitor:
    """性能监控"""
    
    def __init__(self, name: str = "Task"):
        """初始化性能监控
        
        Args:
            name: 任务名称
        """
        self.name = name
        self.logger = logging.getLogger("ai-analyze.performance")
        self.start_time = None
        self.end_time = None
        self.metrics = {}
    
    def start(self):
        """开始监控"""
        self.start_time = time.time()
        self.logger.debug(f"开始: {self.name}")
    
    def stop(self):
        """停止监控"""
        self.end_time = time.time()
        elapsed = self.end_time - self.start_time
        self.logger.info(f"完成: {self.name} (耗时: {elapsed:.2f}s)")
        return elapsed
    
    def add_metric(self, name: str, value: Any):
        """添加指标
        
        Args:
            name: 指标名称
            value: 指标值
        """
        self.metrics[name] = value
    
    def get_metrics(self) -> dict:
        """获取所有指标"""
        metrics = {
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed": self.end_time - self.start_time if self.end_time else None,
            **self.metrics
        }
        return metrics
    
    def print_metrics(self):
        """打印指标"""
        print(f"\n{'='*60}")
        print(f"性能指标: {self.name}")
        print(f"{'='*60}")
        
        metrics = self.get_metrics()
        for key, value in metrics.items():
            if key == "elapsed" and value:
                print(f"  {key}: {value:.2f}s")
            elif isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
        print(f"{'='*60}\n")


class ContextProgressBar:
    """上下文管理器进度条"""
    
    def __init__(
        self,
        total: int,
        title: str = "Progress",
        width: int = 50
    ):
        """初始化上下文进度条
        
        Args:
            total: 总项数
            title: 进度条标题
            width: 进度条宽度
        """
        self.progress_bar = ProgressBar(total, title, width)
    
    def __enter__(self):
        """进入上下文"""
        return self.progress_bar
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        self.progress_bar.finish()


class ContextPerformanceMonitor:
    """上下文管理器性能监控"""
    
    def __init__(self, name: str = "Task"):
        """初始化上下文性能监控
        
        Args:
            name: 任务名称
        """
        self.monitor = PerformanceMonitor(name)
    
    def __enter__(self):
        """进入上下文"""
        self.monitor.start()
        return self.monitor
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        self.monitor.stop()
        if exc_type is None:
            self.monitor.print_metrics()


def progress_bar(
    total: int,
    title: str = "Progress",
    width: int = 50
) -> ContextProgressBar:
    """创建进度条上下文管理器
    
    Args:
        total: 总项数
        title: 进度条标题
        width: 进度条宽度
    
    Returns:
        ContextProgressBar: 进度条上下文管理器
    
    Example:
        with progress_bar(100, "Processing") as pbar:
            for i in range(100):
                # 处理项
                pbar.increment()
    """
    return ContextProgressBar(total, title, width)


def performance_monitor(name: str = "Task") -> ContextPerformanceMonitor:
    """创建性能监控上下文管理器
    
    Args:
        name: 任务名称
    
    Returns:
        ContextPerformanceMonitor: 性能监控上下文管理器
    
    Example:
        with performance_monitor("Analysis") as monitor:
            # 执行分析
            monitor.add_metric("files_analyzed", 100)
    """
    return ContextPerformanceMonitor(name)


if __name__ == "__main__":
    # 测试进度条
    print("测试进度条:")
    with progress_bar(100, "Processing") as pbar:
        for i in range(100):
            time.sleep(0.01)
            pbar.increment()
    
    # 测试性能监控
    print("\n测试性能监控:")
    with performance_monitor("Analysis") as monitor:
        time.sleep(1)
        monitor.add_metric("files_analyzed", 100)
        monitor.add_metric("issues_found", 5)
