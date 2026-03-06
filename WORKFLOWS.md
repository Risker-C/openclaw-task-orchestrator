# Task Orchestrator v3.0 工作流定义

## 预定义工作流

### 1. document_analysis - 文档分析工作流

**适用场景**: 分析飞书文档、技术方案评估

**Pipeline**:
```json
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
      "task_template": "使用 feishu-strategic-agent skill 分析文档：{document_url}\n输出到：{output_path}\n包含：document_data.md, metadata.json"
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
        "research-analyst": "基于 {input_path}/document_data.md 进行技术调研和竞品分析\n使用 tavily-search skill\n输出到：{output_path}/research-analysis.md",
        "architect": "基于 {input_path}/document_data.md 进行架构设计分析\n输出到：{output_path}/architecture-design.md",
        "implementation-planner": "基于 {input_path}/document_data.md 制定实施计划\n输出到：{output_path}/implementation-plan.md"
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
      "task_template": "整合以下分析结果：\n- {input_path}/research-analysis.md\n- {input_path}/architecture-design.md\n- {input_path}/implementation-plan.md\n\n生成最终报告：{output_path}/final-report.md"
    }
  ]
}
```

### 2. tech_evaluation - 技术方案评估工作流

**适用场景**: 评估新技术可行性、技术选型

**Pipeline**:
```json
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
      "task_template": "调研技术：{tech_name}\n包括：\n- 技术原理\n- 成熟度\n- 社区支持\n- 竞品对比\n使用 tavily-search skill"
    },
    {
      "id": "phase2_architecture",
      "name": "Architecture Design",
      "agents": ["architect"],
      "dependencies": ["phase1_research"],
      "timeout": 120,
      "output_path": "shared/phase2-architecture/",
      "task_template": "基于 {input_path}/research-report.md 设计技术架构\n包括：\n- 系统架构图\n- 技术栈选择\n- 集成方案"
    },
    {
      "id": "phase3_security",
      "name": "Security Assessment",
      "agents": ["security-monitor"],
      "dependencies": ["phase2_architecture"],
      "timeout": 90,
      "output_path": "shared/phase3-security/",
      "task_template": "评估 {input_path}/architecture-design.md 的安全风险\n包括：\n- 安全威胁分析\n- 风险等级评估\n- 缓解措施建议"
    },
    {
      "id": "phase4_planning",
      "name": "Implementation Planning",
      "agents": ["implementation-planner"],
      "dependencies": ["phase2_architecture", "phase3_security"],
      "timeout": 120,
      "output_path": "shared/phase4-planning/",
      "task_template": "制定实施计划\n输入：\n- {input_path}/architecture-design.md\n- {input_path}/security-assessment.md\n\n输出：\n- 实施路线图\n- 里程碑规划\n- 资源需求"
    }
  ]
}
```

### 3. code_review - 代码审查工作流

**适用场景**: PR审查、代码质量检查

**Pipeline**:
```json
{
  "name": "code_review",
  "description": "多维度代码审查",
  "phases": [
    {
      "id": "phase1_quality",
      "name": "Code Quality Review",
      "agents": ["code-reviewer"],
      "dependencies": [],
      "timeout": 120,
      "output_path": "shared/phase1-quality/",
      "task_template": "审查代码质量：{pr_url}\n检查：\n- 代码风格\n- 最佳实践\n- 可维护性\n- 测试覆盖"
    },
    {
      "id": "phase2_security",
      "name": "Security Review",
      "agents": ["security-monitor"],
      "dependencies": [],
      "timeout": 90,
      "output_path": "shared/phase2-security/",
      "parallel_with": ["phase1_quality"],
      "task_template": "安全审查：{pr_url}\n检查：\n- 安全漏洞\n- 敏感数据泄露\n- 权限控制\n- 依赖安全"
    },
    {
      "id": "phase3_architecture",
      "name": "Architecture Review",
      "agents": ["architect"],
      "dependencies": [],
      "timeout": 90,
      "output_path": "shared/phase3-architecture/",
      "parallel_with": ["phase1_quality", "phase2_security"],
      "task_template": "架构审查：{pr_url}\n检查：\n- 架构一致性\n- 设计模式\n- 性能影响\n- 可扩展性"
    },
    {
      "id": "phase4_summary",
      "name": "Review Summary",
      "agents": ["task-orchestrator"],
      "dependencies": ["phase1_quality", "phase2_security", "phase3_architecture"],
      "timeout": 30,
      "output_path": "shared/phase4-summary/",
      "task_template": "整合审查结果\n生成：\n- 综合评分\n- 关键问题列表\n- 改进建议\n- 批准/拒绝建议"
    }
  ]
}
```

### 4. ui_design - UI/UX设计工作流

**适用场景**: 产品设计、用户体验优化

**Pipeline**:
```json
{
  "name": "ui_design",
  "description": "UI/UX设计和评审",
  "phases": [
    {
      "id": "phase1_research",
      "name": "User Research",
      "agents": ["research-analyst"],
      "dependencies": [],
      "timeout": 120,
      "output_path": "shared/phase1-research/",
      "task_template": "用户研究：{product_name}\n包括：\n- 用户画像\n- 使用场景\n- 竞品分析\n- 最佳实践"
    },
    {
      "id": "phase2_design",
      "name": "UI Design",
      "agents": ["ui-designer"],
      "dependencies": ["phase1_research"],
      "timeout": 180,
      "output_path": "shared/phase2-design/",
      "task_template": "基于 {input_path}/user-research.md 设计UI\n包括：\n- 交互原型\n- 视觉设计\n- 设计规范\n- 可用性说明"
    },
    {
      "id": "phase3_review",
      "name": "Design Review",
      "agents": ["architect", "security-monitor"],
      "dependencies": ["phase2_design"],
      "timeout": 90,
      "output_path": "shared/phase3-review/",
      "parallel": true,
      "task_templates": {
        "architect": "技术可行性评审\n检查：\n- 实现复杂度\n- 性能影响\n- 兼容性",
        "security-monitor": "安全性评审\n检查：\n- 隐私保护\n- 数据安全\n- 访问控制"
      }
    }
  ]
}
```

## 工作流使用方法

### 1. 使用预定义工作流

```bash
# 启动文档分析工作流
bash orchestrator-v3-supervisor.sh execute \
  --workflow document_analysis \
  --params '{"document_url": "https://my.feishu.cn/wiki/XXX"}' \
  --shared-dir /tmp/analysis-shared

# 启动技术评估工作流
bash orchestrator-v3-supervisor.sh execute \
  --workflow tech_evaluation \
  --params '{"tech_name": "Apple ML-SHARP"}' \
  --shared-dir /tmp/tech-eval-shared
```

### 2. 自定义工作流

```bash
# 创建自定义工作流定义
cat > custom-workflow.json << 'EOF'
{
  "name": "custom_analysis",
  "description": "自定义分析流程",
  "phases": [
    {
      "id": "phase1",
      "name": "Initial Analysis",
      "agents": ["research-analyst"],
      "dependencies": [],
      "timeout": 120,
      "output_path": "shared/phase1/",
      "task_template": "分析：{target}"
    },
    {
      "id": "phase2",
      "name": "Deep Dive",
      "agents": ["architect", "doc-engineer"],
      "dependencies": ["phase1"],
      "timeout": 180,
      "output_path": "shared/phase2/",
      "parallel": true
    }
  ]
}
EOF

# 执行自定义工作流
bash orchestrator-v3-supervisor.sh execute \
  --workflow-file custom-workflow.json \
  --params '{"target": "My Analysis Target"}' \
  --shared-dir /tmp/custom-shared
```

## Agent配置规范

### 强制规则

1. **不覆盖预配置模型**
   ```bash
   # ❌ 错误
   sessions_spawn agentId=research-analyst model=openai/gpt-5.3-codex
   
   # ✅ 正确
   sessions_spawn agentId=research-analyst  # 使用预配置的 xai/grok-4.1-thinking
   ```

2. **Supervisor只协调**
   - ✅ 允许：任务分解、agent分配、进度监控、结果聚合
   - ❌ 禁止：文档分析、代码生成、研究执行、复杂计算

3. **标准化输出**
   - 所有agent必须输出到指定的 `output_path`
   - 必须包含 `metadata.json`
   - 文件命名规范：`{agent_id}-{output_type}.md`

## 监控和调试

### 查看工作流状态

```bash
# 查看当前活跃的工作流
bash orchestrator-v3-supervisor.sh status

# 查看特定任务的详细状态
bash orchestrator-v3-supervisor.sh status --task-id TASK-001

# 查看队列状态
bash orchestrator-v3-supervisor.sh queue
```

### 日志查看

```bash
# 查看orchestrator日志
tail -f /tmp/task-orchestrator/logs/orchestrator.log | jq '.'

# 查看特定agent日志
tail -f /tmp/task-orchestrator/logs/subagent-doc-engineer.log | jq '.'

# 实时监控（带高亮）
bash task-orchestrator/log-analyzer-integration.sh monitor
```

## 最佳实践

1. **选择合适的工作流**
   - 文档分析 → `document_analysis`
   - 技术评估 → `tech_evaluation`
   - 代码审查 → `code_review`
   - UI设计 → `ui_design`

2. **合理设置超时**
   - 简单任务：60-90秒
   - 中等任务：120-180秒
   - 复杂任务：180-300秒

3. **利用并行执行**
   - 独立任务使用 `parallel: true`
   - 减少总执行时间
   - 提高资源利用率

4. **监控和日志**
   - 使用结构化日志
   - 定期查看监控状态
   - 及时处理异常

5. **错误处理**
   - 设置合理的重试次数
   - 实现降级策略
   - 记录详细错误信息

---

*文档版本: v3.0*
*更新时间: 2026-03-06*