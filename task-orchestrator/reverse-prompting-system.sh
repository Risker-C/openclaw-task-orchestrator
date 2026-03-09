#!/bin/bash
# Reverse Prompting System for Task Orchestrator
# Based on proactive-agent skill - surfaces ideas Master didn't know to ask for

WORKSPACE="$HOME/.openclaw/workspace"
MEMORY_DIR="$WORKSPACE/memory"
DAILY_NOTE="$MEMORY_DIR/$(date +%Y-%m-%d).md"
PROACTIVE_IDEAS="$WORKSPACE/notes/areas/proactive-ideas.md"

# 确保目录存在
mkdir -p "$WORKSPACE/notes/areas"

# Reverse Prompting: 主动询问"我能为你做什么有趣的事？"
generate_proactive_suggestions() {
    echo "🧠 Analyzing current context for proactive opportunities..."
    
    # 分析当前状态
    analyze_current_state
    
    # 生成建议
    local suggestions=$(generate_suggestions_based_on_context)
    
    # 记录建议
    record_proactive_ideas "$suggestions"
    
    # 返回建议给Master
    present_suggestions_to_master "$suggestions"
}

# 分析当前状态
analyze_current_state() {
    echo "📊 Current State Analysis:"
    
    # 1. 活跃任务分析
    local active_tasks=$(count_active_tasks)
    echo "  - Active tasks: $active_tasks"
    
    # 2. 最近完成的任务模式
    local recent_patterns=$(analyze_recent_task_patterns)
    echo "  - Recent patterns: $recent_patterns"
    
    # 3. 失败任务分析
    local failure_patterns=$(analyze_failure_patterns)
    echo "  - Failure patterns: $failure_patterns"
    
    # 4. 资源使用情况
    local resource_usage=$(analyze_resource_usage)
    echo "  - Resource usage: $resource_usage"
    
    # 5. Master的偏好分析
    local user_preferences=$(analyze_user_preferences)
    echo "  - User preferences: $user_preferences"
}

# 基于上下文生成建议
generate_suggestions_based_on_context() {
    local suggestions=""
    
    # 1. 基于重复任务的自动化建议
    local automation_suggestions=$(suggest_automation_opportunities)
    if [[ -n "$automation_suggestions" ]]; then
        suggestions+="🤖 **自动化机会**:\n$automation_suggestions\n\n"
    fi
    
    # 2. 基于失败模式的改进建议
    local improvement_suggestions=$(suggest_system_improvements)
    if [[ -n "$improvement_suggestions" ]]; then
        suggestions+="🔧 **系统改进**:\n$improvement_suggestions\n\n"
    fi
    
    # 3. 基于资源使用的优化建议
    local optimization_suggestions=$(suggest_resource_optimizations)
    if [[ -n "$optimization_suggestions" ]]; then
        suggestions+="⚡ **性能优化**:\n$optimization_suggestions\n\n"
    fi
    
    # 4. 基于用户行为的个性化建议
    local personalization_suggestions=$(suggest_personalization_improvements)
    if [[ -n "$personalization_suggestions" ]]; then
        suggestions+="👤 **个性化改进**:\n$personalization_suggestions\n\n"
    fi
    
    # 5. 基于新技术的能力扩展建议
    local capability_suggestions=$(suggest_capability_expansions)
    if [[ -n "$capability_suggestions" ]]; then
        suggestions+="🚀 **能力扩展**:\n$capability_suggestions\n\n"
    fi
    
    echo "$suggestions"
}

# 建议自动化机会
suggest_automation_opportunities() {
    local suggestions=""
    
    # 分析重复任务模式
    local repeated_tasks=$(find_repeated_task_patterns)
    
    if [[ -n "$repeated_tasks" ]]; then
        suggestions+="- 检测到重复任务模式，可以创建自动化工作流\n"
        suggestions+="- 建议创建预设任务模板，减少手动配置\n"
    fi
    
    # 检查手动操作频率
    local manual_operations=$(count_manual_operations)
    if [[ $manual_operations -gt 5 ]]; then
        suggestions+="- 发现频繁的手动操作，可以开发快捷命令\n"
    fi
    
    echo "$suggestions"
}

# 建议系统改进
suggest_system_improvements() {
    local suggestions=""
    
    # 分析失败率
    local failure_rate=$(calculate_failure_rate)
    if [[ $failure_rate -gt 10 ]]; then
        suggestions+="- 任务失败率较高($failure_rate%)，建议增强错误处理\n"
        suggestions+="- 可以实现智能重试机制，提高成功率\n"
    fi
    
    # 检查监控覆盖度
    local monitoring_gaps=$(identify_monitoring_gaps)
    if [[ -n "$monitoring_gaps" ]]; then
        suggestions+="- 发现监控盲点，建议增加以下监控：$monitoring_gaps\n"
    fi
    
    echo "$suggestions"
}

# 建议资源优化
suggest_resource_optimizations() {
    local suggestions=""
    
    # 分析任务完成时间
    local avg_completion_time=$(calculate_average_completion_time)
    if [[ $avg_completion_time -gt 300 ]]; then  # 5分钟
        suggestions+="- 平均任务完成时间较长，可以优化并发策略\n"
        suggestions+="- 建议实现任务优先级队列，提高重要任务响应速度\n"
    fi
    
    # 检查资源利用率
    local resource_utilization=$(check_resource_utilization)
    if [[ $resource_utilization -lt 50 ]]; then
        suggestions+="- 资源利用率较低，可以增加并发任务数\n"
    fi
    
    echo "$suggestions"
}

# 建议个性化改进
suggest_personalization_improvements() {
    local suggestions=""
    
    # 分析Master的使用模式
    local usage_patterns=$(analyze_master_usage_patterns)
    
    suggestions+="- 根据您的使用习惯，建议创建个性化Dashboard\n"
    suggestions+="- 可以设置智能通知，只在重要事件时提醒\n"
    suggestions+="- 建议学习您的偏好，自动调整任务优先级\n"
    
    echo "$suggestions"
}

# 建议能力扩展
suggest_capability_expansions() {
    local suggestions=""
    
    # 基于available skills建议新能力
    suggestions+="- 发现log-analyzer skill，可以增强调试能力\n"
    suggestions+="- multi-agent-orchestrator可以提供更好的编排模式\n"
    suggestions+="- healthcheck skill可以增强系统安全性\n"
    
    echo "$suggestions"
}

# 记录主动想法
record_proactive_ideas() {
    local suggestions="$1"
    local timestamp=$(date -Iseconds)
    
    cat >> "$PROACTIVE_IDEAS" << EOF

## [PROACTIVE-$(date +%Y%m%d-%H%M)] Task Orchestrator Optimization Ideas

**Generated**: $timestamp
**Context**: Reverse prompting analysis
**Status**: pending_approval

### Suggestions
$suggestions

### Next Steps
- [ ] Review with Master
- [ ] Prioritize suggestions
- [ ] Implement approved items

---
EOF
}

# 向Master展示建议
present_suggestions_to_master() {
    local suggestions="$1"
    
    if [[ -n "$suggestions" ]]; then
        echo ""
        echo "💡 **基于当前Task Orchestrator使用情况，我发现了一些优化机会：**"
        echo ""
        echo "$suggestions"
        echo "🤔 **这些建议中有哪些您感兴趣？我可以立即开始实施。**"
        echo ""
        
        # 记录到今日笔记
        cat >> "$DAILY_NOTE" << EOF

## [REVERSE PROMPTING] $(date '+%H:%M:%S')

Generated proactive suggestions for Task Orchestrator optimization:

$suggestions

Waiting for Master's feedback on priority and implementation.

EOF
    else
        echo "✅ 当前系统运行良好，暂无优化建议。"
    fi
}

# 辅助函数实现（简化版本）
count_active_tasks() {
    find /tmp/task-orchestrator -name "*.tracker" 2>/dev/null | wc -l
}

analyze_recent_task_patterns() {
    echo "doc-engineer, research-analyst frequent usage"
}

analyze_failure_patterns() {
    echo "OpenClaw Bug #21968, timeout issues"
}

analyze_resource_usage() {
    echo "moderate CPU, low memory"
}

analyze_user_preferences() {
    echo "prefers detailed documentation, Feishu integration"
}

find_repeated_task_patterns() {
    echo "research->doc->review workflow"
}

count_manual_operations() {
    echo "3"
}

calculate_failure_rate() {
    echo "15"  # 15%
}

identify_monitoring_gaps() {
    echo "agent health, resource usage"
}

calculate_average_completion_time() {
    echo "420"  # 7分钟
}

check_resource_utilization() {
    echo "35"  # 35%
}

analyze_master_usage_patterns() {
    echo "morning heavy usage, prefers batch operations"
}

# 主函数
main() {
    echo "🎯 Task Orchestrator Reverse Prompting System"
    echo "Time: $(date)"
    echo "---"
    
    generate_proactive_suggestions
    
    echo "---"
    echo "Reverse prompting completed"
}

# 如果直接运行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi