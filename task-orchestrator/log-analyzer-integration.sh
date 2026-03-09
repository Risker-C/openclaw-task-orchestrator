#!/bin/bash
# Log Analyzer Integration for Task Orchestrator
# Based on log-analyzer skill

WORKSPACE="$HOME/.openclaw/workspace"
LOG_DIR="/tmp/task-orchestrator/logs"
LEARNING_DIR="$WORKSPACE/.learnings"
DAILY_NOTE="$WORKSPACE/memory/$(date +%Y-%m-%d).md"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 分析Task Orchestrator日志
analyze_orchestrator_logs() {
    echo "📋 Task Orchestrator Log Analysis"
    echo "Time: $(date)"
    echo "---"
    
    # 1. 分析subagent日志
    analyze_subagent_logs
    
    # 2. 分析监控系统日志
    analyze_monitor_logs
    
    # 3. 分析错误模式
    analyze_error_patterns
    
    # 4. 生成报告
    generate_log_report
}

# 分析subagent日志
analyze_subagent_logs() {
    echo "🤖 Subagent Log Analysis:"
    
    # 查找所有subagent日志
    local subagent_logs=$(find "$LOG_DIR" -name "subagent-*.log" 2>/dev/null)
    
    if [[ -z "$subagent_logs" ]]; then
        echo "  No subagent logs found"
        return
    fi
    
    # 统计错误
    local error_count=$(grep -ci 'error\|exception\|fatal' $subagent_logs 2>/dev/null || echo "0")
    echo "  Total errors: $error_count"
    
    # 按agent类型分组错误
    echo "  Errors by agent type:"
    for log in $subagent_logs; do
        local agent_id=$(basename "$log" .log | sed 's/subagent-//')
        local errors=$(grep -ci 'error' "$log" 2>/dev/null || echo "0")
        if [[ $errors -gt 0 ]]; then
            echo "    $agent_id: $errors errors"
        fi
    done
    
    # 提取最常见的错误
    echo "  Top 5 error messages:"
    grep -hi 'error\|exception' $subagent_logs 2>/dev/null | \
        sed 's/^[0-9TZ:.+\-]* //' | \
        sed 's/\b[0-9a-f]\{8,\}\b/ID/g' | \
        sort | uniq -c | sort -rn | head -5 | \
        awk '{$1=$1; print "    " $0}'
}

# 分析监控系统日志
analyze_monitor_logs() {
    echo ""
    echo "💓 Monitor System Log Analysis:"
    
    local monitor_log="$LOG_DIR/monitor.log"
    
    if [[ ! -f "$monitor_log" ]]; then
        echo "  No monitor log found"
        return
    fi
    
    # 统计监控事件
    local total_checks=$(grep -c 'check' "$monitor_log" 2>/dev/null || echo "0")
    local failures=$(grep -c 'failed\|timeout' "$monitor_log" 2>/dev/null || echo "0")
    local recoveries=$(grep -c 'recovered\|fixed' "$monitor_log" 2>/dev/null || echo "0")
    
    echo "  Total checks: $total_checks"
    echo "  Failures detected: $failures"
    echo "  Auto-recoveries: $recoveries"
    
    # 计算成功率
    if [[ $total_checks -gt 0 ]]; then
        local success_rate=$(( (total_checks - failures) * 100 / total_checks ))
        echo "  Success rate: ${success_rate}%"
    fi
}

# 分析错误模式
analyze_error_patterns() {
    echo ""
    echo "🔍 Error Pattern Analysis:"
    
    # 查找所有日志文件
    local all_logs=$(find "$LOG_DIR" -name "*.log" 2>/dev/null)
    
    if [[ -z "$all_logs" ]]; then
        echo "  No logs to analyze"
        return
    fi
    
    # 检测OpenClaw Bug #21968
    local bug_21968_count=$(grep -c 'unsupported channel: feishu' $all_logs 2>/dev/null || echo "0")
    if [[ $bug_21968_count -gt 0 ]]; then
        echo "  ⚠️ OpenClaw Bug #21968 detected: $bug_21968_count occurrences"
        record_pattern_to_learning "openclaw_bug_21968" "$bug_21968_count"
    fi
    
    # 检测超时模式
    local timeout_count=$(grep -c 'timeout\|timed out' $all_logs 2>/dev/null || echo "0")
    if [[ $timeout_count -gt 0 ]]; then
        echo "  ⏰ Timeout pattern detected: $timeout_count occurrences"
        
        # 分析哪些agent最容易超时
        echo "    Timeout by agent:"
        grep -h 'timeout' $all_logs 2>/dev/null | \
            grep -oP 'agent[_-]?\K[a-z-]+' | \
            sort | uniq -c | sort -rn | head -3 | \
            awk '{print "      " $2 ": " $1 "x"}'
    fi
    
    # 检测rate limit模式
    local rate_limit_count=$(grep -c 'rate limit\|429' $all_logs 2>/dev/null || echo "0")
    if [[ $rate_limit_count -gt 0 ]]; then
        echo "  🚦 Rate limit pattern detected: $rate_limit_count occurrences"
        record_pattern_to_learning "rate_limit" "$rate_limit_count"
    fi
    
    # 检测Bitable错误
    local bitable_errors=$(grep -c 'bitable.*error\|feishu.*failed' $all_logs 2>/dev/null || echo "0")
    if [[ $bitable_errors -gt 0 ]]; then
        echo "  📊 Bitable error pattern detected: $bitable_errors occurrences"
    fi
}

# 记录模式到learning
record_pattern_to_learning() {
    local pattern_name="$1"
    local occurrence_count="$2"
    
    if [[ ! -f "$LEARNING_DIR/ERRORS.md" ]]; then
        return
    fi
    
    # 检查是否已经记录过这个模式
    if grep -q "\[$pattern_name\]" "$LEARNING_DIR/ERRORS.md" 2>/dev/null; then
        # 更新occurrence count
        return
    fi
    
    # 记录新模式
    cat >> "$LEARNING_DIR/ERRORS.md" << EOF

## [ERR-$(date +%Y%m%d)-$(printf "%03d" $((RANDOM % 1000)))] $pattern_name

**Logged**: $(date -Iseconds)
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
Recurring error pattern detected by log analyzer

### Error
Pattern: $pattern_name
Occurrences: $occurrence_count

### Context
- Detected by: log-analyzer integration
- Log directory: $LOG_DIR
- Analysis time: $(date)

### Suggested Fix
1. Analyze root cause of recurring pattern
2. Implement specific mitigation strategy
3. Monitor for reduction in occurrences

### Metadata
- Source: log_analyzer
- Reproducible: yes
- Pattern: recurring

---
EOF
    
    echo "    📝 Recorded pattern to learnings: $pattern_name"
}

# 生成日志报告
generate_log_report() {
    echo ""
    echo "📊 Generating detailed report..."
    
    local report_file="$LOG_DIR/analysis-$(date +%Y%m%d-%H%M%S).txt"
    
    {
        echo "=== Task Orchestrator Log Analysis Report ==="
        echo "Generated: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
        echo ""
        
        # 统计所有日志
        echo "--- Log File Summary ---"
        find "$LOG_DIR" -name "*.log" -exec wc -l {} \; 2>/dev/null | \
            awk '{print $2 ": " $1 " lines"}' | sort
        echo ""
        
        # 错误频率
        echo "--- Error Frequency (Last 24h) ---"
        find "$LOG_DIR" -name "*.log" -mtime -1 -exec grep -h 'error\|exception' {} \; 2>/dev/null | \
            grep -oP '\d{4}-\d{2}-\d{2}T\d{2}' | \
            sort | uniq -c | \
            awk '{print $2 ": " $1 " errors"}'
        echo ""
        
        # Top错误消息
        echo "--- Top 10 Error Messages ---"
        find "$LOG_DIR" -name "*.log" -exec grep -hi 'error\|exception' {} \; 2>/dev/null | \
            sed 's/^[0-9TZ:.+\-]* //' | \
            sed 's/\b[0-9a-f]\{8,\}\b/ID/g' | \
            sed 's/[0-9]\{1,\}/N/g' | \
            sort | uniq -c | sort -rn | head -10
        echo ""
        
        # 建议
        echo "--- Recommendations ---"
        generate_recommendations
        
    } > "$report_file"
    
    echo "  Report saved to: $report_file"
    
    # 记录到今日笔记
    cat >> "$DAILY_NOTE" << EOF

## [LOG ANALYSIS] $(date '+%H:%M:%S')

Completed automated log analysis. Report: $report_file

Key findings:
$(tail -20 "$report_file" | head -10)

EOF
}

# 生成建议
generate_recommendations() {
    local all_logs=$(find "$LOG_DIR" -name "*.log" 2>/dev/null)
    
    if [[ -z "$all_logs" ]]; then
        echo "No logs to analyze for recommendations"
        return
    fi
    
    # 基于错误率的建议
    local total_lines=$(cat $all_logs 2>/dev/null | wc -l)
    local error_lines=$(grep -c 'error\|exception' $all_logs 2>/dev/null || echo "0")
    
    if [[ $total_lines -gt 0 ]]; then
        local error_rate=$(( error_lines * 100 / total_lines ))
        
        if [[ $error_rate -gt 10 ]]; then
            echo "1. High error rate ($error_rate%) - consider implementing better error handling"
        fi
    fi
    
    # 基于超时的建议
    local timeout_count=$(grep -c 'timeout' $all_logs 2>/dev/null || echo "0")
    if [[ $timeout_count -gt 5 ]]; then
        echo "2. Frequent timeouts detected - consider increasing timeout limits or optimizing agent performance"
    fi
    
    # 基于OpenClaw Bug的建议
    local bug_count=$(grep -c 'unsupported channel' $all_logs 2>/dev/null || echo "0")
    if [[ $bug_count -gt 0 ]]; then
        echo "3. OpenClaw Bug #21968 detected - implement alternative notification mechanism"
    fi
    
    # 基于rate limit的建议
    local rate_limit_count=$(grep -c 'rate limit' $all_logs 2>/dev/null || echo "0")
    if [[ $rate_limit_count -gt 0 ]]; then
        echo "4. Rate limiting detected - implement exponential backoff retry strategy"
    fi
}

# 实时监控模式
real_time_monitor() {
    echo "🔴 Starting real-time log monitoring..."
    echo "Press Ctrl+C to stop"
    echo "---"
    
    # 监控所有.log文件
    tail -f "$LOG_DIR"/*.log 2>/dev/null | while IFS= read -r line; do
        # 高亮错误
        if echo "$line" | grep -qi 'error\|exception\|fatal'; then
            echo -e "\033[31m[ERROR]\033[0m $line"
            
            # 如果是critical错误，发出警报
            if echo "$line" | grep -qi 'fatal\|critical'; then
                echo -e "\a"  # 终端铃声
            fi
        elif echo "$line" | grep -qi 'warn'; then
            echo -e "\033[33m[WARN]\033[0m $line"
        else
            echo "$line"
        fi
    done
}

# 清理旧日志
cleanup_old_logs() {
    echo "🧹 Cleaning up old logs..."
    
    # 删除7天前的日志
    find "$LOG_DIR" -name "*.log" -mtime +7 -delete
    find "$LOG_DIR" -name "analysis-*.txt" -mtime +7 -delete
    
    echo "  Old logs cleaned"
}

# 主函数
main() {
    local mode="${1:-analyze}"
    
    case "$mode" in
        analyze)
            analyze_orchestrator_logs
            ;;
        monitor)
            real_time_monitor
            ;;
        cleanup)
            cleanup_old_logs
            ;;
        report)
            generate_log_report
            ;;
        *)
            echo "Usage: $0 {analyze|monitor|cleanup|report}"
            echo ""
            echo "  analyze  - Analyze existing logs (default)"
            echo "  monitor  - Real-time log monitoring"
            echo "  cleanup  - Clean up old logs (>7 days)"
            echo "  report   - Generate detailed report only"
            exit 1
            ;;
    esac
}

main "$@"
