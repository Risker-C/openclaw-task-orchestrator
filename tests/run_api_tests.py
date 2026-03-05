#!/usr/bin/env python3
"""
OpenClaw Task Orchestrator - API测试运行器

运行基础任务管理API的功能测试
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator.main import TaskAPI
from src.core.task_manager import task_manager


async def test_basic_crud_operations():
    """测试基础CRUD操作"""
    print("🧪 开始测试基础任务管理API...")
    
    # 清空任务管理器
    task_manager.tasks.clear()
    
    # 1. 测试创建任务
    print("\n1️⃣ 测试创建任务...")
    create_result = await TaskAPI.create_task(
        title="测试任务",
        description="这是一个API测试任务，用于验证基础功能",
        priority="high",
        complexity="L2"
    )
    
    if create_result["success"]:
        task_id = create_result["data"]["task_id"]
        print(f"✅ 任务创建成功: {task_id}")
        print(f"   状态: {create_result['data']['status']}")
        print(f"   复杂度: {create_result['data']['complexity']}")
    else:
        print(f"❌ 任务创建失败: {create_result['error']}")
        return False
    
    # 2. 测试获取任务
    print("\n2️⃣ 测试获取任务...")
    get_result = await TaskAPI.get_task(task_id)
    
    if get_result["success"]:
        task_data = get_result["data"]
        print(f"✅ 任务获取成功:")
        print(f"   标题: {task_data['title']}")
        print(f"   描述: {task_data['description'][:50]}...")
        print(f"   状态: {task_data['status']}")
        print(f"   进度: {task_data['progress']}%")
    else:
        print(f"❌ 任务获取失败: {get_result['error']}")
        return False
    
    # 3. 测试更新任务
    print("\n3️⃣ 测试更新任务...")
    update_result = await TaskAPI.update_task(
        task_id,
        title="更新后的测试任务",
        status="running",
        progress=50
    )
    
    if update_result["success"]:
        print(f"✅ 任务更新成功:")
        print(f"   更新字段: {update_result['data']['updated_fields']}")
        
        # 验证更新结果
        get_result = await TaskAPI.get_task(task_id)
        if get_result["success"]:
            task_data = get_result["data"]
            print(f"   新标题: {task_data['title']}")
            print(f"   新状态: {task_data['status']}")
            print(f"   新进度: {task_data['progress']}%")
    else:
        print(f"❌ 任务更新失败: {update_result['error']}")
        return False
    
    # 4. 测试创建更多任务用于列表测试
    print("\n4️⃣ 创建更多测试任务...")
    for i in range(3):
        await TaskAPI.create_task(
            title=f"批量测试任务 {i+1}",
            description=f"这是第{i+1}个批量测试任务",
            priority=["low", "medium", "high"][i % 3],
            complexity=["L1", "L2", "L3"][i % 3]
        )
    print("✅ 批量任务创建完成")
    
    # 5. 测试列出任务
    print("\n5️⃣ 测试列出任务...")
    list_result = await TaskAPI.list_tasks()
    
    if list_result["success"]:
        tasks = list_result["data"]["tasks"]
        pagination = list_result["data"]["pagination"]
        print(f"✅ 任务列表获取成功:")
        print(f"   总任务数: {pagination['total']}")
        print(f"   当前页任务数: {len(tasks)}")
        
        for task in tasks[:3]:  # 只显示前3个
            print(f"   - {task['title']} ({task['status']}, {task['priority']})")
    else:
        print(f"❌ 任务列表获取失败: {list_result['error']}")
        return False
    
    # 6. 测试过滤功能
    print("\n6️⃣ 测试过滤功能...")
    filter_result = await TaskAPI.list_tasks(priority="high")
    
    if filter_result["success"]:
        high_priority_tasks = filter_result["data"]["tasks"]
        print(f"✅ 高优先级任务过滤成功: {len(high_priority_tasks)} 个任务")
        for task in high_priority_tasks:
            print(f"   - {task['title']} (优先级: {task['priority']})")
    else:
        print(f"❌ 任务过滤失败: {filter_result['error']}")
        return False
    
    # 7. 测试分页功能
    print("\n7️⃣ 测试分页功能...")
    page_result = await TaskAPI.list_tasks(limit=2, offset=0)
    
    if page_result["success"]:
        pagination = page_result["data"]["pagination"]
        print(f"✅ 分页功能测试成功:")
        print(f"   第一页任务数: {len(page_result['data']['tasks'])}")
        print(f"   是否有更多: {pagination['has_more']}")
        print(f"   总数: {pagination['total']}")
    else:
        print(f"❌ 分页功能测试失败: {page_result['error']}")
        return False
    
    # 8. 测试删除任务（先完成运行中的任务）
    print("\n8️⃣ 测试删除任务...")
    
    # 先将运行中的任务标记为完成
    await TaskAPI.update_task(task_id, status="completed", progress=100)
    
    delete_result = await TaskAPI.delete_task(task_id)
    
    if delete_result["success"]:
        print(f"✅ 任务删除成功: {delete_result['data']['task_id']}")
        
        # 验证任务已删除
        get_result = await TaskAPI.get_task(task_id)
        if not get_result["success"] and get_result["error_code"] == "TASK_NOT_FOUND":
            print("✅ 删除验证成功: 任务已不存在")
        else:
            print("❌ 删除验证失败: 任务仍然存在")
            return False
    else:
        print(f"❌ 任务删除失败: {delete_result['error']}")
        return False
    
    print("\n🎉 所有基础CRUD操作测试通过！")
    return True


async def test_validation_and_error_handling():
    """测试数据验证和错误处理"""
    print("\n🔍 开始测试数据验证和错误处理...")
    
    # 测试创建任务的验证错误
    print("\n1️⃣ 测试输入验证...")
    
    # 空标题
    result = await TaskAPI.create_task("", "描述")
    if not result["success"] and result["error_code"] == "VALIDATION_ERROR":
        print("✅ 空标题验证通过")
    else:
        print("❌ 空标题验证失败")
        return False
    
    # 无效优先级
    result = await TaskAPI.create_task("标题", "描述", priority="invalid")
    if not result["success"] and result["error_code"] == "INVALID_PRIORITY":
        print("✅ 无效优先级验证通过")
    else:
        print("❌ 无效优先级验证失败")
        return False
    
    # 无效复杂度
    result = await TaskAPI.create_task("标题", "描述", complexity="L4")
    if not result["success"] and result["error_code"] == "INVALID_COMPLEXITY":
        print("✅ 无效复杂度验证通过")
    else:
        print("❌ 无效复杂度验证失败")
        return False
    
    # 测试获取不存在的任务
    print("\n2️⃣ 测试错误处理...")
    result = await TaskAPI.get_task("00000000-0000-0000-0000-000000000000")
    if not result["success"] and result["error_code"] == "TASK_NOT_FOUND":
        print("✅ 任务不存在错误处理通过")
    else:
        print("❌ 任务不存在错误处理失败")
        return False
    
    # 测试无效任务ID格式
    result = await TaskAPI.get_task("invalid-id")
    if not result["success"] and result["error_code"] == "VALIDATION_ERROR":
        print("✅ 无效任务ID格式验证通过")
    else:
        print("❌ 无效任务ID格式验证失败")
        return False
    
    print("\n🎉 所有验证和错误处理测试通过！")
    return True


async def main():
    """主测试函数"""
    print("🚀 OpenClaw Task Orchestrator - API功能测试")
    print("=" * 50)
    
    try:
        # 运行基础CRUD测试
        crud_success = await test_basic_crud_operations()
        
        if crud_success:
            # 运行验证和错误处理测试
            validation_success = await test_validation_and_error_handling()
            
            if validation_success:
                print("\n" + "=" * 50)
                print("🎊 所有测试通过！基础任务管理API功能正常")
                print("\n📊 测试统计:")
                print(f"   - CRUD操作: ✅ 通过")
                print(f"   - 数据验证: ✅ 通过")
                print(f"   - 错误处理: ✅ 通过")
                print(f"   - 分页功能: ✅ 通过")
                print(f"   - 过滤功能: ✅ 通过")
                
                # 显示最终任务状态
                final_list = await TaskAPI.list_tasks()
                if final_list["success"]:
                    remaining_tasks = len(final_list["data"]["tasks"])
                    print(f"\n📋 测试完成后剩余任务数: {remaining_tasks}")
                
                return True
            else:
                print("\n❌ 验证和错误处理测试失败")
                return False
        else:
            print("\n❌ 基础CRUD操作测试失败")
            return False
            
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)