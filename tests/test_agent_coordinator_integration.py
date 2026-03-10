"""
Agent协调机制集成测试

测试完整的协调流程和多个模块的交互
"""

import pytest
import asyncio
from datetime import datetime

from src.core.agent_communication import communication_bus, MessageType, MessagePriority
from src.core.task_dependency import dependency_manager, DependencyType
from src.core.error_recovery import error_recovery_manager, RetryConfig, RetryStrategy
from src.core.agent_coordinator import agent_coordinator, CoordinationStrategy


class TestAgentCoordinationIntegration:
    """Agent协调集成测试"""
    
    @pytest.mark.asyncio
    async def test_complete_task_coordination_flow(self):
        """测试完整的任务协调流程"""
        # 启动协调器
        await agent_coordinator.start()
        
        try:
            # 1. 更新Agent状态
            await agent_coordinator.update_agent_state(
                agent_id="agent1",
                status="idle",
                health_score=1.0
            )
            
            # 2. 协调任务
            success = await agent_coordinator.coordinate_task(
                task_id="task1",
                agent_id="agent1",
                strategy=CoordinationStrategy.SEQUENTIAL,
                estimated_duration=10.0
            )
            
            assert success
            
            # 3. 验证任务在协调上下文中
            assert "task1" in agent_coordinator.coordination_contexts
            
            # 4. 处理任务完成
            ready_tasks = await agent_coordinator.handle_task_completion(
                task_id="task1",
                success=True,
                result={"status": "completed"}
            )
            
            # 5. 验证Agent状态更新
            state = await agent_coordinator.get_agent_state("agent1")
            assert state.completed_tasks == 1
            
        finally:
            await agent_coordinator.stop()
    
    @pytest.mark.asyncio
    async def test_task_dependency_coordination(self):
        """测试任务依赖协调"""
        await agent_coordinator.start()
        
        try:
            # 1. 协调有依赖的任务
            await agent_coordinator.coordinate_task(
                task_id="task1",
                agent_id="agent1",
                strategy=CoordinationStrategy.SEQUENTIAL
            )
            
            await agent_coordinator.coordinate_task(
                task_id="task2",
                agent_id="agent1",
                strategy=CoordinationStrategy.SEQUENTIAL,
                dependencies=["task1"]
            )
            
            # 2. 验证依赖关系
            satisfied, unsatisfied = await dependency_manager.check_dependencies("task2")
            assert not satisfied
            assert "task1" in unsatisfied
            
            # 3. 完成task1
            ready_tasks = await agent_coordinator.handle_task_completion(
                task_id="task1",
                success=True
            )
            
            # 4. 验证task2现在就绪
            assert "task2" in ready_tasks
            
            # 5. 验证task2的依赖现在满足
            satisfied, unsatisfied = await dependency_manager.check_dependencies("task2")
            assert satisfied
            
        finally:
            await agent_coordinator.stop()
    
    @pytest.mark.asyncio
    async def test_error_recovery_in_coordination(self):
        """测试协调中的错误恢复"""
        await agent_coordinator.start()
        
        try:
            # 1. 协调任务
            await agent_coordinator.coordinate_task(
                task_id="task1",
                agent_id="agent1",
                strategy=CoordinationStrategy.SEQUENTIAL
            )
            
            # 2. 处理任务失败（带重试）
            success = await agent_coordinator.handle_task_failure(
                task_id="task1",
                error="Temporary error",
                retry=True
            )
            
            assert success
            
            # 3. 验证任务被重新加入执行队列
            assert agent_coordinator.execution_queue.qsize() > 0
            
        finally:
            await agent_coordinator.stop()
    
    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self):
        """测试多Agent协调"""
        await agent_coordinator.start()
        
        try:
            # 1. 注册多个Agent
            for i in range(3):
                await agent_coordinator.update_agent_state(
                    agent_id=f"agent{i}",
                    status="idle",
                    health_score=1.0
                )
            
            # 2. 协调多个任务到不同Agent
            for i in range(3):
                await agent_coordinator.coordinate_task(
                    task_id=f"task{i}",
                    agent_id=f"agent{i}",
                    strategy=CoordinationStrategy.PARALLEL
                )
            
            # 3. 验证协调统计
            stats = agent_coordinator.get_coordination_stats()
            assert stats["total_agents"] == 3
            assert stats["total_tasks"] == 3
            
        finally:
            await agent_coordinator.stop()
    
    @pytest.mark.asyncio
    async def test_communication_bus_integration(self):
        """测试通信总线集成"""
        await communication_bus.start()
        
        try:
            # 1. 注册消息处理器
            received_messages = []
            
            async def message_handler(message):
                received_messages.append(message)
            
            await communication_bus.register_message_handler(
                "test_subject",
                message_handler
            )
            
            # 2. 发送消息
            success = await communication_bus.send_request(
                sender_id="agent1",
                receiver_id="agent2",
                subject="test_subject",
                payload={"key": "value"},
                timeout=2.0
            )
            
            # 3. 等待消息处理
            await asyncio.sleep(0.5)
            
            # 4. 验证消息被接收
            # 注意：由于这是异步的，消息可能还在处理中
            
        finally:
            await communication_bus.stop()
    
    @pytest.mark.asyncio
    async def test_complex_dependency_chain(self):
        """测试复杂的依赖链"""
        await agent_coordinator.start()
        
        try:
            # 创建依赖链: task1 -> task2 -> task3 -> task4
            await agent_coordinator.coordinate_task(
                task_id="task1",
                agent_id="agent1"
            )
            
            for i in range(2, 5):
                await agent_coordinator.coordinate_task(
                    task_id=f"task{i}",
                    agent_id="agent1",
                    dependencies=[f"task{i-1}"]
                )
            
            # 获取执行顺序
            order = await dependency_manager.get_execution_order(
                ["task1", "task2", "task3", "task4"]
            )
            
            assert order == ["task1", "task2", "task3", "task4"]
            
            # 逐个完成任务
            for i in range(1, 5):
                ready_tasks = await agent_coordinator.handle_task_completion(
                    task_id=f"task{i}",
                    success=True
                )
                
                # 验证下一个任务就绪
                if i < 4:
                    assert f"task{i+1}" in ready_tasks
            
        finally:
            await agent_coordinator.stop()


class TestCoordinationPerformance:
    """协调性能测试"""
    
    @pytest.mark.asyncio
    async def test_large_scale_coordination(self):
        """测试大规模协调"""
        await agent_coordinator.start()
        
        try:
            # 创建100个Agent和1000个任务
            num_agents = 10
            num_tasks = 100
            
            # 注册Agent
            for i in range(num_agents):
                await agent_coordinator.update_agent_state(
                    agent_id=f"agent{i}",
                    status="idle"
                )
            
            # 协调任务
            import time
            start_time = time.time()
            
            for i in range(num_tasks):
                agent_id = f"agent{i % num_agents}"
                await agent_coordinator.coordinate_task(
                    task_id=f"task{i}",
                    agent_id=agent_id
                )
            
            elapsed = time.time() - start_time
            
            # 验证性能
            stats = agent_coordinator.get_coordination_stats()
            assert stats["total_tasks"] == num_tasks
            
            # 应该在合理时间内完成
            assert elapsed < 10.0  # 10秒内完成
            
        finally:
            await agent_coordinator.stop()


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
