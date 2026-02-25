"""
重试机制
用于处理 API 调用、网络请求等可能失败的操作
"""

import time
import logging
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
import random

from .exceptions import (
    APIException,
    APITimeoutException,
    APIRateLimitException,
    TimeoutException
)


class RetryConfig:
    """重试配置"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        backoff_type: str = "exponential"  # linear, exponential, fibonacci
    ):
        """初始化重试配置
        
        Args:
            max_retries: 最大重试次数
            initial_delay: 初始延迟（秒）
            max_delay: 最大延迟（秒）
            exponential_base: 指数基数
            jitter: 是否添加随机抖动
            backoff_type: 退避类型
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.backoff_type = backoff_type
    
    def get_delay(self, attempt: int) -> float:
        """获取延迟时间
        
        Args:
            attempt: 尝试次数（从 0 开始）
        
        Returns:
            延迟时间（秒）
        """
        if self.backoff_type == "linear":
            delay = self.initial_delay * (attempt + 1)
        elif self.backoff_type == "exponential":
            delay = self.initial_delay * (self.exponential_base ** attempt)
        elif self.backoff_type == "fibonacci":
            delay = self.initial_delay * self._fibonacci(attempt + 1)
        else:
            delay = self.initial_delay
        
        # 限制最大延迟
        delay = min(delay, self.max_delay)
        
        # 添加随机抖动
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay
    
    @staticmethod
    def _fibonacci(n: int) -> int:
        """计算斐波那契数列"""
        if n <= 1:
            return 1
        a, b = 1, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b


class RetryableException(Exception):
    """可重试的异常"""
    pass


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_type: str = "exponential",
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None,
    logger: Optional[logging.Logger] = None
):
    """重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff_type: 退避类型
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数
        logger: 日志记录器
    
    Example:
        @retry(max_retries=3, delay=1.0)
        def api_call():
            return requests.get("https://api.example.com")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            config = RetryConfig(
                max_retries=max_retries,
                initial_delay=delay,
                backoff_type=backoff_type
            )
            
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        wait_time = config.get_delay(attempt)
                        
                        if logger:
                            logger.warning(
                                f"函数 {func.__name__} 执行失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}. "
                                f"将在 {wait_time:.1f} 秒后重试..."
                            )
                        
                        if on_retry:
                            on_retry(attempt, e, wait_time)
                        
                        time.sleep(wait_time)
                    else:
                        if logger:
                            logger.error(
                                f"函数 {func.__name__} 执行失败，已达到最大重试次数 ({max_retries + 1}): {e}"
                            )
            
            raise last_exception
        
        return wrapper
    
    return decorator


class RetryManager:
    """重试管理器"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """初始化重试管理器
        
        Args:
            config: 重试配置
        """
        self.config = config or RetryConfig()
        self.logger = logging.getLogger("ai-analyze.retry")
    
    def execute_with_retry(
        self,
        func: Callable,
        *args,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """执行函数并进行重试
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            exceptions: 需要重试的异常类型
            on_retry: 重试时的回调函数
            **kwargs: 函数关键字参数
        
        Returns:
            函数返回值
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                
                if attempt < self.config.max_retries:
                    wait_time = self.config.get_delay(attempt)
                    
                    self.logger.warning(
                        f"执行失败 (尝试 {attempt + 1}/{self.config.max_retries + 1}): {e}. "
                        f"将在 {wait_time:.1f} 秒后重试..."
                    )
                    
                    if on_retry:
                        on_retry(attempt, e, wait_time)
                    
                    time.sleep(wait_time)
                else:
                    self.logger.error(
                        f"执行失败，已达到最大重试次数 ({self.config.max_retries + 1}): {e}"
                    )
        
        raise last_exception


# 特定的重试策略
class APIRetryManager(RetryManager):
    """API 重试管理器"""
    
    def __init__(self):
        """初始化 API 重试管理器"""
        config = RetryConfig(
            max_retries=3,
            initial_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True,
            backoff_type="exponential"
        )
        super().__init__(config)
    
    def execute_api_call(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """执行 API 调用并进行重试
        
        Args:
            func: API 调用函数
            *args: 函数参数
            **kwargs: 函数关键字参数
        
        Returns:
            API 响应
        """
        def on_retry(attempt, exc, wait_time):
            if isinstance(exc, APIRateLimitException):
                self.logger.warning(f"API 速率限制，等待 {wait_time:.1f} 秒...")
            elif isinstance(exc, APITimeoutException):
                self.logger.warning(f"API 超时，等待 {wait_time:.1f} 秒...")
        
        return self.execute_with_retry(
            func,
            *args,
            exceptions=(APIException, TimeoutException),
            on_retry=on_retry,
            **kwargs
        )


if __name__ == "__main__":
    # 测试重试机制
    logger = logging.getLogger("test")
    logging.basicConfig(level=logging.DEBUG)
    
    attempt_count = 0
    
    @retry(max_retries=3, delay=0.5, logger=logger)
    def failing_function():
        global attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError(f"尝试 {attempt_count} 失败")
        return "成功"
    
    result = failing_function()
    print(f"结果: {result}")
