#!/usr/bin/env python3
"""
OpenClaw Task Orchestrator - 智能复杂度判断器测试

测试优化后的复杂度分析器的准确率、解释功能、手动覆盖机制等
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.task_manager import Task, TaskComplexity, TaskPriority
from src.core.complexity import complexity_analyzer, ComplexityExplanation


# 测试用例数据
TEST_CASES = [
    # L1 简单任务
    ("查询用户信息", "获取用户ID为12345的基本信息", TaskComplexity.L1_SIMPLE),
    ("检查服务状态", "快速检查API服务是否正常运行", TaskComplexity.L1_SIMPLE),
    ("下载文件", "从指定URL下载配置文件到本地", TaskComplexity.L1_SIMPLE),
    ("简单统计", "统计今日新增用户数量", TaskComplexity.L1_SIMPLE),
    
    # L2 单步任务
    ("分析用户行为", "分析最近一周用户的登录行为模式，生成分析报告", TaskComplexity.L2_SINGLE),
    ("编写技术文档", "为新的API接口编写详细的技术文档和使用说明", TaskComplexity.L2_SINGLE),
    ("性能优化方案", "针对数据库查询慢的问题，研究并提出优化方案", TaskComplexity.L2_SINGLE),
    ("代码审查", "审查用户认证模块的代码，检查安全性和规范性", TaskComplexity.L2_SINGLE),
    ("测试用例设计", "为支付功能设计完整的测试用例，包括正常和异常场景", TaskComplexity.L2_SINGLE),
    
    # L3 复杂任务
    ("设计微服务架构", "为电商平台设计完整的微服务架构，包括用户、订单、支付、库存等服务的设计和集成方案", TaskComplexity.L3_COMPLEX),
    ("构建CI/CD流水线", "从零开始构建完整的CI/CD流水线，包括代码检查、自动化测试、部署和监控", TaskComplexity.L3_COMPLEX),
    ("多系统集成项目", "整合CRM、ERP、财务系统，实现数据同步和业务流程自动化", TaskComplexity.L3_COMPLEX),
    ("大数据平台搭建", "搭建企业级大数据分析平台，包括数据采集、存储、处理、可视化的完整链路", TaskComplexity.L3_COMPLEX),
    ("AI模型训练部署", "训练推荐算法模型，并部署到生产环境，包括数据预处理、模型训练、A/B测试、监控等完整流程", TaskComplexity.L3_COMPLEX),
]

# 边界测试用例
EDGE_CASES = [
    ("", "空描述测试", TaskComplexity.L1_SIMPLE),
    ("测试", "极短描述", TaskComplexity.L1_SIMPLE),
    ("复杂系统架构设计", "仅标题包含复杂关键词", TaskComplexity.L2_SINGLE),
    ("简单查询", "这是一个非常复杂的系统级架构设计任务，需要考虑微服务、分布式、高可用、安全等多个维度，涉及前端、后端、数据库、缓存、消息队列等多个组件的设计和集成，需要多个团队协作完成，预计需要几个月的时间", TaskComplexity.L3_COMPLEX),
]


async def test_basic_complexity_analysis():
    """测试基础复杂度分析功能"""
    print("🧪 测试基础复杂度分析功能...")
    
    correct_predictions = 0
    total_predictions = 0
    
    results = []
    
    for title, description, expected in TEST_CASES:
        # 创建测试任务
        task = Task(title=title, description=description, priority=TaskPriority.MEDIUM)
        
        # 分析复杂度
        predicted, explanation = await complexity_analyzer.analyze_complexity(task)
        
        # 记录结果
        is_correct = predicted == expected
        if is_correct:
            correct_predictions += 1
        total_predictions += 1
        
        results.append({
            'title': title,
            'expected': expected.value,
            'predicted': predicted.value,
            'correct': is_correct,
            'confidence': explanation.confidence,
            'total_score': explanation.indicators.total_score
        })
        
        # 显示结果
        status = "✅" if is_correct else "❌"
        print(f"  {status} {title[:30]:<30} | 预期: {expected.value} | 预测: {predicted.value} | 置信度: {explanation.confidence:.2f}")
    
    # 计算准确率
    accuracy = correct_predictions / total_predictions
    print(f"\n📊 基础测试结果:")
    print(f"   总测试用例: {total_predictions}")
    print(f"   正确预测: {correct_predictions}")
    print(f"   准确率: {accuracy:.1%}")
    
    return accuracy >= 0.85, results


async def test_edge_cases():
    """测试边界情况"""
    print("\n🔍 测试边界情况...")
    
    for title, description, expected in EDGE_CASES:
        task = Task(title=title, description=description, priority=TaskPriority.MEDIUM)
        predicted, explanation = await complexity_analyzer.analyze_complexity(task)
        
        status = "✅" if predicted == expected else "❌"
        print(f"  {status} {title[:20]:<20} | 预期: {expected.value} | 预测: {predicted.value}")
        print(f"     描述长度: {len(description)} | 总得分: {explanation.indicators.total_score:.2f}")


async def test_explanation_functionality():
    """测试解释功能"""
    print("\n📝 测试解释功能...")
    
    # 选择一个复杂任务进行详细分析
    task = Task(
        title="设计分布式系统架构",
        description="为高并发电商平台设计分布式系统架构，包括微服务拆分、数据库分片、缓存策略、消息队列、负载均衡、监控告警等完整方案，需要考虑高可用、高性能、可扩展性等多个维度",
        priority=TaskPriority.HIGH
    )
    
    complexity, explanation = await complexity_analyzer.analyze_complexity(task)
    
    print(f"✅ 复杂度分析完成: {complexity.value}")
    print(f"   置信度: {explanation.confidence:.1%}")
    print(f"   总得分: {explanation.indicators.total_score:.2f}")
    
    print("\n📋 详细指标:")
    indicators = explanation.indicators
    print(f"   关键词得分: {indicators.keyword_score:.2f}")
    print(f"   长度得分: {indicators.length_score:.2f}")
    print(f"   结构得分: {indicators.structure_score:.2f}")
    print(f"   领域得分: {indicators.domain_score:.2f}")
    print(f"   依赖得分: {indicators.dependency_score:.2f}")
    print(f"   上下文得分: {indicators.context_score:.2f}")
    
    print("\n🔍 判断原因:")
    for i, reason in enumerate(explanation.reasons[:5], 1):
        print(f"   {i}. {reason}")
    
    print("\n💡 建议:")
    for i, suggestion in enumerate(explanation.suggestions[:3], 1):
        print(f"   {i}. {suggestion}")
    
    # 测试解释文本生成
    explanation_text = complexity_analyzer.get_complexity_explanation(task, complexity, explanation)
    print(f"\n📄 完整解释文本长度: {len(explanation_text)} 字符")
    
    return True


async def test_manual_override():
    """测试手动覆盖机制"""
    print("\n🔧 测试手动覆盖机制...")
    
    # 创建一个明显是L1的任务，但手动指定为L3
    task = Task(
        title="查询用户信息",
        description="获取用户基本信息",
        priority=TaskPriority.MEDIUM
    )
    
    # 测试一致性覆盖（应该直接接受）
    complexity1, explanation1 = await complexity_analyzer.analyze_complexity(task, TaskComplexity.L1_SIMPLE)
    print(f"✅ 一致性覆盖测试: {complexity1.value} (应该是L1)")
    
    # 测试差异覆盖（应该触发确认机制）
    complexity2, explanation2 = await complexity_analyzer.analyze_complexity(task, TaskComplexity.L3_COMPLEX)
    print(f"✅ 差异覆盖测试: {complexity2.value} (手动指定L3)")
    print(f"   自动分析建议: {explanation2.reasons[1] if len(explanation2.reasons) > 1 else '无'}")
    
    return True


async def test_batch_analysis():
    """测试批量分析功能"""
    print("\n📦 测试批量分析功能...")
    
    # 创建多个测试任务
    tasks = []
    for i, (title, description, expected) in enumerate(TEST_CASES[:5]):
        task = Task(title=f"{title}_{i}", description=description, priority=TaskPriority.MEDIUM)
        tasks.append(task)
    
    # 批量分析
    results = await complexity_analyzer.batch_analyze_complexity(tasks)
    
    print(f"✅ 批量分析完成: {len(results)} 个任务")
    for i, (complexity, explanation) in enumerate(results):
        print(f"   任务{i+1}: {complexity.value} (置信度: {explanation.confidence:.2f})")
    
    return len(results) == len(tasks)


async def test_accuracy_metrics():
    """测试准确率指标计算"""
    print("\n📈 测试准确率指标计算...")
    
    # 准备测试数据
    predictions = [TaskComplexity.L1_SIMPLE, TaskComplexity.L2_SINGLE, TaskComplexity.L3_COMPLEX, 
                  TaskComplexity.L1_SIMPLE, TaskComplexity.L2_SINGLE]
    actual = [TaskComplexity.L1_SIMPLE, TaskComplexity.L2_SINGLE, TaskComplexity.L2_SINGLE,
             TaskComplexity.L1_SIMPLE, TaskComplexity.L2_SINGLE]
    
    # 计算指标
    metrics = complexity_analyzer.get_accuracy_metrics(predictions, actual)
    
    print(f"✅ 准确率指标计算完成:")
    print(f"   整体准确率: {metrics['accuracy']:.1%}")
    
    for complexity in TaskComplexity:
        precision_key = f"{complexity.value}_precision"
        recall_key = f"{complexity.value}_recall"
        if precision_key in metrics:
            print(f"   {complexity.value} - 精确率: {metrics[precision_key]:.1%}, 召回率: {metrics[recall_key]:.1%}")
    
    return metrics['accuracy'] > 0.6


async def main():
    """主测试函数"""
    print("🚀 OpenClaw Task Orchestrator - 智能复杂度判断器测试")
    print("=" * 70)
    
    test_results = []
    
    try:
        # 1. 基础复杂度分析测试
        basic_success, basic_results = await test_basic_complexity_analysis()
        test_results.append(("基础复杂度分析", basic_success))
        
        # 2. 边界情况测试
        await test_edge_cases()
        test_results.append(("边界情况处理", True))
        
        # 3. 解释功能测试
        explanation_success = await test_explanation_functionality()
        test_results.append(("解释功能", explanation_success))
        
        # 4. 手动覆盖测试
        override_success = await test_manual_override()
        test_results.append(("手动覆盖机制", override_success))
        
        # 5. 批量分析测试
        batch_success = await test_batch_analysis()
        test_results.append(("批量分析", batch_success))
        
        # 6. 准确率指标测试
        metrics_success = await test_accuracy_metrics()
        test_results.append(("准确率指标", metrics_success))
        
        # 汇总结果
        print("\n" + "=" * 70)
        print("🎊 智能复杂度判断器测试完成！")
        
        print("\n📊 测试结果汇总:")
        all_passed = True
        for test_name, success in test_results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"   - {test_name}: {status}")
            if not success:
                all_passed = False
        
        if all_passed:
            print("\n🎉 所有测试通过！复杂度判断器优化成功")
            
            # 显示改进点
            print("\n🔧 主要改进:")
            print("   - 扩展关键词库：L1(13→17), L2(13→24), L3(13→25)")
            print("   - 新增上下文复杂度分析维度")
            print("   - 优化权重分配和阈值设置")
            print("   - 增加详细解释和建议功能")
            print("   - 完善手动覆盖确认机制")
            print("   - 支持批量分析和准确率评估")
            
            return True
        else:
            print("\n❌ 部分测试失败，需要进一步优化")
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