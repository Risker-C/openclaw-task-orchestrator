"""
OpenClaw Task Orchestrator - 核心任务管理器

基于异步工单机制的任务管理，支持智能复杂度判断和飞书深度集成
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio
import uuid


class TaskComplexity(str, Enum):
    """任务复杂度枚举"""
    L1_SIMPLE = "L1"      # 简单任务：单Agent直接执行
    L2_SINGLE = "L2"      # 单步任务：专业Agent处理  
    L3_COMPLEX = "L3"     # 复杂任务：多Agent协作


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"           # 待处理
    ANALYZING = "analyzing"       # 分析中（复杂度判断）
    READY = "ready"              # 就绪（等待执行）
    RUNNING = "running"          # 执行中
    REVIEW = "review"            # 审查中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"  
    HIGH = "high"
    URGENT = "urgent"


class Task(BaseModel):
    """任务数据模型"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    complexity: Optional[TaskComplexity] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # 执行相关
    assigned_agent: Optional[str] = None
    agent_session_key: Optional[str] = None
    progress: int = Field(default=0, ge=0, le=100)
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 资源消耗
    token_cost: int = 0
    execution_time: Optional[float] = None  # 秒
    
    # 结果和文档
    result: Optional[Dict[str, Any]] = None
    result_doc_token: Optional[str] = None
    wiki_node_token: Optional[str] = None
    
    # 飞书集成
    bitable_record_id: Optional[str] = None
    approval_instance_id: Optional[str] = None
    
    # OpenSpec工作流
    openspec_artifacts: Optional[Dict[str, str]] = None  # artifact_type -> content
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskManager:
    """任务管理器 - 核心任务生命周期管理"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        
    async def create_task(self, title: str, description: str, 
                         priority: TaskPriority = TaskPriority.MEDIUM,
                         manual_complexity: Optional[TaskComplexity] = None) -> Task:
        """
        创建新任务 - 异步工单机制的核心入口
        
        Args:
            title: 任务标题
            description: 任务描述  
            priority: 任务优先级
            manual_complexity: 手动指定复杂度（可选）
            
        Returns:
            Task: 创建的任务对象
        """
        task = Task(
            title=title,
            description=description,
            priority=priority,
            complexity=manual_complexity
        )
        
        # 存储任务
        self.tasks[task.task_id] = task
        
        # 如果没有手动指定复杂度，需要进行智能判断
        if manual_complexity is None:
            task.status = TaskStatus.ANALYZING
            # 这里会调用复杂度判断器
            await self._analyze_complexity(task)
        else:
            task.status = TaskStatus.READY
            
        # 加入执行队列
        await self.task_queue.put(task.task_id)
        
        # 同步到飞书Bitable
        await self._sync_to_bitable(task)
        
        # 发送创建通知
        await self._send_notification(task, "task_created")
        
        return task
    
    async def update_task_status(self, task_id: str, status: TaskStatus, 
                                progress: Optional[int] = None,
                                result: Optional[Dict[str, Any]] = None) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            progress: 进度百分比（可选）
            result: 执行结果（可选）
            
        Returns:
            bool: 更新是否成功
        """
        if task_id not in self.tasks:
            return False
            
        task = self.tasks[task_id]
        old_status = task.status
        
        # 更新任务信息
        task.status = status
        task.updated_at = datetime.now()
        
        if progress is not None:
            task.progress = progress
            
        if result is not None:
            task.result = result
            
        # 状态特殊处理
        if status == TaskStatus.RUNNING and old_status != TaskStatus.RUNNING:
            task.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()
            if task.started_at:
                task.execution_time = (task.completed_at - task.started_at).total_seconds()
                
        # 同步到飞书
        await self._sync_to_bitable(task)
        
        # 发送状态变更通知
        await self._send_notification(task, "status_changed", {
            "old_status": old_status,
            "new_status": status
        })
        
        return True
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息"""
        return self.tasks.get(task_id)
    
    async def list_tasks(self, status: Optional[TaskStatus] = None,
                        complexity: Optional[TaskComplexity] = None,
                        priority: Optional[TaskPriority] = None) -> List[Task]:
        """
        列出任务
        
        Args:
            status: 按状态过滤（可选）
            complexity: 按复杂度过滤（可选）  
            priority: 按优先级过滤（可选）
            
        Returns:
            List[Task]: 符合条件的任务列表
        """
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        if complexity:
            tasks = [t for t in tasks if t.complexity == complexity]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
            
        # 按创建时间倒序排列
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks
    
    async def _analyze_complexity(self, task: Task):
        """智能复杂度判断 - 基于Magi项目的三级分流"""
        # TODO: 实现智能复杂度判断逻辑
        # 这里应该调用复杂度判断器，基于任务描述、历史数据等进行判断
        
        # 临时简单实现：基于描述长度和关键词
        description = task.description.lower()
        
        # L3复杂任务关键词
        l3_keywords = ["设计", "架构", "系统", "框架", "多轮", "迭代", "协作"]
        # L2单步任务关键词  
        l2_keywords = ["分析", "方案", "文档", "报告", "研究", "评估"]
        
        if any(keyword in description for keyword in l3_keywords) or len(description) > 500:
            task.complexity = TaskComplexity.L3_COMPLEX
        elif any(keyword in description for keyword in l2_keywords) or len(description) > 100:
            task.complexity = TaskComplexity.L2_SINGLE
        else:
            task.complexity = TaskComplexity.L1_SIMPLE
            
        task.status = TaskStatus.READY
    
    async def _sync_to_bitable(self, task: Task):
        """同步任务到飞书Bitable"""
        # TODO: 实现飞书Bitable同步逻辑
        # 这里应该调用飞书API，创建或更新Bitable记录
        pass
    
    async def _send_notification(self, task: Task, event_type: str, extra_data: Optional[Dict] = None):
        """发送飞书通知"""
        # TODO: 实现飞书消息通知逻辑
        # 这里应该发送飞书消息卡片或机器人消息
        pass


# 全局任务管理器实例
task_manager = TaskManager()