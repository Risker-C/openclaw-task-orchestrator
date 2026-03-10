"""
Agent协调器 - 实现Agent间的协调和状态同步

整合通信协议、依赖管理、错误恢复等机制
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from .agent_communication import (
    communication_bus, Message, MessageType, MessagePriority
)
from .task_dependency import (
    dependency_manager, DependencyType, DependencyCondition
)
from .error_recovery import error_recovery_manager, RetryConfig, RetryStrategy


class CoordinationStrategy(str, Enum):
    """协调策略"""
    SEQUENTIAL = "sequential"      # 顺序执行
    PARALLEL = "parallel"          # 并行执行
    HIERARCHICAL = "hierarchical"  # 分层执行
    ADAPTIVE = "adaptive"          # 自适应执行


@dataclass
class AgentState:
    """Agent状态快照"""
    agent_id: str
    status: str                    # idle, busy, error, offline
    current_tasks: Set[str] = field(default_factory=set)
    completed_tasks: int = 0
    failed_tasks: int = 0
    health_score: float = 1.0
    last_update: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinationContext:
    """协调上下文"""
    task_id: str
    agent_id: str
    strategy: CoordinationStrategy
    dependencies: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    estimated_duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentCoordinator:
    """Agent协调器 - 核心协调逻辑"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Agent状态缓存
        self.agent_states: Dict[str, AgentState] = {}
        
        # 协调上下文
        self.coordination_contexts: Dict[str, CoordinationContext] = {}
        
        # 任务执行队列
        self.execution_queue: asyncio.Queue = asyncio.Queue()
        
        # 状态同步间隔
        self.state_sync_interval = 5.0  # 秒
        
        # 运行状态
        self._running = False
        self._state_sync_task: Optional[asyncio.Task] = None
        self._execution_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动协调器"""
        if self._running:
            return
        
        self.logger.info("Starting Agent Coordinator...")
        self._running = True
        
        # 启动通信总线
        await communication_bus.start()
        
        # 启动状态同步任务
        self._state_sync_task = asyncio.create_task(self._state_sync_loop())
        
        # 启动执行任务
        self._execution_task = asyncio.create_task(self._execution_loop())
        
        # 注册消息处理器
        await self._register_message_handlers()
        
        self.logger.info("Agent Coordinator started successfully")
    
    async def stop(self):
        """停止协调器"""
        if not self._running:
            return
        
        self.logger.info("Stopping Agent Coordinator...")
        self._running = False
        
        # 停止任务
        if self._state_sync_task:
            self._state_sync_task.cancel()
            try:
                await self._state_sync_task
            except asyncio.CancelledError:
                pass
        
        if self._execution_task:
            self._execution_task.cancel()
            try:
                await self._execution_task
            except asyncio.CancelledError:
                pass
        
        # 停止通信总线
        await communication_bus.stop()
        
        self.logger.info("Agent Coordinator stopped")
    
    async def coordinate_task(self, task_id: str, agent_id: str,
                             strategy: CoordinationStrategy = CoordinationStrategy.SEQUENTIAL,
                             dependencies: Optional[List[str]] = None,
                             estimated_duration: Optional[float] = None) -> bool:
        """
        协调任务执行
        
        Args:
            task_id: 任务ID
            agent_id: Agent ID
            strategy: 协调策略
            dependencies: 依赖的任务列表
            estimated_duration: 预计执行时间
            
        Returns:
            bool: 协调是否成功
        """
        try:
            # 创建协调上下文
            context = CoordinationContext(
                task_id=task_id,
                agent_id=agent_id,
                strategy=strategy,
                dependencies=dependencies or [],
                estimated_duration=estimated_duration
            )
            
            self.coordination_contexts[task_id] = context
            
            # 添加依赖关系
            for dep_task_id in (dependencies or []):
                await dependency_manager.add_dependency(
                    task_id=task_id,
                    depends_on=dep_task_id,
                    dependency_type=DependencyType.SEQUENTIAL
                )
            
            # 检查依赖
            all_satisfied, unsatisfied = await dependency_manager.check_dependencies(task_id)
            
            if all_satisfied:
                # 依赖满足，加入执行队列
                await self.execution_queue.put(context)
                self.logger.info(f"Task {task_id} added to execution queue")
            else:
                # 依赖未满足，等待
                self.logger.info(f"Task {task_id} waiting for dependencies: {unsatisfied}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error coordinating task: {e}")
            return False
    
    async def update_agent_state(self, agent_id: str, status: str,
                                current_tasks: Optional[Set[str]] = None,
                                health_score: Optional[float] = None,
                                metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        更新Agent状态
        
        Args:
            agent_id: Agent ID
            status: 状态
            current_tasks: 当前任务集合
            health_score: 健康分数
            metadata: 元数据
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if agent_id not in self.agent_states:
                self.agent_states[agent_id] = AgentState(agent_id=agent_id, status=status)
            
            state = self.agent_states[agent_id]
            state.status = status
            state.last_update = datetime.now()
            
            if current_tasks is not None:
                state.current_tasks = current_tasks
            
            if health_score is not None:
                state.health_score = max(0.0, min(1.0, health_score))
            
            if metadata is not None:
                state.metadata.update(metadata)
            
            # 发布状态更新事件
            await communication_bus.publish_event(
                sender_id="coordinator",
                event_type="agent_state_updated",
                payload={
                    "agent_id": agent_id,
                    "status": status,
                    "health_score": state.health_score,
                    "current_tasks": list(state.current_tasks)
                },
                priority=MessagePriority.HIGH
            )
            
            self.logger.debug(f"Agent {agent_id} state updated: {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating agent state: {e}")
            return False
    
    async def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """获取Agent状态"""
        return self.agent_states.get(agent_id)
    
    async def sync_agent_states(self) -> Dict[str, AgentState]:
        """同步所有Agent的状态"""
        try:
            # 发送状态同步请求
            response = await communication_bus.send_request(
                sender_id="coordinator",
                receiver_id="*",
                subject="sync_state",
                payload={},
                priority=MessagePriority.HIGH,
                timeout=5.0
            )
            
            if response:
                self.logger.debug("Agent states synchronized")
            
            return self.agent_states
            
        except Exception as e:
            self.logger.error(f"Error syncing agent states: {e}")
            return self.agent_states
    
    async def handle_task_completion(self, task_id: str, success: bool = True,
                                    result: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        处理任务完成
        
        Args:
            task_id: 任务ID
            success: 是否成功
            result: 任务结果
            
        Returns:
            List[str]: 现在可以执行的任务列表
        """
        try:
            # 标记任务完成
            ready_tasks = await dependency_manager.mark_task_completed(
                task_id=task_id,
                success=success,
                result=result
            )
            
            # 更新Agent状态
            if task_id in self.coordination_contexts:
                context = self.coordination_contexts[task_id]
                agent_id = context.agent_id
                
                if agent_id in self.agent_states:
                    state = self.agent_states[agent_id]
                    state.current_tasks.discard(task_id)
                    
                    if success:
                        state.completed_tasks += 1
                    else:
                        state.failed_tasks += 1
            
            # 将就绪的任务加入执行队列
            for ready_task_id in ready_tasks:
                if ready_task_id in self.coordination_contexts:
                    context = self.coordination_contexts[ready_task_id]
                    await self.execution_queue.put(context)
                    self.logger.info(f"Task {ready_task_id} is now ready for execution")
            
            # 发布任务完成事件
            await communication_bus.publish_event(
                sender_id="coordinator",
                event_type="task_completed",
                payload={
                    "task_id": task_id,
                    "success": success,
                    "result": result,
                    "ready_tasks": ready_tasks
                },
                priority=MessagePriority.HIGH
            )
            
            return ready_tasks
            
        except Exception as e:
            self.logger.error(f"Error handling task completion: {e}")
            return []
    
    async def handle_task_failure(self, task_id: str, error: str,
                                 retry: bool = True) -> bool:
        """
        处理任务失败
        
        Args:
            task_id: 任务ID
            error: 错误信息
            retry: 是否重试
            
        Returns:
            bool: 是否成功处理
        """
        try:
            self.logger.warning(f"Task {task_id} failed: {error}")
            
            if retry and task_id in self.coordination_contexts:
                context = self.coordination_contexts[task_id]
                
                # 设置重试配置
                retry_config = RetryConfig(
                    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                    max_retries=3,
                    initial_delay=1.0
                )
                error_recovery_manager.retry_manager.set_retry_config(task_id, retry_config)
                
                # 重新加入执行队列
                await self.execution_queue.put(context)
                self.logger.info(f"Task {task_id} will be retried")
            else:
                # 标记任务失败
                await self.handle_task_completion(task_id, success=False)
            
            # 发布任务失败事件
            await communication_bus.publish_event(
                sender_id="coordinator",
                event_type="task_failed",
                payload={
                    "task_id": task_id,
                    "error": error,
                    "retry": retry
                },
                priority=MessagePriority.HIGH
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling task failure: {e}")
            return False
    
    async def _register_message_handlers(self):
        """注册消息处理器"""
        try:
            # 注册状态更新处理器
            async def handle_state_update(message: Message):
                agent_id = message.payload.get("agent_id")
                status = message.payload.get("status")
                health_score = message.payload.get("health_score")
                
                await self.update_agent_state(
                    agent_id=agent_id,
                    status=status,
                    health_score=health_score
                )
            
            await communication_bus.register_message_handler(
                "agent_state_update",
                handle_state_update
            )
            
            # 注册任务完成处理器
            async def handle_task_complete(message: Message):
                task_id = message.payload.get("task_id")
                success = message.payload.get("success", True)
                result = message.payload.get("result")
                
                await self.handle_task_completion(task_id, success, result)
            
            await communication_bus.register_message_handler(
                "task_complete",
                handle_task_complete
            )
            
            # 注册任务失败处理器
            async def handle_task_fail(message: Message):
                task_id = message.payload.get("task_id")
                error = message.payload.get("error")
                retry = message.payload.get("retry", True)
                
                await self.handle_task_failure(task_id, error, retry)
            
            await communication_bus.register_message_handler(
                "task_fail",
                handle_task_fail
            )
            
            self.logger.info("Message handlers registered")
            
        except Exception as e:
            self.logger.error(f"Error registering message handlers: {e}")
    
    async def _state_sync_loop(self):
        """状态同步循环"""
        while self._running:
            try:
                await self.sync_agent_states()
                await asyncio.sleep(self.state_sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in state sync loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _execution_loop(self):
        """执行循环"""
        while self._running:
            try:
                # 从执行队列获取任务
                context = await asyncio.wait_for(
                    self.execution_queue.get(),
                    timeout=1.0
                )
                
                # 执行任务
                await self._execute_task(context)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in execution loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _execute_task(self, context: CoordinationContext):
        """执行任务"""
        try:
            task_id = context.task_id
            agent_id = context.agent_id
            
            self.logger.info(f"Executing task {task_id} on agent {agent_id}")
            
            # 更新Agent状态
            if agent_id in self.agent_states:
                state = self.agent_states[agent_id]
                state.current_tasks.add(task_id)
            
            # 发送执行请求给Agent
            response = await communication_bus.send_request(
                sender_id="coordinator",
                receiver_id=agent_id,
                subject="execute_task",
                payload={
                    "task_id": task_id,
                    "strategy": context.strategy.value,
                    "metadata": context.metadata
                },
                priority=MessagePriority.HIGH,
                timeout=context.estimated_duration or 300.0
            )
            
            if response and response.get("success"):
                # 任务执行成功
                result = response.get("result")
                await self.handle_task_completion(task_id, success=True, result=result)
            else:
                # 任务执行失败
                error = response.get("error", "Unknown error") if response else "No response"
                await self.handle_task_failure(task_id, error, retry=True)
            
        except asyncio.TimeoutError:
            self.logger.error(f"Task {context.task_id} execution timeout")
            await self.handle_task_failure(context.task_id, "Execution timeout", retry=True)
        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            await self.handle_task_failure(context.task_id, str(e), retry=True)
    
    def get_coordination_stats(self) -> Dict[str, Any]:
        """获取协调统计信息"""
        total_agents = len(self.agent_states)
        total_tasks = len(self.coordination_contexts)
        
        active_tasks = sum(len(state.current_tasks) for state in self.agent_states.values())
        completed_tasks = sum(state.completed_tasks for state in self.agent_states.values())
        failed_tasks = sum(state.failed_tasks for state in self.agent_states.values())
        
        avg_health = sum(state.health_score for state in self.agent_states.values()) / max(total_agents, 1)
        
        return {
            "total_agents": total_agents,
            "total_tasks": total_tasks,
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "average_health_score": avg_health,
            "queue_size": self.execution_queue.qsize()
        }


# 全局Agent协调器实例
agent_coordinator = AgentCoordinator()
