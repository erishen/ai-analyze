"""Tests for retry module - RetryConfig and retry decorator"""

import pytest

from src.infrastructure.retry import RetryConfig, retry, RetryManager, RetryableException


class TestRetryConfig:
    """RetryConfig tests"""

    def test_default_values(self):
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.backoff_type == "exponential"

    def test_linear_delay(self):
        config = RetryConfig(initial_delay=1.0, backoff_type="linear", jitter=False)
        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 3.0

    def test_exponential_delay(self):
        config = RetryConfig(initial_delay=1.0, exponential_base=2.0, backoff_type="exponential", jitter=False)
        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0

    def test_fibonacci_delay(self):
        config = RetryConfig(initial_delay=1.0, backoff_type="fibonacci", jitter=False)
        # fib(n+1): fib(1)=1, fib(2)=1, fib(3)=2, fib(4)=3, fib(5)=5
        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 3.0
        assert config.get_delay(3) == 5.0

    def test_max_delay_cap(self):
        config = RetryConfig(initial_delay=100.0, max_delay=50.0, backoff_type="linear", jitter=False)
        assert config.get_delay(0) == 50.0

    def test_jitter_adds_randomness(self):
        config = RetryConfig(initial_delay=1.0, jitter=True, backoff_type="linear")
        delays = [config.get_delay(0) for _ in range(10)]
        # With jitter, delays should vary (0.5x to 1.5x)
        assert len(set(delays)) > 1

    def test_unknown_backoff_defaults_to_initial(self):
        config = RetryConfig(initial_delay=2.0, backoff_type="unknown", jitter=False)
        assert config.get_delay(0) == 2.0
        assert config.get_delay(5) == 2.0

    def test_fibonacci_static(self):
        assert RetryConfig._fibonacci(0) == 1
        assert RetryConfig._fibonacci(1) == 1
        assert RetryConfig._fibonacci(5) == 8
        assert RetryConfig._fibonacci(10) == 89


class TestRetryDecorator:
    """retry() decorator tests"""

    def test_success_no_retry(self):
        call_count = 0

        @retry(max_retries=3, delay=0.01)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count == 1

    def test_retry_then_succeed(self):
        call_count = 0

        @retry(max_retries=3, delay=0.01)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"

        result = fail_then_succeed()
        assert result == "ok"
        assert call_count == 3

    def test_retry_exhausted(self):
        @retry(max_retries=2, delay=0.01)
        def always_fail():
            raise ValueError("always fail")

        with pytest.raises(ValueError, match="always fail"):
            always_fail()

    def test_retry_specific_exceptions(self):
        call_count = 0

        @retry(max_retries=3, delay=0.01, exceptions=(ValueError,))
        def raise_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("not retried")

        with pytest.raises(TypeError):
            raise_type_error()
        assert call_count == 1  # No retry for TypeError


class TestRetryManager:
    """RetryManager tests"""

    def test_execute_success(self):
        manager = RetryManager()
        result = manager.execute_with_retry(lambda: 42)
        assert result == 42

    def test_execute_retry_then_succeed(self):
        call_count = 0

        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"

        config = RetryConfig(max_retries=3, initial_delay=0.01, jitter=False)
        manager = RetryManager(config)
        result = manager.execute_with_retry(fail_twice)
        assert result == "ok"
        assert call_count == 3

    def test_execute_retry_exhausted(self):
        def always_fail():
            raise ValueError("nope")

        config = RetryConfig(max_retries=2, initial_delay=0.01, jitter=False)
        manager = RetryManager(config)
        with pytest.raises(ValueError, match="nope"):
            manager.execute_with_retry(always_fail)


class TestRetryableException:
    def test_is_exception(self):
        e = RetryableException("retry me")
        assert isinstance(e, Exception)
        assert str(e) == "retry me"
