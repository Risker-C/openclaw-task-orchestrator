#!/bin/bash
# Memory Flush Monitor - Proactive context management
# Based on proactive-agent skill

WORKSPACE="$HOME/.openclaw/workspace"
MEMORY_DIR="$WORKSPACE/memory"
DAILY_NOTE="$MEMORY_DIR/$(date +%Y-%m-%d).md"

# 获取当前上下文使用率
get_context_usage() {
    # 通过session_status获取上下文使用情况
    # 这里需要实际实现，暂时返回模拟值
    echo "45"  # 返回百分比
}

# Memory Flush Protocol
check_and_flush() {
    local context_pct=$(get_context_usage)
    local timestamp=$(date -Iseconds)
    
    echo "📊 Context Usage: ${context_pct}%"
    
    if [[ $context_pct -ge 85 ]]; then
        echo "🚨 EMERGENCY FLUSH (>85%)"
        flush_critical_context
        return 1
    elif [[ $context_pct -ge 70 ]]; then
        echo "⚠️ ACTIVE FLUSHING (70-85%)"
        flush_important_context
        return 2
    elif [[ $context_pct -ge 50 ]]; then
        echo "👀 INCREASED VIGILANCE (50-70%)"
        return 3
    else
        echo "✅ Normal operation (<50%)"
        return 0
    fi
}

# 紧急刷新：保存所有关键上下文
flush_critical_context() {
    cat >> "$DAILY_NOTE" << EOF

## [EMERGENCY FLUSH] $(date '+%Y-%m-%d %H:%M:%S')

**Context Usage**: >85% - Emergency flush triggered

### Active Tasks
$(list_active_tasks)

### Recent Decisions
$(extract_recent_decisions)

### Open Questions
$(list_open_questions)

### Action Items
$(list_action_items)

---
EOF
    
    echo "✅ Critical context flushed to $DAILY_NOTE"
}

# 主动刷新：保存重要上下文
flush_important_context() {
    cat >> "$DAILY_NOTE" << EOF

## [ACTIVE FLUSH] $(date '+%Y-%m-%d %H:%M:%S')

**Context Usage**: 70-85% - Active flushing

### Key Points
$(extract_key_points)

### Decisions Made
$(extract_recent_decisions)

---
EOF
    
    echo "✅ Important context flushed to $DAILY_NOTE"
}

# 辅助函数（需要实际实现）
list_active_tasks() {
    # 列出当前活跃的任务
    find /tmp/task-orchestrator -name "*.tracker" 2>/dev/null | while read tracker; do
        task_id=$(basename "$tracker" .tracker)
        status=$(jq -r '.status // "unknown"' "$tracker" 2>/dev/null)
        echo "- $task_id: $status"
    done
}

extract_recent_decisions() {
    # 从最近的对话中提取决策
    echo "- [需要实现：从会话历史提取决策]"
}

list_open_questions() {
    # 列出未解决的问题
    echo "- [需要实现：从会话历史提取问题]"
}

list_action_items() {
    # 列出待办事项
    echo "- [需要实现：从会话历史提取待办]"
}

extract_key_points() {
    # 提取关键点
    echo "- [需要实现：从会话历史提取关键点]"
}

# 主函数
main() {
    check_and_flush
    exit_code=$?
    
    # 根据返回码决定下一步
    case $exit_code in
        0) echo "No action needed" ;;
        1) echo "Emergency flush completed" ;;
        2) echo "Active flush completed" ;;
        3) echo "Monitoring increased" ;;
    esac
}

main "$@"
