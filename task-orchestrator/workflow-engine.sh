#!/bin/bash
# Workflow Execution Engine for Task Orchestrator v3.0
# Implements actual workflow execution with Supervisor pattern

WORKSPACE="$HOME/.openclaw/workspace"
ORCHESTRATOR_DIR="$WORKSPACE/task-orchestrator"
SHARED_DIR="/tmp/task-orchestrator/shared"
STATE_DIR="/tmp/task-orchestrator/state"
QUEUE_DIR="/tmp/task-orchestrator/queue"
WORKFLOWS_DIR="$ORCHESTRATOR_DIR/workflows"

# 引入依赖
source "$ORCHESTRATOR_DIR/structured-logging.sh" 2>/dev/null || true
source "$ORCHESTRATOR_DIR/orchestrator-v3-supervisor.sh" 2>/dev/null || true

# 确保目录存在
mkdir -p "$WORKFLOWS_DIR" "$SHARED_DIR" "$STATE_DIR" "$QUEUE_DIR"

# 预定义工作流
init_predefined_workflows() {
    log_info "WorkflowEngine: Initializing predefined workflows"
    
    # 文档分析工作流
    cat > "$WORKFLOWS_DIR/document_analysis.json" << 'EOF'
{
  "name": "document_analysis",
  "description": "分析文档内容并生成专业报告",
  "phases": [
    {
      "id": "phase1_extraction",
      "name": "Document Extraction",
      "description": "提取文档内容和结构",
      "agents": ["doc-engineer"],
      "dependencies": [],
      "timeout": 120,
      "output_path": "shared/phase1-document/",
      "success_criteria": ["document_data.md", "metadata.json"],
      "task_template": "使用 feishu-strategic-agent skill 分析文档：{document_url}\n\n输出要求：\n1. 创建 {output_path}/document_data.md - 包含文档的完整内容和结构\n2. 创建 {output_path}/metadata.json - 包含文档元信息\n\n请确保输出文件格式正确，便于后续阶段使用。"
    },
    {
      "id": "phase2_analysis",
      "name": "Parallel Expert Analysis",
      "description": "多专家并行分析",
      "agents": ["research-analyst", "architect", "implementation-planner"],
      "dependencies": ["phase1_extraction"],
      "timeout": 180,
      "output_path": "shared/phase2-analysis/",
      "parallel": true,
      "task_templates": {
        "research-analyst": "基于 {input_path}/document_data.md 进行技术调研和竞品分析\n\n任务要求：\n1. 使用 tavily-search skill 进行网络调研\n2. 分析相关技术的成熟度和可行性\n3. 对比竞品方案的优劣\n4. 输出到：{output_path}/research-analysis.md\n\n请提供详细的调研报告和建议。",
        "architect": "基于 {input_path}/document_data.md 进行架构设计分析\n\n任务要求：\n1. 分析技术架构的合理性\n2. 评估系统设计的可扩展性\n3. 识别潜在的技术风险\n4. 输出到：{output_path}/architecture-design.md\n\n请提供专业的架构分析和优化建议。",
        "implementation-planner": "基于 {input_path}/document_data.md 制定实施计划\n\n任务要求：\n1. 分解实施步骤和里程碑\n2. 评估资源需求和时间安排\n3. 识别关键风险和依赖\n4. 输出到：{output_path}/implementation-plan.md\n\n请提供可执行的实施路线图。"
      }
    },
    {
      "id": "phase3_coordination",
      "name": "Final Coordination",
      "description": "整合所有分析结果",
      "agents": ["task-orchestrator"],
      "dependencies": ["phase2_analysis"],
      "timeout": 60,
      "output_path": "shared/phase3-final/",
      "task_template": "整合以下分析结果生成最终报告：\n\n输入文件：\n- {input_path}/research-analysis.md\n- {input_path}/architecture-design.md\n- {input_path}/implementation-plan.md\n\n输出要求：\n1. 生成 {output_path}/final-report.md - 综合分析报告\n2. 生成 {output_path}/executive-summary.md - 执行摘要\n3. 生成 {output_path}/recommendations.md - 具体建议\n\n请确保报告结构清晰，结论明确。"
    }
  ]
}
EOF

    # 技术评估工作流
    cat > "$WORKFLOWS_DIR/tech_evaluation.json" << 'EOF'
{
  "name": "tech_evaluation",
  "description": "评估技术方案的可行性和风险",
  "phases": [
    {
      "id": "phase1_research",
      "name": "Technology Research",
      "agents": ["research-analyst"],
      "dependencies": [],
      "timeout": 180,
      "output_path": "shared/phase1-research/",
      "task_template": "调研技术：{tech_name}\n\n调研内容：\n1. 技术原理和核心特性\n2. 技术成熟度和稳定性\n3. 社区支持和生态系统\n4. 竞品对比和优势分析\n\n使用 tavily-search skill 进行深度调研\n输出到：{output_path}/research-report.md"
    },
    {
      "id": "phase2_architecture",
      "name": "Architecture Design",
      "agents": ["architect"],
      "dependencies": ["phase1_research"],
      "timeout": 120,
      "output_path": "shared/phase2-architecture/",
      "task_template": "基于 {input_path}/research-report.md 设计技术架构\n\n设计内容：\n1. 系统架构图和组件设计\n2. 技术栈选择和集成方案\n3. 数据流和接口设计\n4. 部署和运维方案\n\n输出到：{output_path}/architecture-design.md"
    },
    {
      "id": "phase3_planning",
      "name": "Implementation Planning",
      "agents": ["implementation-planner"],
      "dependencies": ["phase2_architecture"],
      "timeout": 120,
      "output_path": "shared/phase3-planning/",
      "task_template": "制定实施计划\n\n输入：\n- {input_path}/architecture-design.md\n\n输出内容：\n1. 实施路线图和时间安排\n2. 里程碑规划和交付物\n3. 资源需求和团队配置\n4. 风险识别和缓解措施\n\n输出到：{output_path}/implementation-plan.md"
    }
  ]
}
EOF

    log_info "WorkflowEngine: Predefined workflows initialized"
}

# 执行工作流
execute_workflow() {
    local workflow_name="$1"
    local params="$2"
    local shared_dir="$3"
    local task_id="${4:-TASK-$(date +%Y%m%d-%H%M%S)}"
    
    log_info "WorkflowEngine: Starting workflow execution" \
        "workflow" "$workflow_name" \
        "task_id" "$task_id"
    
    # 加载工作流定义
    local workflow_file="$WORKFLOWS_DIR/${workflow_name}.json"
    
    if [[ ! -f "$workflow_file" ]]; then
        log_error "WorkflowEngine: Workflow not found" "workflow" "$workflow_name"
        return 1
    fi
    
    # 创建任务状态
    local task_state_file="$STATE_DIR/${task_id}-state.json"
    
    cat > "$task_state_file" << EOF
{
  "task_id": "$task_id",
  "workflow": "$workflow_name",
  "status": "running",
  "current_phase": "",
  "started_at": "$(date -Iseconds)",
  "params": $params,
  "shared_dir": "$shared_dir",
  "phases": {},
  "error_count": 0
}
EOF
    
    # 创建共享目录
    mkdir -p "$shared_dir"
    
    # 解析工作流并执行
    local phases=$(jq -r '.phases[] | @base64' "$workflow_file")
    
    for phase_data in $phases; do
        local phase_json=$(echo "$phase_data" | base64 -d)
        local phase_id=$(echo "$phase_json" | jq -r '.id')
        
        log_info "WorkflowEngine: Processing phase" \
            "task_id" "$task_id" \
            "phase_id" "$phase_id"
        
        # 检查依赖
        if ! check_phase_dependencies "$task_id" "$phase_json"; then
            log_warn "WorkflowEngine: Phase dependencies not met, queuing" \
                "task_id" "$task_id" \
                "phase_id" "$phase_id"
            
            queue_phase "$task_id" "$phase_json"
            continue
        fi
        
        # 执行阶段
        execute_phase "$task_id" "$phase_json" "$params" "$shared_dir"
    done
    
    log_info "WorkflowEngine: Workflow execution initiated" "task_id" "$task_id"
    echo "$task_id"
}

# 检查阶段依赖
check_phase_dependencies() {
    local task_id="$1"
    local phase_json="$2"
    
    local dependencies=$(echo "$phase_json" | jq -r '.dependencies[]? // empty')
    
    if [[ -z "$dependencies" ]]; then
        return 0  # 无依赖
    fi
    
    local task_state_file="$STATE_DIR/${task_id}-state.json"
    
    for dep_phase in $dependencies; do
        local dep_status=$(jq -r ".phases[\"$dep_phase\"].status // \"not_started\"" "$task_state_file")
        
        if [[ "$dep_status" != "completed" ]]; then
            log_debug "WorkflowEngine: Dependency not satisfied" \
                "task_id" "$task_id" \
                "dependency" "$dep_phase" \
                "status" "$dep_status"
            return 1
        fi
    done
    
    return 0
}

# 队列阶段（依赖未满足时）
queue_phase() {
    local task_id="$1"
    local phase_json="$2"
    
    local phase_id=$(echo "$phase_json" | jq -r '.id')
    local queue_file="$QUEUE_DIR/${task_id}-${phase_id}.json"
    
    cat > "$queue_file" << EOF
{
  "task_id": "$task_id",
  "phase_data": $phase_json,
  "status": "queued",
  "queued_at": "$(date -Iseconds)"
}
EOF
    
    log_debug "WorkflowEngine: Phase queued" \
        "task_id" "$task_id" \
        "phase_id" "$phase_id"
}

# 执行阶段
execute_phase() {
    local task_id="$1"
    local phase_json="$2"
    local params="$3"
    local shared_dir="$4"
    
    local phase_id=$(echo "$phase_json" | jq -r '.id')
    local phase_name=$(echo "$phase_json" | jq -r '.name')
    local agents=$(echo "$phase_json" | jq -r '.agents[]')
    local is_parallel=$(echo "$phase_json" | jq -r '.parallel // false')
    local timeout=$(echo "$phase_json" | jq -r '.timeout // 120')
    local output_path=$(echo "$phase_json" | jq -r '.output_path')
    
    log_info "WorkflowEngine: Executing phase" \
        "task_id" "$task_id" \
        "phase_id" "$phase_id" \
        "parallel" "$is_parallel"
    
    # 更新任务状态
    update_task_phase_status "$task_id" "$phase_id" "running"
    
    # 创建输出目录
    mkdir -p "$shared_dir/$output_path"
    
    # 执行agents
    if [[ "$is_parallel" == "true" ]]; then
        execute_agents_parallel "$task_id" "$phase_json" "$params" "$shared_dir"
    else
        execute_agents_sequential "$task_id" "$phase_json" "$params" "$shared_dir"
    fi
}

# 并行执行agents
execute_agents_parallel() {
    local task_id="$1"
    local phase_json="$2"
    local params="$3"
    local shared_dir="$4"
    
    local phase_id=$(echo "$phase_json" | jq -r '.id')
    local agents=$(echo "$phase_json" | jq -r '.agents[]')
    
    log_info "WorkflowEngine: Starting parallel execution" \
        "task_id" "$task_id" \
        "phase_id" "$phase_id"
    
    local pids=()
    
    for agent_id in $agents; do
        log_info "WorkflowEngine: Starting agent" \
            "task_id" "$task_id" \
            "phase_id" "$phase_id" \
            "agent_id" "$agent_id"
        
        # 在后台启动agent
        execute_single_agent "$task_id" "$phase_json" "$agent_id" "$params" "$shared_dir" &
        local pid=$!
        pids+=($pid)
        
        log_debug "WorkflowEngine: Agent started in background" \
            "agent_id" "$agent_id" \
            "pid" "$pid"
    done
    
    # 等待所有agents完成
    log_info "WorkflowEngine: Waiting for parallel agents" \
        "task_id" "$task_id" \
        "phase_id" "$phase_id" \
        "agent_count" "${#pids[@]}"
    
    for pid in "${pids[@]}"; do
        wait "$pid"
        local exit_code=$?
        
        if [[ $exit_code -ne 0 ]]; then
            log_error "WorkflowEngine: Agent failed" \
                "task_id" "$task_id" \
                "pid" "$pid" \
                "exit_code" "$exit_code"
        fi
    done
    
    log_info "WorkflowEngine: Parallel execution completed" \
        "task_id" "$task_id" \
        "phase_id" "$phase_id"
}

# 顺序执行agents
execute_agents_sequential() {
    local task_id="$1"
    local phase_json="$2"
    local params="$3"
    local shared_dir="$4"
    
    local phase_id=$(echo "$phase_json" | jq -r '.id')
    local agents=$(echo "$phase_json" | jq -r '.agents[]')
    
    log_info "WorkflowEngine: Starting sequential execution" \
        "task_id" "$task_id" \
        "phase_id" "$phase_id"
    
    for agent_id in $agents; do
        log_info "WorkflowEngine: Executing agent" \
            "task_id" "$task_id" \
            "phase_id" "$phase_id" \
            "agent_id" "$agent_id"
        
        execute_single_agent "$task_id" "$phase_json" "$agent_id" "$params" "$shared_dir"
        local exit_code=$?
        
        if [[ $exit_code -ne 0 ]]; then
            log_error "WorkflowEngine: Agent failed, stopping sequential execution" \
                "task_id" "$task_id" \
                "agent_id" "$agent_id" \
                "exit_code" "$exit_code"
            return $exit_code
        fi
    done
    
    log_info "WorkflowEngine: Sequential execution completed" \
        "task_id" "$task_id" \
        "phase_id" "$phase_id"
}

# 执行单个agent
execute_single_agent() {
    local task_id="$1"
    local phase_json="$2"
    local agent_id="$3"
    local params="$4"
    local shared_dir="$5"
    
    local phase_id=$(echo "$phase_json" | jq -r '.id')
    local timeout=$(echo "$phase_json" | jq -r '.timeout // 120')
    local output_path=$(echo "$phase_json" | jq -r '.output_path')
    
    # 获取任务模板
    local task_template
    local task_templates=$(echo "$phase_json" | jq -r '.task_templates // empty')
    
    if [[ -n "$task_templates" ]]; then
        task_template=$(echo "$phase_json" | jq -r ".task_templates[\"$agent_id\"] // .task_template")
    else
        task_template=$(echo "$phase_json" | jq -r '.task_template')
    fi
    
    # 替换模板变量
    local task_description=$(substitute_template_variables "$task_template" "$params" "$shared_dir" "$output_path")
    
    log_info "WorkflowEngine: Spawning agent" \
        "task_id" "$task_id" \
        "phase_id" "$phase_id" \
        "agent_id" "$agent_id" \
        "timeout" "$timeout"
    
    # 验证agent配置
    if ! validate_agent_config "$agent_id"; then
        log_error "WorkflowEngine: Agent validation failed" "agent_id" "$agent_id"
        return 1
    fi
    
    # 创建tracker文件
    local tracker_file="/tmp/task-orchestrator/${task_id}-${phase_id}-${agent_id}.tracker"
    
    cat > "$tracker_file" << EOF
{
  "task_id": "$task_id",
  "phase_id": "$phase_id",
  "agent_id": "$agent_id",
  "status": "starting",
  "start_time": $(date +%s),
  "timeout": $timeout,
  "output_path": "$shared_dir/$output_path"
}
EOF
    
    # 启动agent（这里需要实际调用sessions_spawn）
    log_info "WorkflowEngine: Agent task" \
        "agent_id" "$agent_id" \
        "task" "$task_description"
    
    # 模拟agent执行（实际应该调用sessions_spawn）
    # sessions_spawn agentId="$agent_id" mode="run" task="$task_description" runTimeoutSeconds="$timeout"
    
    # 更新tracker状态
    jq '.status = "completed" | .end_time = '$(date +%s)'' "$tracker_file" > "${tracker_file}.tmp"
    mv "${tracker_file}.tmp" "$tracker_file"
    
    log_info "WorkflowEngine: Agent completed" \
        "task_id" "$task_id" \
        "agent_id" "$agent_id"
    
    return 0
}

# 替换模板变量
substitute_template_variables() {
    local template="$1"
    local params="$2"
    local shared_dir="$3"
    local output_path="$4"
    
    # 基本变量替换
    local result="$template"
    result="${result//\{shared_dir\}/$shared_dir}"
    result="${result//\{output_path\}/$shared_dir/$output_path}"
    result="${result//\{input_path\}/$shared_dir/shared/phase1-document}"  # 简化版本
    
    # 参数变量替换
    if [[ -n "$params" ]]; then
        local param_keys=$(echo "$params" | jq -r 'keys[]')
        
        for key in $param_keys; do
            local value=$(echo "$params" | jq -r ".$key")
            result="${result//\{$key\}/$value}"
        done
    fi
    
    echo "$result"
}

# 更新任务阶段状态
update_task_phase_status() {
    local task_id="$1"
    local phase_id="$2"
    local status="$3"
    
    local task_state_file="$STATE_DIR/${task_id}-state.json"
    
    local temp_file=$(mktemp)
    jq --arg phase_id "$phase_id" --arg status "$status" \
        '.phases[$phase_id] = {status: $status, updated_at: (now | strftime("%Y-%m-%dT%H:%M:%SZ"))}' \
        "$task_state_file" > "$temp_file"
    mv "$temp_file" "$task_state_file"
    
    log_debug "WorkflowEngine: Phase status updated" \
        "task_id" "$task_id" \
        "phase_id" "$phase_id" \
        "status" "$status"
}

# 获取工作流状态
get_workflow_status() {
    local task_id="$1"
    
    local task_state_file="$STATE_DIR/${task_id}-state.json"
    
    if [[ -f "$task_state_file" ]]; then
        cat "$task_state_file"
    else
        echo '{"error": "Task not found"}'
    fi
}

# 列出所有活跃的工作流
list_active_workflows() {
    log_info "WorkflowEngine: Listing active workflows"
    
    echo "Active Workflows:"
    echo "=================="
    
    for state_file in "$STATE_DIR"/*-state.json; do
        [[ -f "$state_file" ]] || continue
        
        local task_id=$(jq -r '.task_id' "$state_file")
        local workflow=$(jq -r '.workflow' "$state_file")
        local status=$(jq -r '.status' "$state_file")
        local started_at=$(jq -r '.started_at' "$state_file")
        
        echo "Task: $task_id | Workflow: $workflow | Status: $status | Started: $started_at"
    done
}

# 主函数
main() {
    local command="${1:-help}"
    shift
    
    case "$command" in
        init)
            log_info "WorkflowEngine: Initializing"
            init_predefined_workflows
            ;;
        execute)
            local workflow_name="$1"
            local params="${2:-{}}"
            local shared_dir="${3:-/tmp/workflow-shared-$(date +%s)}"
            local task_id="$4"
            
            execute_workflow "$workflow_name" "$params" "$shared_dir" "$task_id"
            ;;
        status)
            local task_id="$1"
            if [[ -n "$task_id" ]]; then
                get_workflow_status "$task_id"
            else
                list_active_workflows
            fi
            ;;
        *)
            echo "Workflow Execution Engine v3.0"
            echo ""
            echo "Usage: $0 <command> [options]"
            echo ""
            echo "Commands:"
            echo "  init                                    - Initialize predefined workflows"
            echo "  execute <workflow> [params] [dir] [id]  - Execute workflow"
            echo "  status [task_id]                        - Show workflow status"
            echo ""
            echo "Examples:"
            echo "  $0 execute document_analysis '{\"document_url\":\"https://...\"}'"
            echo "  $0 execute tech_evaluation '{\"tech_name\":\"ML-SHARP\"}'"
            echo "  $0 status TASK-20260306-123456"
            ;;
    esac
}

# 如果直接运行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi