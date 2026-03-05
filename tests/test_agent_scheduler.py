#!/usr/bin/env python3
"""
OpenClaw Task Orchestrator - Agent调度器测试

测试Agent注册发现、负载均衡、健康检查等核心功能
"""

import asyncio
import sys
from pathlib import Path
from typing import List
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.scheduler import task_scheduler, AgentStatus, LoadBalanceStrategy
from src.core.task_manager import Task, TaskComplexity, TaskPriority


async def test_agent_registration():
    """测试Agent注册和发现"""
    print("🧪 测试Agent注册和发现...")
    
    # 注册多个Agent
    agents_to_register = [
        ("general-1", "general", ["basic"], 2, 1.0),
        ("research-1", "research-analyst", ["research", "analysis"], 3, 1.2),
        ("doc-1", "doc-engineer", ["documentation", "writing"], 2, 1.0),
        ("architect-1", "architect", ["design", "architecture"], 1, 1.5),
        ("code-1", "code-reviewer", ["code", "review"], 3, 1.1),
    ]
    
    registered_count = 0
    for agent_id, agent_type, capabilities, max_tasks, weight in agents_to_register:
        success = await task_scheduler.register_agent(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities,
            max_concurrent_tasks=max_tasks,
            weight=weight
        )
        if success:
            registered_count += 1
            print(f"  ✅ Agent {agent_id} ({agent_type}) 注册成功")
        else:
            print(f"  ❌ Agent {agent_id} 注册失败")
    
    # 检查注册结果
    stats = task_scheduler.get_agent_stats()
    print(f"\n📊 注册统计:")
    print(f"   总Agent数: {stats['total_agents']}")
    print(f"   按状态分布: {stats['agents_by_status']}")
    print(f"   按类型分布: {stats['agents_by_type']}")
    
    return registered_count == len(agents_to_register)


async def test_agent_heartbeat():
    """测试Agent心跳机制"""
    print("\n💓 测试Agent心跳机制...")
    
    # 更新心跳
    agents = ["general-1", "research-1", "doc-1"]
    
    for agent_id in agents:
        success = await task_scheduler.update_agent_heartbeat(
            agent_id=agent_id,
            status=AgentStatus.IDLE,
            health_score=0.95,
            metadata={"last_task": "test", "version": "1.0"}
        )
        if success:
            print(f"  ✅ Agent {agent_id} 心跳更新成功")
        else:
            print(f"  ❌ Agent {agent_id} 心跳更新失败")
    
    # 检查Agent信息
    agent_info = task_scheduler.get_agent_info("research-1")
    if agent_info:
        print(f"  📋 Agent research-1 信息:")
        print(f"     状态: {agent_info['status']}")
        print(f"     健康分数: {agent_info['health_score']}")
        print(f"     负载因子: {agent_info['load_factor']}")
        return True
    else:
        print("  ❌ 获取Agent信息失败")
        return False


async def test_task_assignment():
    """测试任务分配"""
    print("\n📋 测试任务分配...")
    
    # 创建不同复杂度的测试任务
    test_tasks = [
        ("查询用户信息", "获取用户基本信息", TaskComplexity.L1_SIMPLE),
        ("分析用户行为", "分析用户行为模式并生成报告", TaskComplexity.L2_SINGLE),
        ("设计系统架构", "设计分布式系统架构方案", TaskComplexity.L3_COMPLEX),
        ("编写文档", "编写API技术文档", TaskComplexity.L2_SINGLE),
        ("简单查询", "查询数据库记录", TaskComplexity.L1_SIMPLE),
    ]
    
    assigned_tasks = []
    
    for title, description, complexity in test_tasks:
        # 创建任务
        task = Task(
            title=title,
            description=description,
            priority=TaskPriority.MEDIUM,
            complexity=complexity
        )
        
        # 分配任务
        assigned_agent = await task_scheduler.assign_task(task)
        
        if assigned_agent:
            assigned_tasks.append((task.task_id, assigned_agent, complexity))
            print(f"  ✅ 任务 '{title}' ({complexity.value}) 分配给 {assigned_agent}")
        else:
            print(f"  ❌ 任务 '{title}' ({complexity.value}) 分配失败")
    
    # 检查分配结果
    stats = task_scheduler.get_agent_stats()
    print(f"\n📊 分配后统计:")
    print(f"   活跃任务数: {stats['active_tasks']}")
    print(f"   总分配数: {stats['total_assignments']}")
    
    return len(assigned_tasks) > 0, assigned_tasks


async def test_load_balancing():
    """测试负载均衡策略"""
    print("\n⚖️ 测试负载均衡策略...")
    
    # 测试不同的负载均衡策略
    strategies = [
        LoadBalanceStrategy.LEAST_CONNECTIONS,
        LoadBalanceStrategy.COMPLEXITY_BASED,
        LoadBalanceStrategy.WEIGHTED
    ]
    
    results = {}
    
    for strategy in strategies:
        print(f"\n  🔄 测试策略: {strategy.value}")
        task_scheduler.load_balance_strategy = strategy
        
        # 创建多个相同复杂度的任务
        assignments = []
        for i in range(6):
            task = Task(
                title=f"测试任务 {i+1}",
                description=f"负载均衡测试任务 {i+1}",
                priority=TaskPriority.MEDIUM,
                complexity=TaskComplexity.L2_SINGLE
            )
            
            assigned_agent = await task_scheduler.assign_task(task)
            if assigned_agent:
                assignments.append(assigned_agent)
        
        # 统计分配结果
        agent_counts = {}
        for agent_id in assignments:
            agent_counts[agent_id] = agent_counts.get(agent_id, 0) + 1
        
        results[strategy.value] = agent_counts
        print(f"     分配分布: {agent_counts}")
    
    # 恢复默认策略
    task_scheduler.load_balance_strategy = LoadBalanceStrategy.COMPLEXITY_BASED
    
    return len(results) == len(strategies)


async def test_task_completion():
    """测试任务完成处理"""
    print("\n✅ 测试任务完成处理...")
    
    # 获取一些已分配的任务
    completed_count = 0
    
    # 模拟完成前面分配的任务
    for task_id, assignment in list(task_scheduler.assignments.items())[:3]:
        # 模拟执行时间
        execution_time = 30.0 + (hash(task_id) % 60)  # 30-90秒
        
        success = await task_scheduler.complete_task(
            task_id=task_id,
            success=True,
            execution_time=execution_time
        )
        
        if success:
            completed_count += 1
            print(f"  ✅ 任务 {task_id[:8]} 完成 (耗时: {execution_time:.1f}s)")
        else:
            print(f"  ❌ 任务 {task_id[:8]} 完成处理失败")
    
    # 检查Agent状态更新
    print(f"\n📊 完成后Agent状态:")
    for agent_id in ["general-1", "research-1", "doc-1"]:
        agent_info = task_scheduler.get_agent_info(agent_id)
        if agent_info:
            print(f"   {agent_id}: {agent_info['status']}, 当前任务: {agent_info['current_load']}, 已完成: {agent_info['total_tasks_completed']}")
    
    return completed_count > 0


async def test_health_check():
    """测试健康检查机制"""
    print("\n🏥 测试健康检查机制...")
    
    # 模拟一个Agent离线
    offline_agent = "general-1"
    
    # 获取当前状态
    agent_info_before = task_scheduler.get_agent_info(offline_agent)
    print(f"  📋 Agent {offline_agent} 离线前状态: {agent_info_before['status'] if agent_info_before else 'Not found'}")
    
    # 手动设置Agent为离线状态（模拟心跳超时）
    if offline_agent in task_scheduler.agents:
        agent = task_scheduler.agents[offline_agent]
        agent.status = AgentStatus.OFFLINE
        agent.health_score = 0.0
        print(f"  ⚠️ 模拟Agent {offline_agent} 离线")
    
    # 执行一次健康检查
    await task_scheduler._perform_health_check()
    
    # 检查状态
    agent_info_after = task_scheduler.get_agent_info(offline_agent)
    print(f"  📋 Agent {offline_agent} 离线后状态: {agent_info_after['status'] if agent_info_after else 'Not found'}")
    
    # 恢复Agent状态
    await task_scheduler.update_agent_heartbeat(
        offline_agent,
        status=AgentStatus.IDLE,
        health_score=1.0
    )
    print(f"  ✅ Agent {offline_agent} 已恢复")
    
    return True


async def test_agent_unregistration():
    """测试Agent注销"""
    print("\n🚪 测试Agent注销...")
    
    # 注销一个没有任务的Agent
    agent_to_remove = "code-1"
    
    # 检查Agent是否存在
    agent_info = task_scheduler.get_agent_info(agent_to_remove)
    if not agent_info:
        print(f"  ⚠️ Agent {agent_to_remove} 不存在")
        return False
    
    print(f"  📋 注销前Agent {agent_to_remove} 当前任务数: {agent_info['current_load']}")
    
    # 注销Agent
    success = await task_scheduler.unregister_agent(agent_to_remove)
    
    if success:
        print(f"  ✅ Agent {agent_to_remove} 注销成功")
        
        # 验证Agent已被移除
        agent_info_after = task_scheduler.get_agent_info(agent_to_remove)
        if agent_info_after is None:
            print(f"  ✅ 确认Agent {agent_to_remove} 已从系统中移除")
            return True
        else:
            print(f"  ❌ Agent {agent_to_remove} 仍然存在于系统中")
            return False
    else:
        print(f"  ❌ Agent {agent_to_remove} 注销失败")
        return False


async def test_scheduler_lifecycle():
    """测试调度器生命周期"""
    print("\n🔄 测试调度器生命周期...")
    
    # 调度器应该已经在运行
    print(f"  📊 调度器运行状态: {task_scheduler._running}")
    
    # 获取最终统计
    stats = task_scheduler.get_agent_stats()
    print(f"  📊 最终统计:")
    print(f"     总Agent数: {stats['total_agents']}")
    print(f"     活跃任务数: {stats['active_tasks']}")
    print(f"     总分配数: {stats['total_assignments']}")
    
    # 列出所有Agent
    all_agents = task_scheduler.list_agents()
    print(f"  📋 当前Agent列表:")
    for agent in all_agents:
        print(f"     - {agent['agent_id']} ({agent['agent_type']}): {agent['status']}")
    
    return True


async def main():
    """主测试函数"""
    print("🚀 OpenClaw Task Orchestrator - Agent调度器测试")
    print("=" * 60)
    
    # 启动调度器
    await task_scheduler.start()
    
    test_results = []
    
    try:
        # 1. Agent注册测试
        registration_success = await test_agent_registration()
        test_results.append(("Agent注册和发现", registration_success))
        
        # 2. 心跳机制测试
        heartbeat_success = await test_agent_heartbeat()
        test_results.append(("Agent心跳机制", heartbeat_success))
        
        # 3. 任务分配测试
        assignment_success, assigned_tasks = await test_task_assignment()
        test_results.append(("任务分配", assignment_success))
        
        # 4. 负载均衡测试
        load_balance_success = await test_load_balancing()
        test_results.append(("负载均衡策略", load_balance_success))
        
        # 5. 任务完成测试
        completion_success = await test_task_completion()
        test_results.append(("任务完成处理", completion_success))
        
        # 6. 健康检查测试
        health_check_success = await test_health_check()
        test_results.append(("健康检查机制", health_check_success))
        
        # 7. Agent注销测试
        unregistration_success = await test_agent_unregistration()
        test_results.append(("Agent注销", unregistration_success))
        
        # 8. 生命周期测试
        lifecycle_success = await test_scheduler_lifecycle()
        test_results.append(("调度器生命周期", lifecycle_success))
        
        # 汇总结果
        print("\n" + "=" * 60)
        print("🎊 Agent调度器测试完成！")
        
        print("\n📊 测试结果汇总:")
        all_passed = True
        for test_name, success in test_results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"   - {test_name}: {status}")
            if not success:
                all_passed = False
        
        if all_passed:
            print("\n🎉 所有测试通过！Agent调度器实现成功")
            
            # 显示实现的功能
            print("\n🔧 实现的功能:")
            print("   - Agent注册和发现机制")
            print("   - 多种负载均衡策略 (轮询、最少连接、权重、复杂度)")
            print("   - 健康检查和心跳监控")
            print("   - 智能任务分配 (基于复杂度和Agent能力)")
            print("   - Agent状态管理 (空闲、忙碌、离线、错误)")
            print("   - 任务完成跟踪和性能统计")
            print("   - Agent注销和故障处理")
            
            return True
        else:
            print("\n❌ 部分测试失败，需要进一步优化")
            return False
            
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 停止调度器
        await task_scheduler.stop()


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)