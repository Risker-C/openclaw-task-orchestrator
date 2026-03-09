#!/bin/bash
# Structured Logging System for Task Orchestrator
# Provides consistent logging across all components

LOG_DIR="/tmp/task-orchestrator/logs"
mkdir -p "$LOG_DIR"

# 日志级别
declare -A LOG_LEVELS=(
    [DEBUG]=0
    [INFO]=1
    [WARN]=2
    [ERROR]=3
    [FATAL]=4
)

# 当前日志级别（默认INFO）
CURRENT_LOG_LEVEL="${LOG_LEVEL:-INFO}"

# 获取调用者信息
get_caller() {
    local caller_script=$(basename "${BASH_SOURCE[2]}" 2>/dev/null || echo "unknown")
    local caller_line="${BASH_LINENO[1]}"
    echo "${caller_script}:${caller_line}"
}

# 结构化日志函数
log_structured() {
    local level="$1"
    shift
    local message="$1"
    shift
    
    # 检查日志级别
    if [[ ${LOG_LEVELS[$level]:-0} -lt ${LOG_LEVELS[$CURRENT_LOG_LEVEL]:-1} ]]; then
        return
    fi
    
    # 构建JSON日志
    local timestamp=$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')
    local caller=$(get_caller)
    
    # 基础字段
    local log_entry=$(jq -n \
        --arg ts "$timestamp" \
        --arg lvl "$level" \
        --arg msg "$message" \
        --arg caller "$caller" \
        --arg service "task-orchestrator" \
        '{
            timestamp: $ts,
            level: $lvl,
            message: $msg,
            caller: $caller,
            service: $service
        }')
    
    # 添加额外字段
    while [[ $# -gt 0 ]]; do
        local key="$1"
        local value="$2"
        log_entry=$(echo "$log_entry" | jq --arg k "$key" --arg v "$value" '. + {($k): $v}')
        shift 2
    done
    
    # 输出到文件和stdout
    echo "$log_entry" >> "$LOG_DIR/orchestrator.log"
    
    # 根据级别输出到不同的流
    if [[ "$level" == "ERROR" || "$level" == "FATAL" ]]; then
        echo "$log_entry" >&2
    else
        echo "$log_entry"
    fi
}

# 便捷函数
log_debug() {
    log_structured "DEBUG" "$@"
}

log_info() {
    log_structured "INFO" "$@"
}

log_warn() {
    log_structured "WARN" "$@"
}

log_error() {
    log_structured "ERROR" "$@"
}

log_fatal() {
    log_structured "FATAL" "$@"
    exit 1
}

# Subagent专用日志
log_subagent() {
    local agent_id="$1"
    local task_id="$2"
    local level="$3"
    local message="$4"
    shift 4
    
    local log_file="$LOG_DIR/subagent-${agent_id}.log"
    
    log_structured "$level" "$message" \
        "agent_id" "$agent_id" \
        "task_id" "$task_id" \
        "$@" >> "$log_file"
}

# 监控系统专用日志
log_monitor() {
    local check_type="$1"
    local status="$2"
    local message="$3"
    shift 3
    
    log_structured "INFO" "$message" \
        "check_type" "$check_type" \
        "status" "$status" \
        "$@" >> "$LOG_DIR/monitor.log"
}

# 性能日志
log_performance() {
    local operation="$1"
    local duration_ms="$2"
    local status="$3"
    shift 3
    
    log_structured "INFO" "Performance metric" \
        "operation" "$operation" \
        "duration_ms" "$duration_ms" \
        "status" "$status" \
        "$@" >> "$LOG_DIR/performance.log"
}

# 审计日志
log_audit() {
    local action="$1"
    local user="$2"
    local resource="$3"
    local result="$4"
    shift 4
    
    log_structured "INFO" "Audit event" \
        "action" "$action" \
        "user" "$user" \
        "resource" "$resource" \
        "result" "$result" \
        "$@" >> "$LOG_DIR/audit.log"
}

# 导出函数供其他脚本使用
export -f log_structured
export -f log_debug
export -f log_info
export -f log_warn
export -f log_error
export -f log_fatal
export -f log_subagent
export -f log_monitor
export -f log_performance
export -f log_audit

# 如果直接运行，显示使用示例
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Structured Logging System for Task Orchestrator"
    echo ""
    echo "Usage in other scripts:"
    echo "  source $(basename "$0")"
    echo ""
    echo "Examples:"
    echo "  log_info 'Task started' 'task_id' 'TASK-001'"
    echo "  log_error 'Task failed' 'task_id' 'TASK-001' 'error' 'timeout'"
    echo "  log_subagent 'doc-engineer' 'TASK-001' 'INFO' 'Document created'"
    echo "  log_monitor 'health_check' 'success' 'All systems operational'"
    echo "  log_performance 'task_execution' '5234' 'success' 'task_id' 'TASK-001'"
    echo ""
    echo "Log files:"
    echo "  $LOG_DIR/orchestrator.log    - Main log"
    echo "  $LOG_DIR/subagent-*.log      - Per-agent logs"
    echo "  $LOG_DIR/monitor.log         - Monitor system logs"
    echo "  $LOG_DIR/performance.log     - Performance metrics"
    echo "  $LOG_DIR/audit.log           - Audit trail"
fi
