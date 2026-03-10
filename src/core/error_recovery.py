"""
错误恢复和重试机制 - 实现任务失败时的恢复和重试策略

支持指数退避、断路器、故障转移等高级恢复机制
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable, Coroutine
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import random


class RetryStrategy(str, Enum):
    """重试策略"""
    IMMEDIATE = "immediate"           # 立即重试
    LINEAR_BACKOFF = "linear_backoff"  # 线性退避
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # 指数退避
    FIBONACCI_BACKOFF = "fibonacci_backoff"  # 斐波那契退避
    RANDOM_BACKOFF = "random_backoff"  # 随机退避


class CircuitBreakerState(str, Enum):
    """断路器状态"""
    CLOSED = "closed"              # 正常状态，允许请求
    OPEN = "open"                  # 断开状态，拒绝请求
    HALF_OPEN = "half_open"        # 半开状态，允许测试请求


class ErrorType(str, Enum):
    """错误类型"""
    TRANSIENT = "transient"        # 临时错误（可重试）
    PERMANENT = "permanent"        # 永久错误（不可重试）
    TIMEOUT = "timeout"            # 超时错误
    RESOURCE_EXHAUSTED = "resource_exhausted"  # 资源耗尽
    UNKNOWN = "unknown"            # 未知错误


@dataclass
class RetryConfig:
    """重试配置"""
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    max_retries: int = 3
    initial_delay: float = 1.0      # 初始延迟（秒）
    max_delay: float = 60.0         # 最大延迟（秒）
    jitter: bool = True             # 是否添加随机抖动
    timeout: Optional[float] = None  # 单次重试超时


@dataclass
class CircuitBreakerConfig:
    """断路器配置"""
    failure_threshold: int = 5      # 失败次数阈值
    success_threshold: int = 2      # 成功次数阈值（半开状态）
    timeout: float = 60.0           # 断路器打开时长（秒）
    half_open_max_calls: int = 1    # 半开状态允许的最大调用数


@dataclass
class RetryAttempt:
    """重试尝试记录"""
    attempt_number: int
    task_id: str
    error: Optional[str] = None
    error_type: ErrorType = ErrorType.UNKNOWN
    timestamp: datetime = field(default_factory=datetime.now)
    delay_before_retry: Optional[float] = None
    success: bool = False


class RetryManager:
    """重试管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 重试历史记录
        self.retry_history: Dict[str, List[RetryAttempt]] = {}
        
        # 重试配置
        self.retry_configs: Dict[str, RetryConfig] = {}
        
        # 默认重试配置
        self.default_config = RetryConfig()
    
    async def execute_with_retry(self, task_id: str,
                                func: Callable[..., Coroutine],
                                *args, **kwargs) -> Optional[Any]:
        """
        执行函数并在失败时重试
        
        Args:
            task_id: 任务ID
            func: 要执行的异步函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Optional[Any]: 函数返回值，None表示所有重试都失败
        """
        try:
            config = self.retry_configs.get(task_id, self.default_config)
            
            if task_id not in self.retry_history:
                self.retry_history[task_id] = []
            
            for attempt_num in range(1, config.max_retries + 1):
                try:
                    self.logger.debug(f"Executing task {task_id} (attempt {attempt_num})")
                    
                    # 执行函数
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=config.timeout
                    )
                    
                    # 记录成功
                    attempt = RetryAttempt(
                        attempt_number=attempt_num,
                        task_id=task_id,
                        success=True
                    )
                    self.retry_history[task_id].append(attempt)
                    
                    self.logger.info(f"Task {task_id} succeeded on attempt {attempt_num}")
                    return result
                    
                except asyncio.TimeoutError as e:
                    error_type = ErrorType.TIMEOUT
                    error_msg = f"Timeout: {str(e)}"
                    
                except Exception as e:
                    error_type = self._classify_error(e)
                    error_msg = str(e)
                
                # 如果是永久错误，不再重试
                if error_type == ErrorType.PERMANENT:
                    self.logger.error(f"Permanent error in task {task_id}: {error_msg}")
                    attempt = RetryAttempt(
                        attempt_number=attempt_num,
                        task_id=task_id,
                        error=error_msg,
                        error_type=error_type,
                        success=False
                    )
                    self.retry_history[task_id].append(attempt)
                    return None
                
                # 记录重试尝试
                if attempt_num < config.max_retries:
                    delay = self._calculate_delay(attempt_num, config)
                    
                    attempt = RetryAttempt(
                        attempt_number=attempt_num,
                        task_id=task_id,
                        error=error_msg,
                        error_type=error_type,
                        delay_before_retry=delay,
                        success=False
                    )
                    self.retry_history[task_id].append(attempt)
                    
                    self.logger.warning(f"Task {task_id} failed (attempt {attempt_num}), "
                                      f"retrying in {delay:.2f}s: {error_msg}")
                    
                    # 等待后重试
                    await asyncio.sleep(delay)
                else:
                    # 最后一次尝试失败
                    attempt = RetryAttempt(
                        attempt_number=attempt_num,
                        task_id=task_id,
                        error=error_msg,
                        error_type=error_type,
                        success=False
                    )
                    self.retry_history[task_id].append(attempt)
                    
                    self.logger.error(f"Task {task_id} failed after {config.max_retries} attempts: {error_msg}")
                    return None
            
        except Exception as e:
            self.logger.error(f"Error in retry execution: {e}")
            return None
    
    def set_retry_config(self, task_id: str, config: RetryConfig):
        """设置任务的重试配置"""
        self.retry_configs[task_id] = config
        self.logger.debug(f"Retry config set for task {task_id}")
    
    def get_retry_history(self, task_id: str) -> List[RetryAttempt]:
        """获取任务的重试历史"""
        return self.retry_history.get(task_id, [])
    
    def _calculate_delay(self, attempt_num: int, config: RetryConfig) -> float:
        """计算重试延迟"""
        if config.strategy == RetryStrategy.IMMEDIATE:
            return 0.0
        
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.initial_delay * attempt_num
        
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.initial_delay * (2 ** (attempt_num - 1))
        
        elif config.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            # 计算斐波那契数列
            fib = [1, 1]
            for _ in range(attempt_num - 1):
                fib.append(fib[-1] + fib[-2])
            delay = config.initial_delay * fib[attempt_num - 1]
        
        elif config.strategy == RetryStrategy.RANDOM_BACKOFF:
            delay = random.uniform(config.initial_delay, config.max_delay)
        
        else:
            delay = config.initial_delay
        
        # 限制最大延迟
        delay = min(delay, config.max_delay)
        
        # 添加随机抖动
        if config.jitter:
            jitter = random.uniform(0, delay * 0.1)
            delay += jitter
        
        return delay
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """分类错误类型"""
        error_msg = str(error).lower()
        
        # 临时错误关键词
        transient_keywords = ["timeout", "connection", "temporarily", "unavailable", "try again"]
        if any(keyword in error_msg for keyword in transient_keywords):
            return ErrorType.TRANSIENT
        
        # 资源耗尽关键词
        resource_keywords = ["resource", "quota", "limit", "exhausted", "memory"]
        if any(keyword in error_msg for keyword in resource_keywords):
            return ErrorType.RESOURCE_EXHAUSTED
        
        # 永久错误关键词
        permanent_keywords = ["invalid", "not found", "unauthorized", "forbidden", "bad request"]
        if any(keyword in error_msg for keyword in permanent_keywords):
            return ErrorType.PERMANENT
        
        return ErrorType.UNKNOWN


class CircuitBreaker:
    """断路器 - 防止级联故障"""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.logger = logging.getLogger(__name__)
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # 状态
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
    
    async def call(self, func: Callable[..., Coroutine],
                  *args, **kwargs) -> Optional[Any]:
        """
        通过断路器执行函数
        
        Args:
            func: 要执行的异步函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Optional[Any]: 函数返回值
        """
        try:
            # 检查断路器状态
            if self.state == CircuitBreakerState.OPEN:
                # 检查是否应该转换到半开状态
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.half_open_calls = 0
                    self.logger.info(f"Circuit breaker {self.name} transitioned to HALF_OPEN")
                else:
                    raise Exception(f"Circuit breaker {self.name} is OPEN")
            
            # 在半开状态下限制调用数
            if self.state == CircuitBreakerState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise Exception(f"Circuit breaker {self.name} half-open call limit exceeded")
                self.half_open_calls += 1
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 成功处理
            self._on_success()
            
            return result
            
        except Exception as e:
            # 失败处理
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置断路器"""
        if self.last_failure_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.timeout
    
    def _on_success(self):
        """处理成功"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.logger.info(f"Circuit breaker {self.name} transitioned to CLOSED")
        
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0
    
    def _on_failure(self):
        """处理失败"""
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitBreakerState.CLOSED:
            self.failure_count += 1
            
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                self.logger.warning(f"Circuit breaker {self.name} transitioned to OPEN")
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.success_count = 0
            self.logger.warning(f"Circuit breaker {self.name} transitioned back to OPEN")
    
    def get_state(self) -> Dict[str, Any]:
        """获取断路器状态"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class ErrorRecoveryManager:
    """错误恢复管理器 - 综合管理重试和断路器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 重试管理器
        self.retry_manager = RetryManager()
        
        # 断路器
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # 故障转移配置
        self.failover_strategies: Dict[str, List[Callable]] = {}
    
    async def execute_with_recovery(self, task_id: str,
                                   func: Callable[..., Coroutine],
                                   circuit_breaker_name: Optional[str] = None,
                                   *args, **kwargs) -> Optional[Any]:
        """
        执行函数并应用完整的错误恢复策略
        
        Args:
            task_id: 任务ID
            func: 要执行的异步函数
            circuit_breaker_name: 断路器名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Optional[Any]: 函数返回值
        """
        try:
            # 如果指定了断路器，先通过断路器
            if circuit_breaker_name:
                if circuit_breaker_name not in self.circuit_breakers:
                    self.circuit_breakers[circuit_breaker_name] = CircuitBreaker(circuit_breaker_name)
                
                circuit_breaker = self.circuit_breakers[circuit_breaker_name]
                
                # 通过断路器执行
                async def wrapped_func():
                    return await self.retry_manager.execute_with_retry(
                        task_id, func, *args, **kwargs
                    )
                
                return await circuit_breaker.call(wrapped_func)
            else:
                # 直接执行重试
                return await self.retry_manager.execute_with_retry(
                    task_id, func, *args, **kwargs
                )
            
        except Exception as e:
            self.logger.error(f"Error recovery failed for task {task_id}: {e}")
            
            # 尝试故障转移
            if task_id in self.failover_strategies:
                return await self._attempt_failover(task_id, *args, **kwargs)
            
            return None
    
    async def _attempt_failover(self, task_id: str, *args, **kwargs) -> Optional[Any]:
        """尝试故障转移"""
        try:
            strategies = self.failover_strategies.get(task_id, [])
            
            for strategy in strategies:
                try:
                    self.logger.info(f"Attempting failover strategy for task {task_id}")
                    result = await strategy(*args, **kwargs)
                    if result is not None:
                        return result
                except Exception as e:
                    self.logger.warning(f"Failover strategy failed: {e}")
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in failover: {e}")
            return None
    
    def register_failover_strategy(self, task_id: str,
                                  strategy: Callable[..., Coroutine]):
        """注册故障转移策略"""
        if task_id not in self.failover_strategies:
            self.failover_strategies[task_id] = []
        
        self.failover_strategies[task_id].append(strategy)
        self.logger.debug(f"Failover strategy registered for task {task_id}")
    
    def get_circuit_breaker_state(self, name: str) -> Optional[Dict[str, Any]]:
        """获取断路器状态"""
        if name in self.circuit_breakers:
            return self.circuit_breakers[name].get_state()
        return None


# 全局错误恢复管理器实例
error_recovery_manager = ErrorRecoveryManager()
