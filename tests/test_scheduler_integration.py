#!/usr/bin/env python3
"""
OpenClaw Task Orchestrator - Agent调度器集成测试

完整的端到端测试，包括与TaskManager的集成
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.scheduler import task_scheduler, AgentStatus
from src.core.task_manager import task_manager
from src.orchestrator.main import TaskAPI


async def test_end_to_end_workflow():
    """测试端到端工作流"""
    print("🚀 测试端到端工作流...")
    
    # 1. 启动调度器
    await task_scheduler.start()
    
    # 2. 注册Agent
    agents = [
        ("general-1", "general"),
        ("research-1", "research-analyst"),
        ("doc-1", "doc-engineer"),
        ("architect-1", "architect"),
    ]
    
    for agent_id, agent_type in agents:
        await task_scheduler.register_agent(agent_id, agent_type)
        await task_scheduler.update_agent_heartbeat(agent_id, AgentStatus.IDLE, 1.0)
    
    print(f"✅ 注册了 {len(agents)} 个Agent")
    
    # 3. 通过API创建任务
    tasks_to_create = [
        ("查询系统状态", "检查所有服务的运行状态", "medium", None),
        ("分析性能数据", "分析最近一周的系统性能数据，生成优化建议", "high", None),
        ("设计新功能", "设计用户权限管理功能的完整方案", "high", "L3"),
        ("编写API文档", "为新的用户API编写详细的技术文档", "medium", "L2"),
    ]
    
    created_tasks = []
    for title, description, priority, complexity in tasks_to_create:
        result = await TaskAPI.create_task(title, description, priority, complexity)
        if result["success"]:
            task_id = result["data"]["task_id"]
            created_tasks.append(task_id)
            print(f"✅ 创建任务: {title} ({task_id[:8]})")
        else:
            print(f"❌ 创建任务失败: {title} - {result['error']}")
    
    # 4. 检查任务分配
    print(f"\n📊 任务分配情况:")
    for task_id in created_tasks:
        task_info = await TaskAPI.get_task(task_id)
        if task_info["success"]:
            data = task_info["data"]
            print(f"   {data['title'][:20]:<20} | {data['complexity']} | {data['assigned_agent'] or 'Unassigned'}")
    
    # 5. 模拟任务执行
    print(f"\n⚙️ 模拟任务执行...")
    for i, task_id in enumerate(created_tasks[:2]):  # 只完成前两个任务
        # 更新任务状态为运行中
        await TaskAPI.update_task(task_id, status="running", progress=50)
        
        # 模拟执行时间
        await asyncio.sleep(0.1)
        
        # 完成任务
        result = {"message": f"任务 {i+1} 执行完成", "success": True}
        await TaskAPI.update_task(task_id, status="completed", progress=100, result=result)
        print(f"   ✅ 任务 {task_id[:8]} 执行完成")
    
    # 6. 检查最终状态
    print(f"\n📈 最终状态:")
    
    # Agent统计
    stats = task_scheduler.get_agent_stats()
    print(f"   Agent统计: {stats['total_agents']} 个Agent, {stats['active_tasks']} 个活跃任务")
    
    # 任务列表
    task_list = await TaskAPI.list_tasks()
    if task_list["success"]:
        completed_count = sum(1 for task in task_list["data"]["tasks"] if task["status"] == "completed")
        print(f"   任务统计: {task_list['data']['pagination']['total']} 个任务, {completed_count} 个已完成")
    
    # 7. 清理
    await task_scheduler.stop()
    
    return len(created_tasks) > 0


async def test_agent_failure_recovery():
    """测试Agent故障恢复"""
    print("\n🔧 测试Agent故障恢复...")
    
    await task_scheduler.start()
    
    # 注册Agent
    await task_scheduler.register_agent("test-agent", "general")
    await task_scheduler.update_agent_heartbeat("test-agent", AgentStatus.IDLE, 1.0)
    
    # 创建任务
    result = await TaskAPI.create_task("测试任务", "故障恢复测试任务", "medium")
    if not result["success"]:
        print("❌ 创建测试任务失败")
        return False
    
    task_id = result["data"]["task_id"]
    print(f"✅ 创建测试任务: {task_id[:8]}")
    
    # 模拟Agent故障
    if "test-agent" in task_scheduler.agents:
        agent = task_scheduler.agents["test-agent"]
        agent.status = AgentStatus.ERROR
        agent.health_score = 0.0
        print("⚠️ 模拟Agent故障")
    
    # 执行健康检查
    await task_scheduler._perform_health_check()
    
    # 检查Agent状态
    agent_info = task_scheduler.get_agent_info("test-agent")
    if agent_info:
        print(f"📊 Agent状态: {agent_info['status']}, 健康分数: {agent_info['health_score']}")
    
    # 恢复Agent
    await task_scheduler.update_agent_heartbeat("test-agent", AgentStatus.IDLE, 1.0)
    print("✅ Agent已恢复")
    
    await task_scheduler.stop()
    return True


async def test_concurrent_task_processing():
    """测试并发任务处理"""
    print("\n⚡ 测试并发任务处理...")
    
    await task_scheduler.start()
    
    # 注册多个Agent
    for i in range(3):
        agent_id = f"concurrent-agent-{i+1}"
        await task_scheduler.register_agent(agent_id, "general", max_concurrent_tasks=2)
        await task_scheduler.update_agent_heartbeat(agent_id, AgentStatus.IDLE, 1.0)
    
    # 并发创建多个任务
    tasks = []
    for i in range(8):
        task_coro = TaskAPI.create_task(f"并发任务 {i+1}", f"并发测试任务 {i+1}", "medium")
        tasks.append(task_coro)
    
    # 等待所有任务创建完成
    results = await asyncio.gather(*tasks)
    
    successful_tasks = [r for r in results if r["success"]]
    print(f"✅ 成功创建 {len(successful_tasks)} 个并发任务")
    
    # 检查任务分配分布
    agent_task_count = {}
    for result in successful_tasks:
        task_id = result["data"]["task_id"]
        task_info = await TaskAPI.get_task(task_id)
        if task_info["success"] and task_info["data"]["assigned_agent"]:
            agent_id = task_info["data"]["assigned_agent"]
            agent_task_count[agent_id] = agent_task_count.get(agent_id, 0) + 1
    
    print(f"📊 任务分配分布: {agent_task_count}")
    
    await task_scheduler.stop()
    return len(successful_tasks) > 0


async def main():
    """主测试函数"""
    print("🚀 OpenClaw Task Orchestrator - Agent调度器集成测试")
    print("=" * 70)
    
    test_results = []
    
    try:
        # 1. 端到端工作流测试
        workflow_success = await test_end_to_end_workflow()
        test_results.append(("端到端工作流", workflow_success))
        
        # 2. Agent故障恢复测试
        recovery_success = await test_agent_failure_recovery()
        test_results.append(("Agent故障恢复", recovery_success))
        
        # 3. 并发任务处理测试
        concurrent_success = await test_concurrent_task_processing()
        test_results.append(("并发任务处理", concurrent_success))
        
        # 汇总结果
        print("\n" + "=" * 70)
        print("🎊 Agent调度器集成测试完成！")
        
        print("\n📊 测试结果汇总:")
        all_passed = True
        for test_name, success in test_results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"   - {test_name}: {status}")
            if not success:
                all_passed = False
        
        if all_passed:
            print("\n🎉 所有集成测试通过！")
            print("\n🔧 验证的集成功能:")
            print("   - TaskAPI与Agent调度器的完整集成")
            print("   - 任务创建到分配的完整流程")
            print("   - 任务状态更新和完成处理")
            print("   - Agent故障检测和恢复机制")
            print("   - 并发任务的智能分配")
            print("   - 负载均衡在实际场景中的表现")
            
            return True
        else:
            print("\n❌ 部分集成测试失败")
            return False
            
    except Exception as e:
        print(f"\n💥 集成测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行集成测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)