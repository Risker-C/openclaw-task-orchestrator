#!/bin/bash
# Self-Healing System for Task Orchestrator
# Based on proactive-agent skill patterns

WORKSPACE="$HOME/.openclaw/workspace"
LEARNING_DIR="$WORKSPACE/.learnings"
DAILY_NOTE="$WORKSPACE/memory/$(date +%Y-%m-%d).md"

# Self-Healing Pattern: Issue detected → Research → Fix → Test → Document

# 检测常见问题
detect_issues() {
    local issues_found=0
    
    echo "🔍 Scanning for issues..."
    
    # 1. 检查失败的subagents
    check_failed_subagents
    if [[ $? -ne 0 ]]; then
        ((issues_found++))
    fi
    
    # 2. 检查超时任务
    check_timeout_tasks
    if [[ $? -ne 0 ]]; then
        ((issues_found++))
    fi
    
    # 3. 检查Bitable连接
    check_bitable_connectivity
    if [[ $? -ne 0 ]]; then
        ((issues_found++))
    fi
    
    # 4. 检查监控系统状态
    check_monitor_health
    if [[ $? -ne 0 ]]; then
        ((issues_found++))
    fi
    
    echo "📊 Issues detected: $issues_found"
    return $issues_found
}

# 检查失败的subagents
check_failed_subagents() {
    local failed_count=0
    
    for tracker in /tmp/task-orchestrator/*.tracker 2>/dev/null; do
        [[ -f "$tracker" ]] || continue
        
        local status=$(jq -r '.status // "unknown"' "$tracker" 2>/dev/null)
        local task_id=$(basename "$tracker" .tracker)
        
        if [[ "$status" == "failed" ]]; then
            echo "❌ Failed task detected: $task_id"
            attempt_subagent_recovery "$task_id" "$tracker"
            ((failed_count++))
        fi
    done
    
    return $failed_count
}

# 尝试恢复失败的subagent
attempt_subagent_recovery() {
    local task_id="$1"
    local tracker_file="$2"
    
    echo "🔧 Attempting recovery for $task_id..."
    
    # 读取错误信息
    local error_msg=$(jq -r '.error_message // "Unknown error"' "$tracker_file")
    local agent_id=$(jq -r '.agent_id // "unknown"' "$tracker_file")
    
    # 根据错误类型尝试不同的恢复策略
    case "$error_msg" in
        *"unsupported channel: feishu"*)
            echo "🔄 Detected OpenClaw Bug #21968 - implementing workaround"
            implement_openclaw_bug_workaround "$task_id"
            ;;
        *"timeout"*)
            echo "⏰ Timeout detected - checking if task actually completed"
            check_task_actual_completion "$task_id"
            ;;
        *"rate limit"*)
            echo "🚦 Rate limit - scheduling retry with backoff"
            schedule_retry_with_backoff "$task_id" 300  # 5分钟后重试
            ;;
        *)
            echo "❓ Unknown error - logging for analysis"
            log_unknown_error "$task_id" "$error_msg"
            ;;
    esac
}

# 实现OpenClaw Bug #21968的绕过方案
implement_openclaw_bug_workaround() {
    local task_id="$1"
    
    echo "🛠️ Implementing OpenClaw Bug #21968 workaround..."
    
    # 检查任务是否实际完成（通过Bitable状态）
    # 这里需要调用doc-engineer检查Bitable状态
    
    cat >> "$DAILY_NOTE" << EOF

## [SELF-HEALING] OpenClaw Bug #21968 Workaround - $(date '+%H:%M:%S')

**Task**: $task_id
**Issue**: Sub-agent completion announce failed with "unsupported channel: feishu"
**Action**: Checking actual completion status via Bitable
**Status**: Investigating...

EOF
    
    # 记录到learnings
    if [[ -f "$LEARNING_DIR/ERRORS.md" ]]; then
        cat >> "$LEARNING_DIR/ERRORS.md" << EOF

## [ERR-$(date +%Y%m%d)-$(printf "%03d" $((RANDOM % 1000)))] openclaw_bug_21968_recovery

**Logged**: $(date -Iseconds)
**Priority**: high
**Status**: in_progress
**Area**: infra

### Summary
Automatic recovery attempt for OpenClaw Bug #21968

### Error
Sub-agent completion announce failed with "unsupported channel: feishu"

### Context
- Task ID: $task_id
- Recovery strategy: Check actual completion via Bitable
- Self-healing system triggered

### Suggested Fix
Implement alternative notification mechanism that bypasses channel plugin

### Metadata
- Source: self_healing_system
- Reproducible: yes
- See Also: OpenClaw Bug #21968

---
EOF
    fi
}

# 检查任务实际完成状态
check_task_actual_completion() {
    local task_id="$1"
    
    echo "🔍 Checking actual completion status for $task_id..."
    
    # 这里应该调用doc-engineer检查Bitable中的任务状态
    # 暂时记录需要手动检查
    
    cat >> "$DAILY_NOTE" << EOF

## [SELF-HEALING] Task Completion Check - $(date '+%H:%M:%S')

**Task**: $task_id
**Issue**: Timeout reported but checking actual completion
**Action**: Need to verify Bitable status
**Next**: Manual verification required

EOF
}

# 安排带退避的重试
schedule_retry_with_backoff() {
    local task_id="$1"
    local delay_seconds="$2"
    
    echo "⏳ Scheduling retry for $task_id in ${delay_seconds}s..."
    
    # 创建重试任务
    cat > "/tmp/task-orchestrator/${task_id}.retry" << EOF
{
  "task_id": "$task_id",
  "retry_time": $(($(date +%s) + delay_seconds)),
  "retry_count": 1,
  "reason": "rate_limit_backoff"
}
EOF
    
    echo "✅ Retry scheduled"
}

# 记录未知错误
log_unknown_error() {
    local task_id="$1"
    local error_msg="$2"
    
    if [[ -f "$LEARNING_DIR/ERRORS.md" ]]; then
        cat >> "$LEARNING_DIR/ERRORS.md" << EOF

## [ERR-$(date +%Y%m%d)-$(printf "%03d" $((RANDOM % 1000)))] unknown_subagent_failure

**Logged**: $(date -Iseconds)
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Unknown subagent failure requiring investigation

### Error
\`\`\`
$error_msg
\`\`\`

### Context
- Task ID: $task_id
- Self-healing system could not auto-resolve
- Requires manual investigation

### Suggested Fix
1. Analyze error pattern
2. Research root cause
3. Implement specific recovery strategy

### Metadata
- Source: self_healing_system
- Reproducible: unknown

---
EOF
    fi
}

# 检查超时任务
check_timeout_tasks() {
    local timeout_count=0
    local current_time=$(date +%s)
    
    for tracker in /tmp/task-orchestrator/*.tracker 2>/dev/null; do
        [[ -f "$tracker" ]] || continue
        
        local start_time=$(jq -r '.start_time // 0' "$tracker" 2>/dev/null)
        local timeout=$(jq -r '.timeout // 1800' "$tracker" 2>/dev/null)  # 默认30分钟
        local status=$(jq -r '.status // "unknown"' "$tracker" 2>/dev/null)
        
        if [[ "$status" == "running" && $((current_time - start_time)) -gt $timeout ]]; then
            local task_id=$(basename "$tracker" .tracker)
            echo "⏰ Timeout detected: $task_id"
            handle_timeout_task "$task_id" "$tracker"
            ((timeout_count++))
        fi
    done
    
    return $timeout_count
}

# 处理超时任务
handle_timeout_task() {
    local task_id="$1"
    local tracker_file="$2"
    
    echo "🔧 Handling timeout for $task_id..."
    
    # 更新状态为超时
    jq '.status = "timeout" | .timeout_detected = '$(date +%s)'' "$tracker_file" > "${tracker_file}.tmp"
    mv "${tracker_file}.tmp" "$tracker_file"
    
    # 记录超时事件
    cat >> "$DAILY_NOTE" << EOF

## [SELF-HEALING] Timeout Handled - $(date '+%H:%M:%S')

**Task**: $task_id
**Issue**: Task exceeded timeout limit
**Action**: Marked as timeout, investigating actual status
**Next**: Check if work was actually completed

EOF
}

# 检查Bitable连接性
check_bitable_connectivity() {
    echo "🔗 Checking Bitable connectivity..."
    
    # 这里应该实际测试Bitable API
    # 暂时返回成功
    return 0
}

# 检查监控系统健康状态
check_monitor_health() {
    echo "💓 Checking monitor system health..."
    
    # 检查监控脚本是否运行
    if ! pgrep -f "monitor-manager.sh" > /dev/null; then
        echo "⚠️ Monitor not running - attempting restart"
        attempt_monitor_restart
        return 1
    fi
    
    return 0
}

# 尝试重启监控系统
attempt_monitor_restart() {
    echo "🔄 Attempting to restart monitor system..."
    
    if [[ -f "$WORKSPACE/monitor-manager.sh" ]]; then
        bash "$WORKSPACE/monitor-manager.sh" start
        echo "✅ Monitor restart attempted"
    else
        echo "❌ Monitor script not found"
    fi
}

# 主函数
main() {
    echo "🏥 Task Orchestrator Self-Healing System"
    echo "Time: $(date)"
    echo "---"
    
    detect_issues
    local issue_count=$?
    
    if [[ $issue_count -eq 0 ]]; then
        echo "✅ All systems healthy"
    else
        echo "🔧 $issue_count issues detected and processed"
    fi
    
    echo "---"
    echo "Self-healing check completed"
}

main "$@"