"""
Agent间通信协议 - 实现Agent之间的消息传递和通信机制

支持异步消息队列、事件驱动、RPC调用等通信模式
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Callable, Coroutine
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class MessageType(str, Enum):
    """消息类型枚举"""
    REQUEST = "request"           # 请求消息
    RESPONSE = "response"         # 响应消息
    EVENT = "event"               # 事件消息
    HEARTBEAT = "heartbeat"       # 心跳消息
    STATUS_UPDATE = "status_update"  # 状态更新
    ERROR = "error"               # 错误消息


class MessagePriority(str, Enum):
    """消息优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Message:
    """通信消息"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.REQUEST
    sender_id: str = ""
    receiver_id: str = ""
    priority: MessagePriority = MessagePriority.NORMAL
    
    # 消息内容
    subject: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # 关联信息
    correlation_id: Optional[str] = None  # 用于关联请求和响应
    reply_to: Optional[str] = None        # 回复地址
    
    # 状态
    delivered: bool = False
    delivery_attempts: int = 0
    max_retries: int = 3
    
    def is_expired(self) -> bool:
        """检查消息是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "priority": self.priority.value,
            "subject": self.subject,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "delivered": self.delivered,
            "delivery_attempts": self.delivery_attempts
        }


class MessageQueue:
    """消息队列 - 管理Agent间的消息传递"""
    
    def __init__(self, max_queue_size: int = 1000):
        self.logger = logging.getLogger(__name__)
        self.max_queue_size = max_queue_size
        
        # 按优先级分类的消息队列
        self.urgent_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.high_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.normal_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.low_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        
        # 消息历史记录
        self.message_history: Dict[str, Message] = {}
        self.max_history_size = 10000
        
        # 待处理消息
        self.pending_messages: Dict[str, Message] = {}
    
    async def send_message(self, message: Message) -> bool:
        """
        发送消息
        
        Args:
            message: 消息对象
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 检查消息是否过期
            if message.is_expired():
                self.logger.warning(f"Message {message.message_id} is expired")
                return False
            
            # 根据优先级放入相应队列
            queue = self._get_queue_by_priority(message.priority)
            
            try:
                queue.put_nowait(message)
                self.pending_messages[message.message_id] = message
                self.logger.debug(f"Message {message.message_id} sent to {message.receiver_id}")
                return True
            except asyncio.QueueFull:
                self.logger.error(f"Message queue full for priority {message.priority.value}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False
    
    async def receive_message(self, timeout: Optional[float] = None) -> Optional[Message]:
        """
        接收消息 - 按优先级获取
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            Optional[Message]: 接收到的消息，None表示超时
        """
        try:
            # 按优先级顺序尝试获取消息
            queues = [
                self.urgent_queue,
                self.high_queue,
                self.normal_queue,
                self.low_queue
            ]
            
            # 使用wait_for实现超时
            if timeout:
                end_time = asyncio.get_event_loop().time() + timeout
            
            while True:
                # 尝试从高优先级队列获取
                for queue in queues:
                    try:
                        message = queue.get_nowait()
                        self.logger.debug(f"Message {message.message_id} received from {message.sender_id}")
                        return message
                    except asyncio.QueueEmpty:
                        continue
                
                # 所有队列都为空，等待
                if timeout:
                    remaining = end_time - asyncio.get_event_loop().time()
                    if remaining <= 0:
                        return None
                    wait_time = min(0.1, remaining)
                else:
                    wait_time = 0.1
                
                await asyncio.sleep(wait_time)
                
        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            return None
    
    async def acknowledge_message(self, message_id: str) -> bool:
        """
        确认消息已处理
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 确认是否成功
        """
        try:
            if message_id in self.pending_messages:
                message = self.pending_messages.pop(message_id)
                message.delivered = True
                
                # 添加到历史记录
                self._add_to_history(message)
                
                self.logger.debug(f"Message {message_id} acknowledged")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error acknowledging message: {e}")
            return False
    
    async def retry_message(self, message_id: str) -> bool:
        """
        重试发送消息
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 重试是否成功
        """
        try:
            if message_id not in self.pending_messages:
                return False
            
            message = self.pending_messages[message_id]
            
            # 检查重试次数
            if message.delivery_attempts >= message.max_retries:
                self.logger.warning(f"Message {message_id} exceeded max retries")
                return False
            
            # 增加重试次数
            message.delivery_attempts += 1
            
            # 重新发送
            queue = self._get_queue_by_priority(message.priority)
            queue.put_nowait(message)
            
            self.logger.info(f"Message {message_id} retried (attempt {message.delivery_attempts})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error retrying message: {e}")
            return False
    
    def _get_queue_by_priority(self, priority: MessagePriority) -> asyncio.Queue:
        """根据优先级获取队列"""
        if priority == MessagePriority.URGENT:
            return self.urgent_queue
        elif priority == MessagePriority.HIGH:
            return self.high_queue
        elif priority == MessagePriority.NORMAL:
            return self.normal_queue
        else:
            return self.low_queue
    
    def _add_to_history(self, message: Message):
        """添加消息到历史记录"""
        self.message_history[message.message_id] = message
        
        # 限制历史记录大小
        if len(self.message_history) > self.max_history_size:
            # 删除最旧的消息
            oldest_id = min(self.message_history.keys(), 
                          key=lambda k: self.message_history[k].created_at)
            del self.message_history[oldest_id]
    
    def get_message_history(self, sender_id: Optional[str] = None,
                           receiver_id: Optional[str] = None,
                           limit: int = 100) -> List[Message]:
        """获取消息历史"""
        messages = list(self.message_history.values())
        
        if sender_id:
            messages = [m for m in messages if m.sender_id == sender_id]
        if receiver_id:
            messages = [m for m in messages if m.receiver_id == receiver_id]
        
        # 按时间倒序排列
        messages.sort(key=lambda m: m.created_at, reverse=True)
        
        return messages[:limit]


class AgentCommunicationBus:
    """Agent通信总线 - 管理Agent间的通信"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.message_queue = MessageQueue()
        
        # 消息处理器注册表
        self.message_handlers: Dict[str, List[Callable]] = {}
        
        # 事件监听器
        self.event_listeners: Dict[str, List[Callable]] = {}
        
        # RPC调用的响应缓存
        self.rpc_responses: Dict[str, Any] = {}
        self.rpc_response_events: Dict[str, asyncio.Event] = {}
        
        self._running = False
        self._message_processor_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动通信总线"""
        if self._running:
            return
        
        self.logger.info("Starting Agent Communication Bus...")
        self._running = True
        
        # 启动消息处理器
        self._message_processor_task = asyncio.create_task(self._message_processor_loop())
        
        self.logger.info("Agent Communication Bus started")
    
    async def stop(self):
        """停止通信总线"""
        if not self._running:
            return
        
        self.logger.info("Stopping Agent Communication Bus...")
        self._running = False
        
        if self._message_processor_task:
            self._message_processor_task.cancel()
            try:
                await self._message_processor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Agent Communication Bus stopped")
    
    async def send_request(self, sender_id: str, receiver_id: str,
                          subject: str, payload: Dict[str, Any],
                          priority: MessagePriority = MessagePriority.NORMAL,
                          timeout: Optional[float] = 30.0) -> Optional[Dict[str, Any]]:
        """
        发送请求并等待响应 (RPC调用)
        
        Args:
            sender_id: 发送者ID
            receiver_id: 接收者ID
            subject: 请求主题
            payload: 请求数据
            priority: 优先级
            timeout: 超时时间（秒）
            
        Returns:
            Optional[Dict]: 响应数据，None表示超时或失败
        """
        try:
            # 创建请求消息
            message = Message(
                message_type=MessageType.REQUEST,
                sender_id=sender_id,
                receiver_id=receiver_id,
                subject=subject,
                payload=payload,
                priority=priority,
                reply_to=sender_id
            )
            
            # 创建响应事件
            response_event = asyncio.Event()
            self.rpc_response_events[message.message_id] = response_event
            
            # 发送请求
            success = await self.message_queue.send_message(message)
            if not success:
                del self.rpc_response_events[message.message_id]
                return None
            
            # 等待响应
            try:
                await asyncio.wait_for(response_event.wait(), timeout=timeout)
                response = self.rpc_responses.pop(message.message_id, None)
                return response
            except asyncio.TimeoutError:
                self.logger.warning(f"RPC call {message.message_id} timed out")
                return None
            finally:
                self.rpc_response_events.pop(message.message_id, None)
                
        except Exception as e:
            self.logger.error(f"Error sending RPC request: {e}")
            return None
    
    async def send_response(self, sender_id: str, correlation_id: str,
                           payload: Dict[str, Any],
                           priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """
        发送响应消息
        
        Args:
            sender_id: 发送者ID
            correlation_id: 关联的请求ID
            payload: 响应数据
            priority: 优先级
            
        Returns:
            bool: 发送是否成功
        """
        try:
            message = Message(
                message_type=MessageType.RESPONSE,
                sender_id=sender_id,
                subject="response",
                payload=payload,
                priority=priority,
                correlation_id=correlation_id
            )
            
            return await self.message_queue.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
            return False
    
    async def publish_event(self, sender_id: str, event_type: str,
                           payload: Dict[str, Any],
                           priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """
        发布事件
        
        Args:
            sender_id: 发送者ID
            event_type: 事件类型
            payload: 事件数据
            priority: 优先级
            
        Returns:
            bool: 发布是否成功
        """
        try:
            message = Message(
                message_type=MessageType.EVENT,
                sender_id=sender_id,
                receiver_id="*",  # 广播
                subject=event_type,
                payload=payload,
                priority=priority
            )
            
            return await self.message_queue.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error publishing event: {e}")
            return False
    
    def register_message_handler(self, subject: str, 
                                handler: Callable[[Message], Coroutine]) -> bool:
        """
        注册消息处理器
        
        Args:
            subject: 消息主题
            handler: 处理函数
            
        Returns:
            bool: 注册是否成功
        """
        try:
            if subject not in self.message_handlers:
                self.message_handlers[subject] = []
            
            self.message_handlers[subject].append(handler)
            self.logger.debug(f"Message handler registered for subject: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering message handler: {e}")
            return False
    
    def register_event_listener(self, event_type: str,
                               listener: Callable[[Message], Coroutine]) -> bool:
        """
        注册事件监听器
        
        Args:
            event_type: 事件类型
            listener: 监听函数
            
        Returns:
            bool: 注册是否成功
        """
        try:
            if event_type not in self.event_listeners:
                self.event_listeners[event_type] = []
            
            self.event_listeners[event_type].append(listener)
            self.logger.debug(f"Event listener registered for event: {event_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering event listener: {e}")
            return False
    
    async def _message_processor_loop(self):
        """消息处理循环"""
        while self._running:
            try:
                # 接收消息
                message = await self.message_queue.receive_message(timeout=1.0)
                
                if message is None:
                    continue
                
                # 处理消息
                await self._process_message(message)
                
                # 确认消息
                await self.message_queue.acknowledge_message(message.message_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in message processor loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_message(self, message: Message):
        """处理消息"""
        try:
            if message.message_type == MessageType.REQUEST:
                # 处理请求
                handlers = self.message_handlers.get(message.subject, [])
                for handler in handlers:
                    try:
                        await handler(message)
                    except Exception as e:
                        self.logger.error(f"Error in message handler: {e}")
                        
            elif message.message_type == MessageType.RESPONSE:
                # 处理响应
                if message.correlation_id in self.rpc_response_events:
                    self.rpc_responses[message.correlation_id] = message.payload
                    self.rpc_response_events[message.correlation_id].set()
                    
            elif message.message_type == MessageType.EVENT:
                # 处理事件
                listeners = self.event_listeners.get(message.subject, [])
                for listener in listeners:
                    try:
                        await listener(message)
                    except Exception as e:
                        self.logger.error(f"Error in event listener: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")


# 全局通信总线实例
communication_bus = AgentCommunicationBus()
