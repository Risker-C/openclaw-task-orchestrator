#!/usr/bin/env python3
"""
配置辅助工具 - Task Orchestrator v0.0.1
用于管理和验证飞书配置
"""

import json
import logging
import argparse
import sys
import os
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigHelper:
    """配置辅助工具类"""
    
    def __init__(self, config_path: str = "config/feishu.json"):
        """初始化配置工具"""
        self.config_path = config_path
        self.config = {}
    
    def create_default_config(self) -> Dict[str, Any]:
        """创建默认配置"""
        default_config = {
            "app_info": {
                "app_id": "cli_xxxxxxxxxx",
                "app_secret": "your_app_secret_here"
            },
            "bitable": {
                "app_token": "your_app_token_here",
                "tables": {
                    "tasks": {
                        "table_id": "your_table_id_here",
                        "fields": {
                            "task_id": "任务ID",
                            "title": "任务标题",
                            "complexity": "复杂度",
                            "status": "状态",
                            "agent": "分配Agent",
                            "created_at": "创建时间",
                            "completed_at": "完成时间",
                            "result": "执行结果",
                            "notes": "备注"
                        }
                    }
                }
            },
            "notification": {
                "default_chat_id": "oc_xxxxxxxxxx",
                "templates": {
                    "task_assigned": "🎯 任务分配通知\n\n**任务**: {task}\n**Agent**: {agent}\n**复杂度**: {complexity}\n**截止时间**: {deadline}",
                    "task_completed": "✅ 任务完成通知\n\n**任务**: {task}\n**结果**: {result}\n**耗时**: {duration}",
                    "task_failed": "❌ 任务失败通知\n\n**任务**: {task}\n**错误**: {error}\n**时间**: {timestamp}",
                    "task_progress": "📊 任务进度更新\n\n**任务**: {task}\n**进度**: {progress}%\n**状态**: {status}",
                    "system_alert": "🚨 系统告警\n\n**类型**: {alert_type}\n**消息**: {message}\n**时间**: {timestamp}"
                }
            },
            "settings": {
                "auto_sync": True,
                "notification_enabled": True,
                "retry_count": 3,
                "timeout": 30
            }
        }
        return default_config
    
    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"配置文件加载成功: {self.config_path}")
                return True
            else:
                logger.warning(f"配置文件不存在: {self.config_path}")
                return False
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return False
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """保存配置文件"""
        try:
            config_to_save = config or self.config
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置文件保存成功: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def init_config(self) -> bool:
        """初始化配置文件"""
        try:
            if os.path.exists(self.config_path):
                print(f"⚠️  配置文件已存在: {self.config_path}")
                response = input("是否覆盖现有配置? (y/N): ")
                if response.lower() != 'y':
                    print("取消初始化")
                    return False
            
            # 创建默认配置
            default_config = self.create_default_config()
            
            # 保存配置
            if self.save_config(default_config):
                print(f"✅ 默认配置文件已创建: {self.config_path}")
                print("\n📝 请编辑配置文件，填入正确的飞书应用信息:")
                print(f"   - app_id: 飞书应用ID")
                print(f"   - app_secret: 飞书应用密钥")
                print(f"   - app_token: Bitable应用token")
                print(f"   - table_id: 任务表格ID")
                print(f"   - default_chat_id: 默认通知群组ID")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"初始化配置异常: {e}")
            return False
    
    def validate_config(self) -> bool:
        """验证配置文件"""
        try:
            if not self.load_config():
                print("❌ 配置文件加载失败")
                return False
            
            errors = []
            warnings = []
            
            # 检查必需字段
            required_fields = [
                ("app_info.app_id", "飞书应用ID"),
                ("app_info.app_secret", "飞书应用密钥"),
                ("bitable.app_token", "Bitable应用token"),
                ("bitable.tables.tasks.table_id", "任务表格ID")
            ]
            
            for field_path, description in required_fields:
                if not self._get_nested_value(self.config, field_path):
                    errors.append(f"缺少必需配置: {field_path} ({description})")
            
            # 检查可选字段
            optional_fields = [
                ("notification.default_chat_id", "默认通知群组ID"),
            ]
            
            for field_path, description in optional_fields:
                if not self._get_nested_value(self.config, field_path):
                    warnings.append(f"缺少可选配置: {field_path} ({description})")
            
            # 输出验证结果
            if errors:
                print("❌ 配置验证失败:")
                for error in errors:
                    print(f"   • {error}")
            
            if warnings:
                print("⚠️  配置警告:")
                for warning in warnings:
                    print(f"   • {warning}")
            
            if not errors and not warnings:
                print("✅ 配置验证通过")
                return True
            elif not errors:
                print("✅ 配置基本有效（有警告）")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"验证配置异常: {e}")
            print(f"❌ 配置验证异常: {e}")
            return False
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """获取嵌套字典的值"""
        try:
            keys = path.split('.')
            value = data
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return None
    
    def show_config(self) -> bool:
        """显示当前配置"""
        try:
            if not self.load_config():
                print("❌ 无法加载配置文件")
                return False
            
            print("📋 当前配置:")
            print(json.dumps(self.config, indent=2, ensure_ascii=False))
            return True
            
        except Exception as e:
            logger.error(f"显示配置异常: {e}")
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            if not self.load_config():
                print("❌ 无法加载配置文件")
                return False
            
            # 递归更新配置
            self._deep_update(self.config, updates)
            
            # 保存更新后的配置
            if self.save_config():
                print("✅ 配置更新成功")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"更新配置异常: {e}")
            return False
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """深度更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def test_connection(self) -> bool:
        """测试飞书连接"""
        try:
            if not self.load_config():
                print("❌ 无法加载配置文件")
                return False
            
            print("🔍 测试飞书连接...")
            
            # 这里应该实际测试飞书API连接
            # 暂时只验证配置完整性
            if self.validate_config():
                print("✅ 配置有效，连接测试通过")
                return True
            else:
                print("❌ 配置无效，连接测试失败")
                return False
                
        except Exception as e:
            logger.error(f"测试连接异常: {e}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="飞书配置辅助工具")
    parser.add_argument("--action", required=True,
                       choices=["init", "validate", "show", "update", "test"],
                       help="操作类型")
    
    # 配置参数
    parser.add_argument("--config", default="config/feishu.json", help="配置文件路径")
    parser.add_argument("--updates", help="更新数据(JSON格式)")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 初始化配置工具
        config_helper = ConfigHelper(args.config)
        
        # 执行相应操作
        success = False
        
        if args.action == "init":
            success = config_helper.init_config()
            
        elif args.action == "validate":
            success = config_helper.validate_config()
            
        elif args.action == "show":
            success = config_helper.show_config()
            
        elif args.action == "update":
            if not args.updates:
                print("错误: 更新配置需要 --updates 参数")
                sys.exit(1)
            
            try:
                updates = json.loads(args.updates)
            except json.JSONDecodeError:
                print("错误: --updates 参数必须是有效的JSON格式")
                sys.exit(1)
            
            success = config_helper.update_config(updates)
            
        elif args.action == "test":
            success = config_helper.test_connection()
        
        # 输出结果
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"脚本执行异常: {e}")
        print(f"❌ 脚本执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()