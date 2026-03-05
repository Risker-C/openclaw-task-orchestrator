#!/usr/bin/env python3
"""
飞书Bitable初始化脚本

创建任务管理所需的Bitable表结构和字段
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def init_bitable():
    """初始化飞书Bitable表结构"""
    print("🚀 开始初始化飞书Bitable表结构...")
    
    try:
        # 加载配置
        config_path = project_root / "config" / "feishu.json"
        if not config_path.exists():
            config_path = project_root / "config" / "feishu.example.json"
            print("⚠️  使用示例配置文件，请更新 config/feishu.json")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        app_token = config.get('app_token')
        if not app_token or app_token.startswith('your_'):
            print("❌ 请在 config/feishu.json 中配置正确的 app_token")
            return False
        
        # 检查是否已有表配置
        table_config = config.get('table_configs', {}).get('tasks', {})
        table_id = table_config.get('table_id')
        
        if table_id and not table_id.startswith('your_'):
            print(f"✅ 任务表已配置: {table_id}")
            return True
        
        print("📋 需要创建任务表...")
        print("\n请按照以下步骤手动创建Bitable表：")
        print("\n1. 打开飞书，进入多维表格应用")
        print(f"2. 使用app_token: {app_token}")
        print("3. 创建新表格，命名为 '任务管理'")
        print("4. 添加以下字段：")
        
        fields = [
            ("任务ID", "单行文本", "主键，唯一标识"),
            ("任务标题", "单行文本", "任务的简短标题"),
            ("任务描述", "多行文本", "详细的任务描述"),
            ("复杂度", "单选", "L1/L2/L3"),
            ("状态", "单选", "待处理/分析中/就绪/执行中/审查中/已完成/失败/已取消"),
            ("优先级", "单选", "低/中/高/紧急"),
            ("分配Agent", "单行文本", "执行任务的Agent"),
            ("创建时间", "日期", "任务创建时间"),
            ("更新时间", "日期", "最后更新时间"),
            ("进度百分比", "数字", "0-100的进度"),
            ("Token消耗", "数字", "执行消耗的Token数量"),
            ("结果文档", "单行文本", "结果文档的token"),
            ("Wiki节点", "单行文本", "归档的Wiki节点token")
        ]
        
        for i, (name, type_name, desc) in enumerate(fields, 1):
            print(f"   {i:2d}. {name:<12} ({type_name:<8}) - {desc}")
        
        print("\n5. 创建看板视图：")
        print("   - 按 '状态' 字段分组")
        print("   - 设置为默认视图")
        print("   - 启用拖拽功能")
        
        print("\n6. 获取表格ID并更新配置：")
        print("   - 复制表格URL中的table_id")
        print("   - 更新 config/feishu.json 中的 table_id")
        
        print("\n7. 可选：配置通知")
        print("   - 创建或选择通知群组")
        print("   - 获取chat_id并更新配置")
        
        print("\n✨ 手动创建完成后，请重新运行此脚本验证配置")
        return False
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False


async def verify_bitable():
    """验证Bitable配置"""
    print("🔍 验证Bitable配置...")
    
    try:
        config_path = project_root / "config" / "feishu.json"
        if not config_path.exists():
            print("❌ 配置文件不存在: config/feishu.json")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查必要配置
        required_fields = ['app_id', 'app_secret', 'app_token']
        for field in required_fields:
            value = config.get(field)
            if not value or value.startswith('your_'):
                print(f"❌ 请配置 {field}")
                return False
        
        # 检查表配置
        table_config = config.get('table_configs', {}).get('tasks', {})
        table_id = table_config.get('table_id')
        
        if not table_id or table_id.startswith('your_'):
            print("❌ 请配置 tasks.table_id")
            return False
        
        print("✅ 基础配置验证通过")
        
        # TODO: 这里应该调用OpenClaw的feishu工具验证表是否存在
        # 暂时跳过实际验证
        print("⚠️  实际表验证跳过（需要OpenClaw环境）")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


async def main():
    """主函数"""
    print("🎯 OpenClaw Task Orchestrator - Bitable初始化工具")
    print("=" * 50)
    
    # 检查配置文件
    config_path = project_root / "config" / "feishu.json"
    if config_path.exists():
        # 验证现有配置
        if await verify_bitable():
            print("\n🎉 Bitable配置验证成功！")
            print("可以启动任务编排器了：python src/orchestrator/main.py")
        else:
            print("\n❌ 配置验证失败，请检查配置")
    else:
        # 初始化配置
        if not await init_bitable():
            print("\n📝 请按照上述步骤完成Bitable表创建")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    asyncio.run(main())