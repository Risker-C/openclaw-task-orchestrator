#!/usr/bin/env python3
"""
飞书同步脚本 - Task Orchestrator v0.0.1
用于同步任务状态到飞书Bitable和发送通知
"""

import json
import logging
import argparse
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.integrations.feishu.client import FeishuClient
    from src.core.task_manager import TaskStatus, TaskComplexity
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FeishuSyncTool:
    """飞书同步工具类"""
    
    def __init__(self, config_path: str = "config/feishu.json"):
        """初始化飞书同步工具"""
        self.config_path = config_path
        self.feishu_client = None
        self._load_config()
    
    def _load_config(self):
        """加载飞书配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.feishu_client = FeishuClient(config)
                logger.info("飞书配置加载成功")
            else:
                logger.warning(f"配置文件不存在: {self.config_path}")
                logger.info("将使用OpenClaw工具进行飞书操作")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            raise
    
    def create_task_record(self, task_id: str, title: str, complexity: str, 
                          agent: str = "", description: str = "") -> bool:
        """创建任务记录到Bitable"""
        try:
            if not self.feishu_client:
                logger.warning("飞书客户端未初始化，跳过Bitable操作")
                return False
            
            # 准备记录数据
            record_data = {
                "任务ID": task_id,
                "任务标题": title,
                "复杂度": complexity,
                "状态": "待处理",
                "分配Agent": agent,
                "创建时间": datetime.now().isoformat(),
                "描述": description[:500] if description else ""  # 限制长度
            }
            
            # 调用飞书客户端创建记录
            result = self.feishu_client.create_bitable_record(record_data)
            
            if result:
                logger.info(f"任务记录创建成功: {task_id}")
                return True
            else:
                logger.error(f"任务记录创建失败: {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"创建任务记录异常: {e}")
            return False
    
    def update_task_status(self, task_id: str, status: str, 
                          progress: int = 0, result: str = "") -> bool:
        """更新任务状态"""
        try:
            if not self.feishu_client:
                logger.warning("飞书客户端未初始化，跳过状态更新")
                return False
            
            # 准备更新数据
            update_data = {
                "状态": status,
                "进度": f"{progress}%",
                "更新时间": datetime.now().isoformat()
            }
            
            # 如果任务完成，添加结果
            if status == "已完成" and result:
                update_data["执行结果"] = result[:1000]  # 限制长度
                update_data["完成时间"] = datetime.now().isoformat()
            
            # 调用飞书客户端更新记录
            result = self.feishu_client.update_bitable_record(task_id, update_data)
            
            if result:
                logger.info(f"任务状态更新成功: {task_id} -> {status}")
                return True
            else:
                logger.error(f"任务状态更新失败: {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"更新任务状态异常: {e}")
            return False
    
    def send_notification(self, message: str, target: str = "", 
                         template: str = "", data: Dict[str, Any] = None) -> bool:
        """发送飞书通知"""
        try:
            if not self.feishu_client:
                logger.warning("飞书客户端未初始化，跳过通知发送")
                return False
            
            # 如果使用模板
            if template and data:
                result = self.feishu_client.send_template_message(template, data, target)
            else:
                result = self.feishu_client.send_message(message, target)
            
            if result:
                logger.info(f"通知发送成功: {message[:50]}...")
                return True
            else:
                logger.error(f"通知发送失败: {message[:50]}...")
                return False
                
        except Exception as e:
            logger.error(f"发送通知异常: {e}")
            return False
    
    def sync_all_tasks(self) -> bool:
        """同步所有任务状态"""
        try:
            logger.info("开始同步所有任务状态...")
            
            # 这里应该从TaskManager获取所有任务
            # 由于是脚本模式，暂时跳过
            logger.info("批量同步功能待实现")
            return True
            
        except Exception as e:
            logger.error(f"同步所有任务异常: {e}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="飞书同步工具")
    parser.add_argument("--action", required=True, 
                       choices=["create", "update", "notify", "sync-all"],
                       help="操作类型")
    
    # 创建任务参数
    parser.add_argument("--task-id", help="任务ID")
    parser.add_argument("--title", help="任务标题")
    parser.add_argument("--complexity", help="任务复杂度")
    parser.add_argument("--agent", help="分配的Agent")
    parser.add_argument("--description", help="任务描述")
    
    # 更新状态参数
    parser.add_argument("--status", help="任务状态")
    parser.add_argument("--progress", type=int, default=0, help="任务进度")
    parser.add_argument("--result", help="执行结果")
    
    # 通知参数
    parser.add_argument("--message", help="通知消息")
    parser.add_argument("--target", help="通知目标")
    parser.add_argument("--template", help="消息模板")
    parser.add_argument("--data", help="模板数据(JSON格式)")
    
    # 配置参数
    parser.add_argument("--config", default="config/feishu.json", help="配置文件路径")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 初始化同步工具
        sync_tool = FeishuSyncTool(args.config)
        
        # 执行相应操作
        if args.action == "create":
            if not args.task_id or not args.title:
                print("错误: 创建任务需要 --task-id 和 --title 参数")
                sys.exit(1)
            
            success = sync_tool.create_task_record(
                args.task_id, args.title, args.complexity or "L1",
                args.agent or "", args.description or ""
            )
            
        elif args.action == "update":
            if not args.task_id or not args.status:
                print("错误: 更新状态需要 --task-id 和 --status 参数")
                sys.exit(1)
            
            success = sync_tool.update_task_status(
                args.task_id, args.status, args.progress, args.result or ""
            )
            
        elif args.action == "notify":
            if not args.message:
                print("错误: 发送通知需要 --message 参数")
                sys.exit(1)
            
            data = None
            if args.data:
                try:
                    data = json.loads(args.data)
                except json.JSONDecodeError:
                    print("错误: --data 参数必须是有效的JSON格式")
                    sys.exit(1)
            
            success = sync_tool.send_notification(
                args.message, args.target or "", args.template or "", data
            )
            
        elif args.action == "sync-all":
            success = sync_tool.sync_all_tasks()
        
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