"""
Agent调度器 - 基础Agent池管理和任务调度

实现Agent注册发现、负载均衡、健康检查等核心功能
支持多Agent并行执行和智能资源分配
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import uuid

from .task_manager import Task, TaskComplexity, TaskStatus


class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"           # 空闲
    BUSY = "busy"           # 忙碌
    OFFLINE = "offline"     # 离线
    ERROR = "error"         # 错误状态
    MAINTENANCE = "maintenance"  # 维护中


class LoadBalanceStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"     # 轮询
    LEAST_CONNECTIONS = "least_connections"  # 最少连接
    RANDOM = "random"               # 随机
    WEIGHTED = "weighted"           # 权重
    COMPLEXITY_BASED = "complexity_based"  # 基于复杂度


@dataclass
class AgentInfo:
    """Agent信息"""
    agent_id: str
    agent_type: str
    status: AgentStatus = AgentStatus.OFFLINE
    capabilities: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 3
    current_tasks: Set[str] = field(default_factory=set)
    total_tasks_completed: int = 0
    total_execution_time: float = 0.0
    last_heartbeat: Optional[datetime] = None
    health_score: float = 1.0
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_available(self) -> bool:
        """检查Agent是否可用"""
        return (self.status == AgentStatus.IDLE and 
                len(self.current_tasks) < self.max_concurrent_tasks)
    
    @property
    def load_factor(self) -> float:
        """计算负载因子 (0-1)"""
        if self.max_concurrent_tasks == 0:
            return 1.0
        return len(self.current_tasks) / self.max_concurrent_tasks
    
    @property
    def average_execution_time(self) -> float:
        """平均执行时间"""
        if self.total_tasks_completed == 0:
            return 0.0
        return self.total_execution_time / self.total_tasks_completed


@dataclass
class TaskAssignment:
    """任务分配记录"""
    task_id: str
    agent_id: str
    assigned_at: datetime
    complexity: TaskComplexity
    estimated_duration: Optional[float] = None
    actual_duration: Optional[float] = None
    completed_at: Optional[datetime] = None
    success: bool = False


class AgentScheduler:
    """Agent调度器 - 核心调度逻辑"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agents: Dict[str, AgentInfo] = {}
        self.assignments: Dict[str, TaskAssignment] = {}  # task_id -> assignment
        self.load_balance_strategy = LoadBalanceStrategy.COMPLEXITY_BASED
        self.health_check_interval = 30.0  # 健康检查间隔(秒)
        self.heartbeat_timeout = 60.0      # 心跳超时(秒)
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None
        
        # 复杂度到Agent类型的映射
        self.complexity_agent_mapping = {
            TaskComplexity.L1_SIMPLE: ["general"],
            TaskComplexity.L2_SINGLE: [
                "research-analyst", "doc-engineer", "architect", 
                "code-reviewer", "ui-designer", "implementation-planner"
            ],
            TaskComplexity.L3_COMPLEX: [
                "task-orchestrator", "architect", "security-monitor", 
                "resource-manager", "implementation-planner"
            ]
        }
    
    async def start(self):
        """启动调度器"""
        if self._running:
            return
        
        self.logger.info("Starting Agent Scheduler...")
        self._running = True
        
        # 启动健康检查任务
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        self.logger.info("Agent Scheduler started successfully")
    
    async def stop(self):
        """停止调度器"""
        if not self._running:
            return
        
        self.logger.info("Stopping Agent Scheduler...")
        self._running = False
        
        # 停止健康检查任务
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # 清理所有Agent状态
        for agent in self.agents.values():
            agent.status = AgentStatus.OFFLINE
        
        self.logger.info("Agent Scheduler stopped")
    
    async def register_agent(self, agent_id: str, agent_type: str, 
                           capabilities: Optional[List[str]] = None,
                           max_concurrent_tasks: int = 3,
                           weight: float = 1.0,
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        注册Agent
        
        Args:
            agent_id: Agent唯一标识
            agent_type: Agent类型
            capabilities: Agent能力列表
            max_concurrent_tasks: 最大并发任务数
            weight: 权重 (用于加权负载均衡)
            metadata: 元数据
            
        Returns:
            bool: 注册是否成功
        """
        try:
            if agent_id in self.agents:
                self.logger.warning(f"Agent {agent_id} already registered, updating...")
            
            agent_info = AgentInfo(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities or [],
                max_concurrent_tasks=max_concurrent_tasks,
                weight=weight,
                metadata=metadata or {},
                status=AgentStatus.IDLE,
                last_heartbeat=datetime.now()
            )
            
            self.agents[agent_id] = agent_info
            self.logger.info(f"Agent {agent_id} ({agent_type}) registered successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {agent_id}: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        注销Agent
        
        Args:
            agent_id: Agent标识
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if agent_id not in self.agents:
                self.logger.warning(f"Agent {agent_id} not found")
                return False
            
            agent = self.agents[agent_id]
            
            # 检查是否有正在执行的任务
            if agent.current_tasks:
                self.logger.warning(f"Agent {agent_id} has {len(agent.current_tasks)} running tasks")
                # 可以选择等待任务完成或强制取消
                agent.status = AgentStatus.MAINTENANCE
                return False
            
            # 移除Agent
            del self.agents[agent_id]
            self.logger.info(f"Agent {agent_id} unregistered successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    async def update_agent_heartbeat(self, agent_id: str, 
                                   status: Optional[AgentStatus] = None,
                                   health_score: Optional[float] = None,
                                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        更新Agent心跳
        
        Args:
            agent_id: Agent标识
            status: 状态更新
            health_score: 健康分数 (0-1)
            metadata: 元数据更新
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if agent_id not in self.agents:
                self.logger.warning(f"Agent {agent_id} not found for heartbeat update")
                return False
            
            agent = self.agents[agent_id]
            agent.last_heartbeat = datetime.now()
            
            if status is not None:
                agent.status = status
            
            if health_score is not None:
                agent.health_score = max(0.0, min(1.0, health_score))
            
            if metadata is not None:
                agent.metadata.update(metadata)
            
            self.logger.debug(f"Agent {agent_id} heartbeat updated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update agent {agent_id} heartbeat: {e}")
            return False
    
    async def assign_task(self, task: Task) -> Optional[str]:
        """
        分配任务给合适的Agent
        
        Args:
            task: 任务对象
            
        Returns:
            Optional[str]: 分配的Agent ID，None表示分配失败
        """
        try:
            # 根据复杂度筛选候选Agent
            candidate_agents = self._get_candidate_agents(task.complexity)
            
            if not candidate_agents:
                self.logger.warning(f"No available agents for task {task.task_id} (complexity: {task.complexity.value})")
                return None
            
            # 根据负载均衡策略选择Agent
            selected_agent_id = self._select_agent(candidate_agents, task)
            
            if not selected_agent_id:
                self.logger.warning(f"No suitable agent selected for task {task.task_id}")
                return None
            
            # 执行分配
            success = await self._execute_assignment(task, selected_agent_id)
            
            if success:
                self.logger.info(f"Task {task.task_id} assigned to agent {selected_agent_id}")
                return selected_agent_id
            else:
                self.logger.error(f"Failed to assign task {task.task_id} to agent {selected_agent_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error assigning task {task.task_id}: {e}")
            return None
    
    async def complete_task(self, task_id: str, success: bool = True, 
                          execution_time: Optional[float] = None) -> bool:
        """
        标记任务完成
        
        Args:
            task_id: 任务ID
            success: 是否成功完成
            execution_time: 实际执行时间
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if task_id not in self.assignments:
                self.logger.warning(f"Task {task_id} assignment not found")
                return False
            
            assignment = self.assignments[task_id]
            agent_id = assignment.agent_id
            
            if agent_id not in self.agents:
                self.logger.warning(f"Agent {agent_id} not found for task completion")
                return False
            
            agent = self.agents[agent_id]
            
            # 更新任务分配记录
            assignment.completed_at = datetime.now()
            assignment.success = success
            if execution_time is not None:
                assignment.actual_duration = execution_time
            
            # 更新Agent状态
            if task_id in agent.current_tasks:
                agent.current_tasks.remove(task_id)
            
            if success:
                agent.total_tasks_completed += 1
                if execution_time is not None:
                    agent.total_execution_time += execution_time
            
            # 如果没有其他任务，设置为空闲
            if not agent.current_tasks and agent.status == AgentStatus.BUSY:
                agent.status = AgentStatus.IDLE
            
            self.logger.info(f"Task {task_id} completed on agent {agent_id} (success: {success})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error completing task {task_id}: {e}")
            return False
    
    def _get_candidate_agents(self, complexity: TaskComplexity) -> List[AgentInfo]:
        """根据复杂度获取候选Agent"""
        suitable_types = self.complexity_agent_mapping.get(complexity, [])
        
        candidates = []
        for agent in self.agents.values():
            if (agent.agent_type in suitable_types and 
                agent.is_available and 
                agent.status not in [AgentStatus.OFFLINE, AgentStatus.ERROR, AgentStatus.MAINTENANCE]):
                candidates.append(agent)
        
        return candidates
    
    def _select_agent(self, candidates: List[AgentInfo], task: Task) -> Optional[str]:
        """根据负载均衡策略选择Agent"""
        if not candidates:
            return None
        
        if self.load_balance_strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._select_round_robin(candidates)
        elif self.load_balance_strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return self._select_least_connections(candidates)
        elif self.load_balance_strategy == LoadBalanceStrategy.RANDOM:
            return self._select_random(candidates)
        elif self.load_balance_strategy == LoadBalanceStrategy.WEIGHTED:
            return self._select_weighted(candidates)
        elif self.load_balance_strategy == LoadBalanceStrategy.COMPLEXITY_BASED:
            return self._select_complexity_based(candidates, task)
        else:
            # 默认使用最少连接策略
            return self._select_least_connections(candidates)
    
    def _select_round_robin(self, candidates: List[AgentInfo]) -> str:
        """轮询选择"""
        # 简单实现：按agent_id排序后选择
        candidates.sort(key=lambda x: x.agent_id)
        return candidates[0].agent_id
    
    def _select_least_connections(self, candidates: List[AgentInfo]) -> str:
        """最少连接选择"""
        return min(candidates, key=lambda x: len(x.current_tasks)).agent_id
    
    def _select_random(self, candidates: List[AgentInfo]) -> str:
        """随机选择"""
        import random
        return random.choice(candidates).agent_id
    
    def _select_weighted(self, candidates: List[AgentInfo]) -> str:
        """权重选择"""
        # 考虑权重和当前负载
        best_agent = None
        best_score = float('inf')
        
        for agent in candidates:
            # 分数 = 负载因子 / 权重 (越小越好)
            score = agent.load_factor / max(agent.weight, 0.1)
            if score < best_score:
                best_score = score
                best_agent = agent
        
        return best_agent.agent_id if best_agent else candidates[0].agent_id
    
    def _select_complexity_based(self, candidates: List[AgentInfo], task: Task) -> str:
        """基于复杂度的智能选择"""
        # 综合考虑：负载、健康分数、历史表现、Agent类型匹配度
        best_agent = None
        best_score = float('-inf')
        
        for agent in candidates:
            # 计算综合分数
            load_score = 1.0 - agent.load_factor  # 负载越低分数越高
            health_score = agent.health_score
            performance_score = 1.0 / max(agent.average_execution_time, 1.0) if agent.average_execution_time > 0 else 1.0
            
            # 类型匹配度
            type_score = 1.0
            if task.complexity == TaskComplexity.L3_COMPLEX and agent.agent_type in ["architect", "task-orchestrator"]:
                type_score = 1.5
            elif task.complexity == TaskComplexity.L2_SINGLE and agent.agent_type in ["research-analyst", "doc-engineer"]:
                type_score = 1.2
            
            # 综合分数 (可调整权重)
            total_score = (load_score * 0.4 + 
                          health_score * 0.3 + 
                          performance_score * 0.2 + 
                          type_score * 0.1)
            
            if total_score > best_score:
                best_score = total_score
                best_agent = agent
        
        return best_agent.agent_id if best_agent else candidates[0].agent_id
    
    async def _execute_assignment(self, task: Task, agent_id: str) -> bool:
        """执行任务分配"""
        try:
            agent = self.agents[agent_id]
            
            # 创建分配记录
            assignment = TaskAssignment(
                task_id=task.task_id,
                agent_id=agent_id,
                assigned_at=datetime.now(),
                complexity=task.complexity
            )
            
            # 估算执行时间
            if agent.average_execution_time > 0:
                complexity_multiplier = {
                    TaskComplexity.L1_SIMPLE: 1.0,
                    TaskComplexity.L2_SINGLE: 3.0,
                    TaskComplexity.L3_COMPLEX: 8.0
                }
                assignment.estimated_duration = (agent.average_execution_time * 
                                                complexity_multiplier.get(task.complexity, 1.0))
            
            # 更新Agent状态
            agent.current_tasks.add(task.task_id)
            if agent.status == AgentStatus.IDLE:
                agent.status = AgentStatus.BUSY
            
            # 保存分配记录
            self.assignments[task.task_id] = assignment
            
            # 更新任务状态
            task.assigned_agent = agent_id
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute assignment for task {task.task_id}: {e}")
            return False
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self._running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5.0)  # 错误后短暂等待
    
    async def _perform_health_check(self):
        """执行健康检查"""
        current_time = datetime.now()
        timeout_threshold = timedelta(seconds=self.heartbeat_timeout)
        
        for agent_id, agent in self.agents.items():
            if agent.last_heartbeat is None:
                continue
            
            # 检查心跳超时
            if current_time - agent.last_heartbeat > timeout_threshold:
                if agent.status != AgentStatus.OFFLINE:
                    self.logger.warning(f"Agent {agent_id} heartbeat timeout, marking as offline")
                    agent.status = AgentStatus.OFFLINE
                    agent.health_score = 0.0
                    
                    # 处理该Agent的运行中任务
                    await self._handle_agent_failure(agent_id)
    
    async def _handle_agent_failure(self, agent_id: str):
        """处理Agent故障"""
        agent = self.agents.get(agent_id)
        if not agent:
            return
        
        # 获取该Agent的所有运行中任务
        failed_tasks = list(agent.current_tasks)
        
        for task_id in failed_tasks:
            self.logger.warning(f"Task {task_id} failed due to agent {agent_id} failure")
            
            # 移除任务分配
            if task_id in self.assignments:
                assignment = self.assignments[task_id]
                assignment.completed_at = datetime.now()
                assignment.success = False
            
            # 清理Agent状态
            agent.current_tasks.discard(task_id)
            
            # TODO: 这里可以实现任务重新调度逻辑
            # await self._reschedule_task(task_id)
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """获取Agent统计信息"""
        stats = {
            "total_agents": len(self.agents),
            "agents_by_status": {},
            "agents_by_type": {},
            "total_assignments": len(self.assignments),
            "active_tasks": 0
        }
        
        for agent in self.agents.values():
            # 按状态统计
            status = agent.status.value
            stats["agents_by_status"][status] = stats["agents_by_status"].get(status, 0) + 1
            
            # 按类型统计
            agent_type = agent.agent_type
            stats["agents_by_type"][agent_type] = stats["agents_by_type"].get(agent_type, 0) + 1
            
            # 活跃任务数
            stats["active_tasks"] += len(agent.current_tasks)
        
        return stats
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取特定Agent信息"""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        return {
            "agent_id": agent.agent_id,
            "agent_type": agent.agent_type,
            "status": agent.status.value,
            "capabilities": agent.capabilities,
            "max_concurrent_tasks": agent.max_concurrent_tasks,
            "current_tasks": list(agent.current_tasks),
            "current_load": len(agent.current_tasks),
            "load_factor": agent.load_factor,
            "total_tasks_completed": agent.total_tasks_completed,
            "average_execution_time": agent.average_execution_time,
            "health_score": agent.health_score,
            "weight": agent.weight,
            "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
            "metadata": agent.metadata
        }
    
    def list_agents(self, status_filter: Optional[AgentStatus] = None,
                   type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出Agent"""
        agents = []
        
        for agent in self.agents.values():
            if status_filter and agent.status != status_filter:
                continue
            if type_filter and agent.agent_type != type_filter:
                continue
            
            agent_info = self.get_agent_info(agent.agent_id)
            if agent_info:
                agents.append(agent_info)
        
        return agents


# 全局调度器实例
task_scheduler = AgentScheduler()