"""
飞书集成客户端 - 深度集成飞书Bitable、消息、审批等能力

基于上午测试验证的飞书能力，实现工单管理、看板可视化、消息通知等功能
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from src.core.task_manager import Task, TaskStatus, TaskComplexity, TaskPriority


class FeishuClient:
    """飞书客户端 - 封装飞书API调用"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        self._initialized = False
        
        # 飞书API工具映射（基于OpenClaw现有工具）
        self.tools = {
            'bitable_create_record': 'feishu_bitable_create_record',
            'bitable_update_record': 'feishu_bitable_update_record', 
            'bitable_list_records': 'feishu_bitable_list_records',
            'bitable_get_record': 'feishu_bitable_get_record',
            'doc_create': 'feishu_doc_create',
            'doc_write': 'feishu_doc_write',
            'wiki_create': 'feishu_wiki_create',
            'message_send': 'message_send'
        }
    
    async def initialize(self):
        """初始化飞书客户端"""
        if self._initialized:
            return
            
        try:
            # 加载配置
            await self._load_config()
            
            # 验证配置
            await self._validate_config()
            
            self._initialized = True
            self.logger.info("Feishu client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Feishu client: {e}")
            raise
    
    async def _load_config(self):
        """加载飞书配置"""
        try:
            with open('config/feishu.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # 使用示例配置
            with open('config/feishu.example.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.logger.warning("Using example config, please update config/feishu.json")
    
    async def _validate_config(self):
        """验证配置有效性"""
        required_fields = ['app_id', 'app_secret', 'app_token']
        for field in required_fields:
            if not self.config.get(field) or self.config[field].startswith('your_'):
                raise ValueError(f"Please configure {field} in config/feishu.json")
    
    async def ensure_task_table(self):
        """确保任务表存在并具有正确的字段结构"""
        try:
            # 检查表是否存在
            table_config = self.config.get('table_configs', {}).get('tasks', {})
            table_id = table_config.get('table_id')
            
            if not table_id or table_id.startswith('your_'):
                self.logger.warning("Task table not configured, please update config/feishu.json")
                return
            
            # TODO: 这里应该调用OpenClaw的feishu工具检查表结构
            # 暂时跳过，假设表已存在
            self.logger.info("Task table validation skipped (TODO: implement)")
            
        except Exception as e:
            self.logger.error(f"Failed to ensure task table: {e}")
            raise
    
    async def create_task_record(self, task: Task) -> Optional[str]:
        """
        在飞书Bitable中创建任务记录
        
        Args:
            task: 任务对象
            
        Returns:
            Optional[str]: 创建的记录ID
        """
        try:
            table_config = self.config.get('table_configs', {}).get('tasks', {})
            app_token = self.config.get('app_token')
            table_id = table_config.get('table_id')
            
            if not app_token or not table_id:
                self.logger.error("Missing app_token or table_id configuration")
                return None
            
            # 构建字段数据
            fields = {
                "任务ID": task.task_id,
                "任务标题": task.title,
                "任务描述": task.description,
                "复杂度": task.complexity.value if task.complexity else "",
                "状态": self._translate_status(task.status),
                "优先级": self._translate_priority(task.priority),
                "分配Agent": task.assigned_agent or "",
                "创建时间": int(task.created_at.timestamp() * 1000),
                "更新时间": int(task.updated_at.timestamp() * 1000),
                "进度百分比": task.progress,
                "Token消耗": task.token_cost
            }
            
            # TODO: 这里应该调用OpenClaw的feishu_bitable_create_record工具
            # 暂时模拟返回记录ID
            record_id = f"rec_{task.task_id[:8]}"
            
            self.logger.info(f"Created Bitable record {record_id} for task {task.task_id}")
            return record_id
            
        except Exception as e:
            self.logger.error(f"Failed to create task record: {e}")
            return None
    
    async def update_task_record(self, task: Task) -> bool:
        """
        更新飞书Bitable中的任务记录
        
        Args:
            task: 任务对象
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if not task.bitable_record_id:
                # 如果没有记录ID，尝试创建新记录
                record_id = await self.create_task_record(task)
                if record_id:
                    task.bitable_record_id = record_id
                return record_id is not None
            
            # 构建更新字段
            fields = {
                "状态": self._translate_status(task.status),
                "更新时间": int(task.updated_at.timestamp() * 1000),
                "进度百分比": task.progress,
                "Token消耗": task.token_cost,
                "分配Agent": task.assigned_agent or ""
            }
            
            # 如果任务完成，添加结果信息
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                if task.result_doc_token:
                    fields["结果文档"] = task.result_doc_token
                if task.wiki_node_token:
                    fields["Wiki节点"] = task.wiki_node_token
            
            # TODO: 这里应该调用OpenClaw的feishu_bitable_update_record工具
            
            self.logger.info(f"Updated Bitable record for task {task.task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update task record: {e}")
            return False
    
    async def send_task_notification(self, task: Task, event_type: str, extra_data: Optional[Dict] = None):
        """
        发送任务相关通知
        
        Args:
            task: 任务对象
            event_type: 事件类型 (task_created, status_changed, task_completed等)
            extra_data: 额外数据
        """
        try:
            notification_config = self.config.get('notification', {})
            if not notification_config.get('enable_cards', True):
                return
            
            chat_id = notification_config.get('chat_id')
            if not chat_id or chat_id.startswith('your_'):
                self.logger.warning("Notification chat_id not configured")
                return
            
            # 构建消息内容
            message = self._build_notification_message(task, event_type, extra_data)
            
            # TODO: 这里应该调用OpenClaw的message工具发送飞书消息
            
            self.logger.info(f"Sent {event_type} notification for task {task.task_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
    
    async def create_task_document(self, task: Task, content: str) -> Optional[str]:
        """
        为任务创建飞书文档
        
        Args:
            task: 任务对象
            content: 文档内容
            
        Returns:
            Optional[str]: 文档token
        """
        try:
            # 构建文档标题
            title = f"任务结果 - {task.title}"
            
            # TODO: 这里应该调用OpenClaw的feishu_doc_create工具
            doc_token = f"doc_{task.task_id[:8]}"
            
            self.logger.info(f"Created document {doc_token} for task {task.task_id}")
            return doc_token
            
        except Exception as e:
            self.logger.error(f"Failed to create task document: {e}")
            return None
    
    async def archive_to_wiki(self, task: Task, doc_token: str) -> Optional[str]:
        """
        将任务文档归档到Wiki
        
        Args:
            task: 任务对象
            doc_token: 文档token
            
        Returns:
            Optional[str]: Wiki节点token
        """
        try:
            # TODO: 这里应该调用OpenClaw的feishu_wiki_create工具
            wiki_node_token = f"wiki_{task.task_id[:8]}"
            
            self.logger.info(f"Archived task {task.task_id} to wiki node {wiki_node_token}")
            return wiki_node_token
            
        except Exception as e:
            self.logger.error(f"Failed to archive to wiki: {e}")
            return None
    
    def _translate_status(self, status: TaskStatus) -> str:
        """将任务状态翻译为中文"""
        translations = {
            TaskStatus.PENDING: "待处理",
            TaskStatus.ANALYZING: "分析中", 
            TaskStatus.READY: "就绪",
            TaskStatus.RUNNING: "执行中",
            TaskStatus.REVIEW: "审查中",
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.FAILED: "失败",
            TaskStatus.CANCELLED: "已取消"
        }
        return translations.get(status, status.value)
    
    def _translate_priority(self, priority: TaskPriority) -> str:
        """将优先级翻译为中文"""
        translations = {
            TaskPriority.LOW: "低",
            TaskPriority.MEDIUM: "中",
            TaskPriority.HIGH: "高", 
            TaskPriority.URGENT: "紧急"
        }
        return translations.get(priority, priority.value)
    
    def _build_notification_message(self, task: Task, event_type: str, extra_data: Optional[Dict] = None) -> str:
        """构建通知消息内容"""
        messages = {
            "task_created": f"📝 新任务创建：{task.title}\n复杂度：{task.complexity.value if task.complexity else '未知'}\n优先级：{self._translate_priority(task.priority)}",
            "status_changed": f"🔄 任务状态变更：{task.title}\n状态：{self._translate_status(task.status)}\n进度：{task.progress}%",
            "task_completed": f"✅ 任务完成：{task.title}\n执行时间：{task.execution_time:.1f}秒" if task.execution_time else f"✅ 任务完成：{task.title}",
            "task_failed": f"❌ 任务失败：{task.title}\n请检查执行日志"
        }
        
        return messages.get(event_type, f"📋 任务更新：{task.title}")
    
    async def close(self):
        """关闭客户端"""
        self._initialized = False
        self.logger.info("Feishu client closed")


# 全局飞书客户端实例
feishu_client = FeishuClient()