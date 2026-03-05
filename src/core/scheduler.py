"""
任务调度器 - 基于OpenClaw的异步任务调度和Agent编排

融合edict异步工单机制、Magi智能路由、OpenSpec工作流等最佳实践
实现高效的任务调度和多Agent协作编排
"""

import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging

from .task_manager import Task, TaskStatus, TaskComplexity, TaskPriority, task_manager
from .complexity import complexity_analyzer


@dataclass
class AgentInfo:
    """Agent信息"""
    agent_id: str
    agent_type: str
    session_key: Optional[str] = None
    status: str = "idle"  # idle, busy, failed
    current_task_id: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    success_rate: float = 1.0
    avg_execution_time: float = 0.0
    total_tasks: int = 0
    failed_tasks: int = 0


@dataclass 
class SchedulingContext:
    """调度上下文"""
    available_agents: List[AgentInfo] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    running_tasks: Dict[str, str] = field(default_factory=dict)  # task_id -> agent_id
    failed_tasks: Set[str] = field(default_factory=set)
    
    
class TaskScheduler:
    """任务调度器 - 核心调度逻辑"""
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self.context = SchedulingContext()
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        
        # 调度配置
        self.max_concurrent_tasks = 10
        self.polling_interval = 30  # 秒
        self.agent_timeout = 300    # Agent超时时间（秒）
        
        # 专业Agent映射
        self.specialist_agents = {
            TaskComplexity.L1_SIMPLE: ["general"],
            TaskComplexity.L2_SINGLE: [
                "research-analyst", "doc-engineer", "code-reviewer", 
                "ui-designer", "security-monitor"
            ],
            TaskComplexity.L3_COMPLEX: [
                "architect", "task-orchestrator", "implementation-planner",
                "resource-manager", "strategic-advisor"
            ]
        }
        
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """启动调度器"""
        if self._running:
            return
            
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("Task scheduler started")
    
    async def stop(self):
        """停止调度器"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Task scheduler stopped")
    
    async def _scheduler_loop(self):
        """调度器主循环"""
        while self._running:
            try:
                await self._schedule_tasks()
                await self._check_agent_health()
                await self._handle_timeouts()
                await asyncio.sleep(self.polling_interval)
            except Exception as e:
                self.logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(5)  # 错误后短暂等待
    
    async def _schedule_tasks(self):
        """调度待处理任务"""
        # 获取待处理任务
        pending_tasks = await task_manager.list_tasks(status=TaskStatus.READY)
        
        # 按优先级和创建时间排序
        pending_tasks.sort(key=lambda t: (
            self._get_priority_weight(t.priority),
            t.created_at
        ))
        
        # 检查并发限制
        running_count = len(self.context.running_tasks)
        if running_count >= self.max_concurrent_tasks:
            return
        
        # 调度任务
        for task in pending_tasks[:self.max_concurrent_tasks - running_count]:
            agent = await self._select_agent(task)
            if agent:
                await self._dispatch_task(task, agent)
    
    async def _select_agent(self, task: Task) -> Optional[AgentInfo]:
        """
        选择最适合的Agent执行任务
        
        基于以下因素进行选择：
        1. Agent类型匹配度
        2. 当前负载情况  
        3. 历史成功率
        4. 平均执行时间
        """
        # 获取适合的Agent类型
        suitable_types = self.specialist_agents.get(task.complexity, ["general"])
        
        # 筛选可用的Agent
        available_agents = [
            agent for agent in self.agents.values()
            if (agent.status == "idle" and 
                agent.agent_type in suitable_types and
                self._is_agent_healthy(agent))
        ]
        
        if not available_agents:
            return None
        
        # 计算Agent得分并选择最优
        best_agent = None
        best_score = -1
        
        for agent in available_agents:
            score = self._calculate_agent_score(agent, task)
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent
    
    def _calculate_agent_score(self, agent: AgentInfo, task: Task) -> float:
        """
        计算Agent适合度得分
        
        参考AutoRedTeam的多方法验证思想，综合多个指标
        """
        # 基础得分
        score = 1.0
        
        # 成功率权重 (40%)
        score += agent.success_rate * 0.4
        
        # 负载权重 (30%) - 空闲Agent得分更高
        if agent.status == "idle":
            score += 0.3
        
        # 经验权重 (20%) - 有经验但不过载
        if agent.total_tasks > 0:
            experience_factor = min(agent.total_tasks / 10, 1.0)
            score += experience_factor * 0.2
        
        # 优先级匹配权重 (10%)
        if task.priority == TaskPriority.URGENT:
            # 紧急任务优先选择成功率高的Agent
            score += agent.success_rate * 0.1
        
        return score
    
    def _get_priority_weight(self, priority: TaskPriority) -> int:
        """获取优先级权重（用于排序）"""
        weights = {
            TaskPriority.URGENT: 4,
            TaskPriority.HIGH: 3,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 1
        }
        return weights.get(priority, 2)
    
    def _is_agent_healthy(self, agent: AgentInfo) -> bool:
        """检查Agent是否健康"""
        if not agent.last_heartbeat:
            return True  # 新Agent默认健康
        
        # 检查心跳超时
        timeout_threshold = datetime.now() - timedelta(seconds=self.agent_timeout)
        if agent.last_heartbeat < timeout_threshold:
            return False
        
        # 检查失败率
        if agent.total_tasks > 5 and agent.success_rate < 0.5:
            return False
        
        return True
    
    async def _dispatch_task(self, task: Task, agent: AgentInfo):
        """
        派发任务给Agent
        
        基于OpenClaw的sessions_spawn机制启动Agent执行任务
        """
        try:
            # 更新任务状态
            await task_manager.update_task_status(
                task.task_id, 
                TaskStatus.RUNNING,
                progress=0
            )
            
            # 根据复杂度选择执行策略
            if task.complexity == TaskComplexity.L1_SIMPLE:
                await self._execute_l1_task(task, agent)
            elif task.complexity == TaskComplexity.L2_SINGLE:
                await self._execute_l2_task(task, agent)
            else:  # L3_COMPLEX
                await self._execute_l3_task(task, agent)
            
            # 更新Agent状态
            agent.status = "busy"
            agent.current_task_id = task.task_id
            
            # 记录调度信息
            self.context.running_tasks[task.task_id] = agent.agent_id
            
            self.logger.info(f"Task {task.task_id} dispatched to agent {agent.agent_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to dispatch task {task.task_id}: {e}")
            await task_manager.update_task_status(task.task_id, TaskStatus.FAILED)
    
    async def _execute_l1_task(self, task: Task, agent: AgentInfo):
        """执行L1简单任务 - 直接执行"""
        # TODO: 实现L1任务的直接执行逻辑
        # 这里应该调用OpenClaw的sessions_spawn，启动简单任务执行
        pass
    
    async def _execute_l2_task(self, task: Task, agent: AgentInfo):
        """执行L2单步任务 - 专业Agent处理"""
        # TODO: 实现L2任务的专业Agent执行逻辑
        # 调用sessions_spawn启动专业Agent
        pass
    
    async def _execute_l3_task(self, task: Task, agent: AgentInfo):
        """执行L3复杂任务 - 多Agent协作"""
        # TODO: 实现L3任务的多Agent协作逻辑
        # 1. 基于OpenSpec工作流进行任务分解
        # 2. 生成artifact结构
        # 3. 启动多个Agent协作执行
        # 4. 协调Agent间的依赖关系
        pass
    
    async def _check_agent_health(self):
        """检查Agent健康状态"""
        current_time = datetime.now()
        
        for agent in self.agents.values():
            if not self._is_agent_healthy(agent):
                if agent.status == "busy" and agent.current_task_id:
                    # Agent不健康且正在执行任务，标记任务失败
                    await self._handle_agent_failure(agent)
                
                # 标记Agent为失败状态
                agent.status = "failed"
                self.logger.warning(f"Agent {agent.agent_id} marked as unhealthy")
    
    async def _handle_timeouts(self):
        """处理任务超时"""
        current_time = datetime.now()
        timeout_threshold = timedelta(hours=2)  # 2小时超时
        
        for task_id, agent_id in list(self.context.running_tasks.items()):
            task = await task_manager.get_task(task_id)
            if task and task.started_at:
                if current_time - task.started_at > timeout_threshold:
                    await self._handle_task_timeout(task, agent_id)
    
    async def _handle_agent_failure(self, agent: AgentInfo):
        """处理Agent失败"""
        if agent.current_task_id:
            task = await task_manager.get_task(agent.current_task_id)
            if task:
                # 尝试重新调度任务
                await self._reschedule_task(task, agent)
        
        # 清理Agent状态
        agent.status = "failed"
        agent.current_task_id = None
    
    async def _handle_task_timeout(self, task: Task, agent_id: str):
        """处理任务超时"""
        self.logger.warning(f"Task {task.task_id} timeout, agent: {agent_id}")
        
        # 标记任务失败
        await task_manager.update_task_status(task.task_id, TaskStatus.FAILED)
        
        # 清理调度状态
        if task.task_id in self.context.running_tasks:
            del self.context.running_tasks[task.task_id]
        
        # 更新Agent状态
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.status = "idle"
            agent.current_task_id = None
            agent.failed_tasks += 1
            self._update_agent_success_rate(agent)
    
    async def _reschedule_task(self, task: Task, failed_agent: AgentInfo):
        """重新调度失败的任务"""
        # 增加重试计数
        retry_count = getattr(task, 'retry_count', 0) + 1
        setattr(task, 'retry_count', retry_count)
        
        # 如果重试次数过多，标记为失败
        if retry_count > 3:
            await task_manager.update_task_status(task.task_id, TaskStatus.FAILED)
            return
        
        # 重置任务状态，重新调度
        await task_manager.update_task_status(task.task_id, TaskStatus.READY)
        
        # 清理调度状态
        if task.task_id in self.context.running_tasks:
            del self.context.running_tasks[task.task_id]
        
        self.logger.info(f"Task {task.task_id} rescheduled (retry {retry_count})")
    
    def _update_agent_success_rate(self, agent: AgentInfo):
        """更新Agent成功率"""
        if agent.total_tasks > 0:
            success_tasks = agent.total_tasks - agent.failed_tasks
            agent.success_rate = success_tasks / agent.total_tasks
    
    async def register_agent(self, agent_id: str, agent_type: str) -> AgentInfo:
        """注册Agent"""
        agent = AgentInfo(
            agent_id=agent_id,
            agent_type=agent_type,
            last_heartbeat=datetime.now()
        )
        self.agents[agent_id] = agent
        self.logger.info(f"Agent {agent_id} ({agent_type}) registered")
        return agent
    
    async def unregister_agent(self, agent_id: str):
        """注销Agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            if agent.current_task_id:
                await self._handle_agent_failure(agent)
            del self.agents[agent_id]
            self.logger.info(f"Agent {agent_id} unregistered")
    
    async def agent_heartbeat(self, agent_id: str):
        """Agent心跳"""
        if agent_id in self.agents:
            self.agents[agent_id].last_heartbeat = datetime.now()
    
    async def task_completed(self, task_id: str, agent_id: str, success: bool):
        """任务完成回调"""
        # 更新任务状态
        status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        await task_manager.update_task_status(task_id, status, progress=100)
        
        # 更新Agent状态
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.status = "idle"
            agent.current_task_id = None
            agent.total_tasks += 1
            if not success:
                agent.failed_tasks += 1
            self._update_agent_success_rate(agent)
        
        # 清理调度状态
        if task_id in self.context.running_tasks:
            del self.context.running_tasks[task_id]
        
        self.logger.info(f"Task {task_id} completed by agent {agent_id}, success: {success}")


# 全局任务调度器实例
task_scheduler = TaskScheduler()