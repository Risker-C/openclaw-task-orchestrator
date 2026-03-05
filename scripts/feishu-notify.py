#!/usr/bin/env python3
"""
飞书通知脚本 - Task Orchestrator v0.0.1
专门用于发送飞书消息通知
"""

import json
import logging
import argparse
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FeishuNotifier:
    """飞书通知工具类"""
    
    def __init__(self, config_path: str = "config/feishu.json"):
        """初始化飞书通知工具"""
        self.config_path = config_path
        self.config = {}
        self.templates = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                
                # 加载消息模板
                self.templates = self.config.get('notification', {}).get('templates', {})
                logger.info("飞书配置和模板加载成功")
            else:
                logger.warning(f"配置文件不存在: {self.config_path}")
                # 使用默认模板
                self._load_default_templates()
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            self._load_default_templates()
    
    def _load_default_templates(self):
        """加载默认消息模板"""
        self.templates = {
            "task_assigned": "🎯 任务分配通知\n\n**任务**: {task}\n**Agent**: {agent}\n**复杂度**: {complexity}\n**截止时间**: {deadline}",
            "task_completed": "✅ 任务完成通知\n\n**任务**: {task}\n**结果**: {result}\n**耗时**: {duration}",
            "task_failed": "❌ 任务失败通知\n\n**任务**: {task}\n**错误**: {error}\n**时间**: {timestamp}",
            "task_progress": "📊 任务进度更新\n\n**任务**: {task}\n**进度**: {progress}%\n**状态**: {status}",
            "system_alert": "🚨 系统告警\n\n**类型**: {alert_type}\n**消息**: {message}\n**时间**: {timestamp}"
        }
        logger.info("使用默认消息模板")
    
    def format_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """格式化消息模板"""
        try:
            if template_name not in self.templates:
                logger.error(f"模板不存在: {template_name}")
                return f"模板 {template_name} 不存在"
            
            template = self.templates[template_name]
            
            # 添加默认值
            formatted_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                **data
            }
            
            # 格式化模板
            message = template.format(**formatted_data)
            return message
            
        except KeyError as e:
            logger.error(f"模板参数缺失: {e}")
            return f"模板参数缺失: {e}"
        except Exception as e:
            logger.error(f"格式化模板异常: {e}")
            return f"格式化失败: {e}"
    
    def send_simple_message(self, message: str, targets: List[str] = None) -> bool:
        """发送简单文本消息"""
        try:
            # 使用OpenClaw的message工具发送
            import subprocess
            
            if not targets:
                # 使用默认目标
                default_target = self.config.get('notification', {}).get('default_chat_id', '')
                if default_target:
                    targets = [default_target]
                else:
                    logger.warning("未指定发送目标，且无默认目标")
                    return False
            
            success_count = 0
            for target in targets:
                try:
                    # 这里应该调用OpenClaw的message工具
                    # 暂时使用日志模拟
                    logger.info(f"发送消息到 {target}: {message[:100]}...")
                    success_count += 1
                except Exception as e:
                    logger.error(f"发送到 {target} 失败: {e}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"发送简单消息异常: {e}")
            return False
    
    def send_template_message(self, template_name: str, data: Dict[str, Any], 
                            targets: List[str] = None) -> bool:
        """发送模板消息"""
        try:
            # 格式化模板
            message = self.format_template(template_name, data)
            
            # 发送消息
            return self.send_simple_message(message, targets)
            
        except Exception as e:
            logger.error(f"发送模板消息异常: {e}")
            return False
    
    def send_card_message(self, title: str, content: str, 
                         targets: List[str] = None) -> bool:
        """发送卡片消息（未来实现）"""
        try:
            # 构建简单的卡片格式消息
            card_message = f"📋 **{title}**\n\n{content}"
            
            return self.send_simple_message(card_message, targets)
            
        except Exception as e:
            logger.error(f"发送卡片消息异常: {e}")
            return False
    
    def send_task_notification(self, task_id: str, task_title: str, 
                             event_type: str, **kwargs) -> bool:
        """发送任务相关通知"""
        try:
            # 根据事件类型选择模板
            template_map = {
                'assigned': 'task_assigned',
                'completed': 'task_completed', 
                'failed': 'task_failed',
                'progress': 'task_progress'
            }
            
            template_name = template_map.get(event_type)
            if not template_name:
                logger.error(f"未知的事件类型: {event_type}")
                return False
            
            # 准备模板数据
            template_data = {
                'task': task_title,
                'task_id': task_id,
                **kwargs
            }
            
            return self.send_template_message(template_name, template_data)
            
        except Exception as e:
            logger.error(f"发送任务通知异常: {e}")
            return False
    
    def send_system_alert(self, alert_type: str, message: str, 
                         targets: List[str] = None) -> bool:
        """发送系统告警"""
        try:
            template_data = {
                'alert_type': alert_type,
                'message': message
            }
            
            return self.send_template_message('system_alert', template_data, targets)
            
        except Exception as e:
            logger.error(f"发送系统告警异常: {e}")
            return False
    
    def list_templates(self) -> Dict[str, str]:
        """列出所有可用模板"""
        return self.templates.copy()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="飞书通知工具")
    parser.add_argument("--action", required=True,
                       choices=["send", "template", "card", "task", "alert", "list-templates"],
                       help="操作类型")
    
    # 通用参数
    parser.add_argument("--message", help="消息内容")
    parser.add_argument("--targets", help="发送目标，多个用逗号分隔")
    parser.add_argument("--target", help="单个发送目标")
    
    # 模板参数
    parser.add_argument("--template", help="模板名称")
    parser.add_argument("--data", help="模板数据(JSON格式)")
    
    # 卡片参数
    parser.add_argument("--title", help="卡片标题")
    parser.add_argument("--content", help="卡片内容")
    
    # 任务通知参数
    parser.add_argument("--task-id", help="任务ID")
    parser.add_argument("--task-title", help="任务标题")
    parser.add_argument("--event-type", help="事件类型")
    
    # 告警参数
    parser.add_argument("--alert-type", help="告警类型")
    
    # 配置参数
    parser.add_argument("--config", default="config/feishu.json", help="配置文件路径")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 初始化通知工具
        notifier = FeishuNotifier(args.config)
        
        # 处理目标列表
        targets = []
        if args.targets:
            targets = [t.strip() for t in args.targets.split(',')]
        elif args.target:
            targets = [args.target]
        
        # 执行相应操作
        success = False
        
        if args.action == "send":
            if not args.message:
                print("错误: 发送消息需要 --message 参数")
                sys.exit(1)
            success = notifier.send_simple_message(args.message, targets)
            
        elif args.action == "template":
            if not args.template or not args.data:
                print("错误: 模板消息需要 --template 和 --data 参数")
                sys.exit(1)
            
            try:
                data = json.loads(args.data)
            except json.JSONDecodeError:
                print("错误: --data 参数必须是有效的JSON格式")
                sys.exit(1)
            
            success = notifier.send_template_message(args.template, data, targets)
            
        elif args.action == "card":
            if not args.title or not args.content:
                print("错误: 卡片消息需要 --title 和 --content 参数")
                sys.exit(1)
            success = notifier.send_card_message(args.title, args.content, targets)
            
        elif args.action == "task":
            if not args.task_id or not args.task_title or not args.event_type:
                print("错误: 任务通知需要 --task-id, --task-title 和 --event-type 参数")
                sys.exit(1)
            
            # 解析额外数据
            extra_data = {}
            if args.data:
                try:
                    extra_data = json.loads(args.data)
                except json.JSONDecodeError:
                    print("错误: --data 参数必须是有效的JSON格式")
                    sys.exit(1)
            
            success = notifier.send_task_notification(
                args.task_id, args.task_title, args.event_type, **extra_data
            )
            
        elif args.action == "alert":
            if not args.alert_type or not args.message:
                print("错误: 系统告警需要 --alert-type 和 --message 参数")
                sys.exit(1)
            success = notifier.send_system_alert(args.alert_type, args.message, targets)
            
        elif args.action == "list-templates":
            templates = notifier.list_templates()
            print("📋 可用消息模板:")
            for name, template in templates.items():
                print(f"\n🔸 {name}:")
                print(f"   {template}")
            success = True
        
        # 输出结果
        if success:
            print(f"✅ {args.action} 操作成功")
            sys.exit(0)
        else:
            print(f"❌ {args.action} 操作失败")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"脚本执行异常: {e}")
        print(f"❌ 脚本执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()