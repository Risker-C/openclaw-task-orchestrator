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
    async def create_task(title: str, description: str, 
                         priority: str = "medium",
                         complexity: Optional[str] = None) -> dict:
        """
        创建新任务
        
        Args:
            title: 任务标题
            description: 任务描述
            priority: 优先级 (low/medium/high/urgent)
            complexity: 手动指定复杂度 (L1/L2/L3)
            
        Returns:
            dict: 任务信息
        """
        try:
            # 转换参数
            task_priority = TaskPriority(priority.lower())
            manual_complexity = TaskComplexity(complexity) if complexity else None
            
            # 创建任务
            task = await task_manager.create_task(
                title=title,
                description=description,
                priority=task_priority,
                manual_complexity=manual_complexity
            )
            
            return {
                "success": True,
                "task_id": task.task_id,
                "status": task.status.value,
                "complexity": task.complexity.value if task.complexity else None,
                "created_at": task.created_at.isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def get_task(task_id: str) -> dict:
        """获取任务信息"""
        try:
            task = await task_manager.get_task(task_id)
            if not task:
                return {
                    "success": False,
                    "error": "Task not found"
                }
            
            return {
                "success": True,
                "task": {
                    "task_id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "complexity": task.complexity.value if task.complexity else None,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "progress": task.progress,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def list_tasks(status: Optional[str] = None,
                        complexity: Optional[str] = None,
                        priority: Optional[str] = None) -> dict:
        """列出任务"""
        try:
            # 转换过滤参数
            status_filter = None
            if status:
                from src.core.task_manager import TaskStatus
                status_filter = TaskStatus(status.lower())
            
            complexity_filter = None
            if complexity:
                complexity_filter = TaskComplexity(complexity)
            
            priority_filter = None
            if priority:
                priority_filter = TaskPriority(priority.lower())
            
            # 获取任务列表
            tasks = await task_manager.list_tasks(
                status=status_filter,
                complexity=complexity_filter,
                priority=priority_filter
            )
            
            task_list = []
            for task in tasks:
                task_list.append({
                    "task_id": task.task_id,
                    "title": task.title,
                    "complexity": task.complexity.value if task.complexity else None,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "progress": task.progress,
                    "created_at": task.created_at.isoformat()
                })
            
            return {
                "success": True,
                "tasks": task_list,
                "total": len(task_list)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
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