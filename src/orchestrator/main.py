"""
OpenClaw Task Orchestrator - 主程序入口

基于异步工单机制的任务编排系统，集成飞书深度能力
融合OpenSpec工作流、Magi智能分级、edict异步机制等最佳实践
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.task_manager import task_manager, Task, TaskComplexity, TaskPriority
from src.core.scheduler import task_scheduler
from src.core.complexity import complexity_analyzer
from src.integrations.feishu.client import feishu_client
from src.integrations.openclaw.client import openclaw_client


class TaskOrchestrator:
    """任务编排器主类"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self._shutdown_event = asyncio.Event()
        
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/orchestrator.log')
            ]
        )
        return logging.getLogger(__name__)
    
    async def start(self):
        """启动编排器"""
        self.logger.info("Starting OpenClaw Task Orchestrator...")
        
        try:
            # 初始化各个组件
            await self._initialize_components()
            
            # 启动任务调度器
            await task_scheduler.start()
            
            # 注册信号处理
            self._register_signal_handlers()
            
            self.logger.info("Task Orchestrator started successfully")
            
            # 等待关闭信号
            await self._shutdown_event.wait()
            
        except Exception as e:
            self.logger.error(f"Failed to start orchestrator: {e}")
            raise
        finally:
            await self._shutdown()
    
    async def _initialize_components(self):
        """初始化各个组件"""
        # 初始化飞书客户端
        await feishu_client.initialize()
        
        # 初始化OpenClaw客户端
        await openclaw_client.initialize()
        
        # 注册默认Agent
        await self._register_default_agents()
        
        # 初始化飞书Bitable表结构
        await self._initialize_bitable()
    
    async def _register_default_agents(self):
        """注册默认Agent"""
        default_agents = [
            ("general", "general"),
            ("research-analyst", "research-analyst"),
            ("doc-engineer", "doc-engineer"),
            ("architect", "architect"),
            ("code-reviewer", "code-reviewer"),
            ("ui-designer", "ui-designer"),
            ("implementation-planner", "implementation-planner"),
            ("task-orchestrator", "task-orchestrator"),
            ("security-monitor", "security-monitor"),
            ("resource-manager", "resource-manager")
        ]
        
        for agent_id, agent_type in default_agents:
            await task_scheduler.register_agent(agent_id, agent_type)
    
    async def _initialize_bitable(self):
        """初始化飞书Bitable表结构"""
        try:
            # 检查并创建任务表
            await feishu_client.ensure_task_table()
            self.logger.info("Bitable task table initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Bitable: {e}")
    
    def _register_signal_handlers(self):
        """注册信号处理器"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self._trigger_shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _trigger_shutdown(self):
        """触发关闭"""
        self._shutdown_event.set()
    
    async def _shutdown(self):
        """关闭编排器"""
        self.logger.info("Shutting down Task Orchestrator...")
        
        # 停止任务调度器
        await task_scheduler.stop()
        
        # 关闭客户端连接
        await feishu_client.close()
        await openclaw_client.close()
        
        self.logger.info("Task Orchestrator shutdown complete")


class TaskAPI:
    """任务API接口 - 提供外部调用接口"""
    
    @staticmethod
    def _validate_task_input(title: str, description: str) -> Optional[str]:
        """验证任务输入参数"""
        if not title or not title.strip():
            return "Task title is required"
        if len(title.strip()) > 200:
            return "Task title too long (max 200 characters)"
        if not description or not description.strip():
            return "Task description is required"
        if len(description.strip()) > 5000:
            return "Task description too long (max 5000 characters)"
        return None
    
    @staticmethod
    def _validate_task_id(task_id: str) -> Optional[str]:
        """验证任务ID格式"""
        if not task_id or not task_id.strip():
            return "Task ID is required"
        # 简单的UUID格式验证
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, task_id.strip()):
            return "Invalid task ID format"
        return None
    
    @staticmethod
    async def create_task(title: str, description: str, 
                         priority: str = "medium",
                         complexity: Optional[str] = None) -> dict:
        """
        创建新任务 - POST /api/tasks
        
        Args:
            title: 任务标题
            description: 任务描述
            priority: 优先级 (low/medium/high/urgent)
            complexity: 手动指定复杂度 (L1/L2/L3)
            
        Returns:
            dict: 任务信息
        """
        try:
            # 输入验证
            validation_error = TaskAPI._validate_task_input(title, description)
            if validation_error:
                return {
                    "success": False,
                    "error": validation_error,
                    "error_code": "VALIDATION_ERROR"
                }
            
            # 参数转换和验证
            try:
                task_priority = TaskPriority(priority.lower())
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid priority: {priority}. Must be one of: low, medium, high, urgent",
                    "error_code": "INVALID_PRIORITY"
                }
            
            manual_complexity = None
            if complexity:
                try:
                    manual_complexity = TaskComplexity(complexity.upper())
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid complexity: {complexity}. Must be one of: L1, L2, L3",
                        "error_code": "INVALID_COMPLEXITY"
                    }
            
            # 创建任务
            task = await task_manager.create_task(
                title=title.strip(),
                description=description.strip(),
                priority=task_priority,
                manual_complexity=manual_complexity
            )
            
            return {
                "success": True,
                "data": {
                    "task_id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "complexity": task.complexity.value if task.complexity else None,
                    "progress": task.progress,
                    "created_at": task.created_at.isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Internal server error: {str(e)}",
                "error_code": "INTERNAL_ERROR"
            }
    
    @staticmethod
    async def get_task(task_id: str) -> dict:
        """
        获取任务信息 - GET /api/tasks/{id}
        
        Args:
            task_id: 任务ID
            
        Returns:
            dict: 任务详细信息
        """
        try:
            # 验证任务ID
            validation_error = TaskAPI._validate_task_id(task_id)
            if validation_error:
                return {
                    "success": False,
                    "error": validation_error,
                    "error_code": "VALIDATION_ERROR"
                }
            
            task = await task_manager.get_task(task_id.strip())
            if not task:
                return {
                    "success": False,
                    "error": "Task not found",
                    "error_code": "TASK_NOT_FOUND"
                }
            
            return {
                "success": True,
                "data": {
                    "task_id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "complexity": task.complexity.value if task.complexity else None,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "progress": task.progress,
                    "assigned_agent": task.assigned_agent,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "execution_time": task.execution_time,
                    "token_cost": task.token_cost,
                    "result": task.result
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Internal server error: {str(e)}",
                "error_code": "INTERNAL_ERROR"
            }
    
    @staticmethod
    async def update_task(task_id: str, **kwargs) -> dict:
        """
        更新任务信息 - PUT /api/tasks/{id}
        
        Args:
            task_id: 任务ID
            **kwargs: 更新字段 (title, description, priority, status, progress, result)
            
        Returns:
            dict: 更新结果
        """
        try:
            # 验证任务ID
            validation_error = TaskAPI._validate_task_id(task_id)
            if validation_error:
                return {
                    "success": False,
                    "error": validation_error,
                    "error_code": "VALIDATION_ERROR"
                }
            
            # 检查任务是否存在
            task = await task_manager.get_task(task_id.strip())
            if not task:
                return {
                    "success": False,
                    "error": "Task not found",
                    "error_code": "TASK_NOT_FOUND"
                }
            
            # 处理更新字段
            updated_fields = []
            
            # 更新标题和描述
            if 'title' in kwargs or 'description' in kwargs:
                new_title = kwargs.get('title', task.title)
                new_description = kwargs.get('description', task.description)
                
                validation_error = TaskAPI._validate_task_input(new_title, new_description)
                if validation_error:
                    return {
                        "success": False,
                        "error": validation_error,
                        "error_code": "VALIDATION_ERROR"
                    }
                
                task.title = new_title.strip()
                task.description = new_description.strip()
                updated_fields.extend(['title', 'description'])
            
            # 更新优先级
            if 'priority' in kwargs:
                try:
                    task.priority = TaskPriority(kwargs['priority'].lower())
                    updated_fields.append('priority')
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid priority: {kwargs['priority']}",
                        "error_code": "INVALID_PRIORITY"
                    }
            
            # 更新状态和进度
            if 'status' in kwargs:
                try:
                    from src.core.task_manager import TaskStatus
                    new_status = TaskStatus(kwargs['status'].lower())
                    progress = kwargs.get('progress')
                    result = kwargs.get('result')
                    
                    success = await task_manager.update_task_status(
                        task_id.strip(), new_status, progress, result
                    )
                    
                    if not success:
                        return {
                            "success": False,
                            "error": "Failed to update task status",
                            "error_code": "UPDATE_FAILED"
                        }
                    
                    updated_fields.extend(['status', 'progress', 'result'])
                    
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid status: {kwargs['status']}",
                        "error_code": "INVALID_STATUS"
                    }
            
            # 如果有其他字段更新，更新时间戳
            if updated_fields:
                from datetime import datetime
                task.updated_at = datetime.now()
            
            return {
                "success": True,
                "data": {
                    "task_id": task.task_id,
                    "updated_fields": updated_fields,
                    "updated_at": task.updated_at.isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Internal server error: {str(e)}",
                "error_code": "INTERNAL_ERROR"
            }
    
    @staticmethod
    async def delete_task(task_id: str) -> dict:
        """
        删除任务 - DELETE /api/tasks/{id}
        
        Args:
            task_id: 任务ID
            
        Returns:
            dict: 删除结果
        """
        try:
            # 验证任务ID
            validation_error = TaskAPI._validate_task_id(task_id)
            if validation_error:
                return {
                    "success": False,
                    "error": validation_error,
                    "error_code": "VALIDATION_ERROR"
                }
            
            # 检查任务是否存在
            task = await task_manager.get_task(task_id.strip())
            if not task:
                return {
                    "success": False,
                    "error": "Task not found",
                    "error_code": "TASK_NOT_FOUND"
                }
            
            # 检查任务状态，运行中的任务不能删除
            from src.core.task_manager import TaskStatus
            if task.status == TaskStatus.RUNNING:
                return {
                    "success": False,
                    "error": "Cannot delete running task. Please cancel it first.",
                    "error_code": "TASK_RUNNING"
                }
            
            # 删除任务
            del task_manager.tasks[task_id.strip()]
            
            return {
                "success": True,
                "data": {
                    "task_id": task_id.strip(),
                    "deleted_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Internal server error: {str(e)}",
                "error_code": "INTERNAL_ERROR"
            }
    
    @staticmethod
    async def list_tasks(status: Optional[str] = None,
                        complexity: Optional[str] = None,
                        priority: Optional[str] = None,
                        limit: int = 50,
                        offset: int = 0) -> dict:
        """
        列出任务 - GET /api/tasks
        
        Args:
            status: 按状态过滤
            complexity: 按复杂度过滤
            priority: 按优先级过滤
            limit: 返回数量限制 (默认50)
            offset: 偏移量 (默认0)
            
        Returns:
            dict: 任务列表
        """
        try:
            # 参数验证
            if limit < 1 or limit > 1000:
                return {
                    "success": False,
                    "error": "Limit must be between 1 and 1000",
                    "error_code": "INVALID_LIMIT"
                }
            
            if offset < 0:
                return {
                    "success": False,
                    "error": "Offset must be non-negative",
                    "error_code": "INVALID_OFFSET"
                }
            
            # 转换过滤参数
            status_filter = None
            if status:
                try:
                    from src.core.task_manager import TaskStatus
                    status_filter = TaskStatus(status.lower())
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid status: {status}",
                        "error_code": "INVALID_STATUS"
                    }
            
            complexity_filter = None
            if complexity:
                try:
                    complexity_filter = TaskComplexity(complexity.upper())
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid complexity: {complexity}",
                        "error_code": "INVALID_COMPLEXITY"
                    }
            
            priority_filter = None
            if priority:
                try:
                    priority_filter = TaskPriority(priority.lower())
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid priority: {priority}",
                        "error_code": "INVALID_PRIORITY"
                    }
            
            # 获取任务列表
            tasks = await task_manager.list_tasks(
                status=status_filter,
                complexity=complexity_filter,
                priority=priority_filter
            )
            
            # 分页处理
            total = len(tasks)
            tasks = tasks[offset:offset + limit]
            
            task_list = []
            for task in tasks:
                task_list.append({
                    "task_id": task.task_id,
                    "title": task.title,
                    "complexity": task.complexity.value if task.complexity else None,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "progress": task.progress,
                    "assigned_agent": task.assigned_agent,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat()
                })
            
            return {
                "success": True,
                "data": {
                    "tasks": task_list,
                    "pagination": {
                        "total": total,
                        "limit": limit,
                        "offset": offset,
                        "has_more": offset + limit < total
                    }
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Internal server error: {str(e)}",
                "error_code": "INTERNAL_ERROR"
            }


async def main():
    """主函数"""
    orchestrator = TaskOrchestrator()
    
    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        print("\nReceived interrupt signal")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 创建日志目录
    Path("logs").mkdir(exist_ok=True)
    
    # 运行主程序
    asyncio.run(main())