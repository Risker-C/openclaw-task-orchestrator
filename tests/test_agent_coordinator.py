"""
Agent协调机制单元测试

测试通信协议、依赖管理、错误恢复等功能
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.core.agent_communication import (
    Message, MessageType, MessagePriority, MessageQueue, AgentCommunicationBus
)
from src.core.task_dependency import (
    DependencyType, DependencyCondition, TaskDependency, DependencyManager
)
from src.core.error_recovery import (
    RetryStrategy, RetryConfig, CircuitBreakerState, RetryManager, CircuitBreaker, ErrorRecoveryManager
)
from src.core.agent_coordinator import (
    CoordinationStrategy, AgentCoordinator, AgentState
)


class TestAgentCommunication:
    """测试Agent通信"""
    
    @pytest.mark.asyncio
    async def test_message_creation(self):
        """测试消息创建"""
        message = Message(
            message_type=MessageType.REQUEST,
            sender_id="agent1",
            receiver_id="agent2",
            subject="test",
            payload={"key": "value"}
        )
        
        assert message.message_type == MessageType.REQUEST
        assert message.sender_id == "agent1"
        assert message.receiver_id == "agent2"
        assert not message.is_expired()
    
    @pytest.mark.asyncio
    async def test_message_expiration(self):
        """测试消息过期"""
        message = Message(
            message_type=MessageType.REQUEST,
            sender_id="agent1",
            receiver_id="agent2",
            expires_at=datetime.now() - timedelta(seconds=1)
        )
        
        assert message.is_expired()
    
    @pytest.mark.asyncio
    async def test_message_queue_send_receive(self):
        """测试消息队列发送和接收"""
        queue = MessageQueue()
        
        message = Message(
            message_type=MessageType.REQUEST,
            sender_id="agent1",
            receiver_id="agent2",
            subject="test"
        )
        
        # 发送消息
        success = await queue.send_message(message)
        assert success
        
        # 接收消息
        received = await asyncio.wait_for(queue.receive_message(timeout=1.0), timeout=2.0)
        assert received is not None
        assert received.message_id == message.message_id
    
    @pytest.mark.asyncio
    async def test_message_priority(self):
        """测试消息优先级"""
        queue = MessageQueue()
        
        # 发送低优先级消息
        low_msg = Message(
            message_type=MessageType.REQUEST,
            sender_id="agent1",
            receiver_id="agent2",
            priority=MessagePriority.LOW
        )
        await queue.send_message(low_msg)
        
        # 发送高优先级消息
        high_msg = Message(
            message_type=MessageType.REQUEST,
            sender_id="agent1",
            receiver_id="agent2",
            priority=MessagePriority.HIGH
        )
        await queue.send_message(high_msg)
        
        # 应该先收到高优先级消息
        received1 = await asyncio.wait_for(queue.receive_message(timeout=1.0), timeout=2.0)
        assert received1.priority == MessagePriority.HIGH


class TestTaskDependency:
    """测试任务依赖管理"""
    
    @pytest.mark.asyncio
    async def test_add_dependency(self):
        """测试添加依赖"""
        manager = DependencyManager()
        
        success = await manager.add_dependency(
            task_id="task2",
            depends_on="task1",
            dependency_type=DependencyType.SEQUENTIAL
        )
        
        assert success
        assert "task2" in manager.dependency_graphs
        assert len(manager.dependency_graphs["task2"].dependencies) == 1
    
    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self):
        """测试循环依赖检测"""
        manager = DependencyManager()
        
        # 添加依赖: task1 -> task2
        await manager.add_dependency("task2", "task1")
        
        # 尝试添加循环依赖: task1 -> task2 -> task1
        success = await manager.add_dependency("task1", "task2")
        
        assert not success  # 应该失败
    
    @pytest.mark.asyncio
    async def test_check_dependencies(self):
        """测试检查依赖"""
        manager = DependencyManager()
        
        # 添加依赖
        await manager.add_dependency("task2", "task1")
        
        # 检查依赖（task1未完成）
        satisfied, unsatisfied = await manager.check_dependencies("task2")
        assert not satisfied
        assert "task1" in unsatisfied
        
        # 标记task1完成
        await manager.mark_task_completed("task1", success=True)
        
        # 再次检查依赖
        satisfied, unsatisfied = await manager.check_dependencies("task2")
        assert satisfied
        assert len(unsatisfied) == 0
    
    @pytest.mark.asyncio
    async def test_execution_order(self):
        """测试执行顺序"""
        manager = DependencyManager()
        
        # 创建依赖链: task1 -> task2 -> task3
        await manager.add_dependency("task2", "task1")
        await manager.add_dependency("task3", "task2")
        
        # 获取执行顺序
        order = await manager.get_execution_order(["task1", "task2", "task3"])
        
        assert order == ["task1", "task2", "task3"]


class TestErrorRecovery:
    """测试错误恢复"""
    
    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self):
        """测试指数退避重试"""
        manager = RetryManager()
        
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            max_retries=3,
            initial_delay=0.1,
            max_delay=1.0,
            jitter=False
        )
        manager.set_retry_config("task1", config)
        
        attempt_count = 0
        
        async def failing_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Temporary error")
            return "success"
        
        result = await manager.execute_with_retry("task1", failing_func)
        
        assert result == "success"
        assert attempt_count == 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_state_transitions(self):
        """测试断路器状态转换"""
        config = CircuitBreakerConfig = type('CircuitBreakerConfig', (), {
            'failure_threshold': 2,
            'success_threshold': 1,
            'timeout': 1.0,
            'half_open_max_calls': 1
        })()
        
        breaker = CircuitBreaker("test", config)
        
        # 初始状态应该是CLOSED
        assert breaker.state == CircuitBreakerState.CLOSED
        
        # 模拟失败
        async def failing_func():
            raise Exception("Error")
        
        # 第一次失败
        try:
            await breaker.call(failing_func)
        except:
            pass
        
        assert breaker.state == CircuitBreakerState.CLOSED
        
        # 第二次失败，应该转换到OPEN
        try:
            await breaker.call(failing_func)
        except:
            pass
        
        assert breaker.state == CircuitBreakerState.OPEN


class TestAgentCoordinator:
    """测试Agent协调器"""
    
    @pytest.mark.asyncio
    async def test_agent_state_update(self):
        """测试Agent状态更新"""
        coordinator = AgentCoordinator()
        
        success = await coordinator.update_agent_state(
            agent_id="agent1",
            status="idle",
            health_score=0.95
        )
        
        assert success
        
        state = await coordinator.get_agent_state("agent1")
        assert state is not None
        assert state.status == "idle"
        assert state.health_score == 0.95
    
    @pytest.mark.asyncio
    async def test_coordination_stats(self):
        """测试协调统计"""
        coordinator = AgentCoordinator()
        
        # 添加Agent状态
        await coordinator.update_agent_state("agent1", "idle")
        await coordinator.update_agent_state("agent2", "busy")
        
        stats = coordinator.get_coordination_stats()
        
        assert stats["total_agents"] == 2
        assert "average_health_score" in stats


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
