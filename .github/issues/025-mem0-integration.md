# Issue #025: Mem0记忆系统集成

**里程碑**: Milestone 5: V0.0.5  
**优先级**: High  
**估时**: 4天  
**依赖**: #018 (用户偏好学习系统)  
**状态**: 📋 待开始  
**创建日期**: 2026-03-06

---

## 描述

集成火山引擎Mem0作为Task Orchestrator的统一记忆层，实现跨Agent记忆共享和跨会话状态持久化。

### 背景

基于记忆系统升级评估报告 (`docs/MEMORY-SYSTEM-EVALUATION.md`)，Mem0是最适合当前环境的方案：

- ✅ 支持10个Agent的跨Agent记忆共享
- ✅ 提供跨会话状态持久化能力（Item 7核心需求）
- ✅ 准确率提升120%，Token消耗降低59%
- ✅ 企业级可靠性（字节跳动火山引擎）
- ✅ ROI 96%，首月回本

### 目标

1. 安装并配置openclaw-mem0-plugin插件
2. 为10个Agent配置统一的userId策略
3. 实现单Agent记忆存储/召回功能
4. 实现跨Agent记忆共享功能
5. 实现跨会话持久化功能
6. 验证性能提升（Token消耗、准确率）
7. 配置监控告警
8. 更新相关文档

---

## 验收标准

- [ ] **插件安装**: Mem0插件安装并配置完成
- [ ] **Agent配置**: 10个Agent配置统一userId策略
- [ ] **单Agent功能**: 单Agent记忆存储/召回功能正常
- [ ] **跨Agent功能**: 跨Agent记忆共享功能正常
- [ ] **跨会话功能**: 跨会话持久化功能正常
- [ ] **性能验证**: Token消耗降低≥50%
- [ ] **准确率验证**: 准确率提升≥100%
- [ ] **监控配置**: 监控告警配置完成
- [ ] **文档更新**: 相关文档更新完成

---

## 实现计划

### Day 1: 准备阶段 (2026-03-08)

**任务**:
1. 确认火山引擎Mem0账号和API Key
2. 创建Mem0项目并配置自定义prompt
3. 测试API连通性
4. 准备配置文件模板

**输出**:
- Mem0项目创建完成
- API Key获取并安全存储
- 连通性测试通过
- 配置文件模板准备完成

### Day 2: 插件安装与配置 (2026-03-08)

**任务**:
1. 安装openclaw-mem0-plugin插件
2. 配置主Agent的Mem0连接
3. 为10个Agent配置userId策略
4. 重启OpenClaw网关

**配置示例**:
```json
{
  "plugins": {
    "entries": {
      "openclaw-mem0-plugin": {
        "enabled": true,
        "config": {
          "mode": "platform",
          "apiKey": "your_api_key",
          "userId": "task-orchestrator-main",
          "host": "mem0_platform_addr"
        }
      }
    }
  }
}
```

**userId策略**:
- 主Agent: `task-orchestrator-main`
- architect: `task-orchestrator-architect`
- doc-engineer: `task-orchestrator-doc-engineer`
- research-analyst: `task-orchestrator-research-analyst`
- ... (其他7个Agent)

**输出**:
- 插件安装完成
- 配置文件更新完成
- 网关重启成功
- 所有Agent可正常启动

### Day 3: 验证测试 (2026-03-09)

**测试1: 单Agent记忆测试**
```bash
# 测试记忆存储
openclaw mem0 search "test memory storage"

# 测试记忆召回
# 在新会话中验证记忆是否保留
```

**测试2: 跨Agent记忆共享测试**
```bash
# research-analyst存储调研结果
# architect读取调研结果
# 验证记忆是否成功共享
```

**测试3: 跨会话持久化测试**
```bash
# 会话1: 存储项目上下文
# 关闭会话
# 会话2: 验证上下文是否保留
```

**测试4: Token消耗对比测试**
```bash
# 记录集成前的Token消耗基准
# 执行相同任务
# 对比Token消耗差异
# 目标: 降低≥50%
```

**测试5: 准确率对比测试**
```bash
# 使用多跳推理问题测试
# 对比集成前后的准确率
# 目标: 提升≥100%
```

**输出**:
- 5项测试全部通过
- 测试报告生成
- 性能数据记录

### Day 4: 生产部署与文档 (2026-03-09)

**任务**:
1. 配置监控告警（Token用量、API错误率）
2. 更新SKILL.md文档
3. 更新README.md
4. 创建Mem0使用指南
5. 提交代码并推送到GitHub

**监控配置**:
- Token用量告警: 超过预算80%时告警
- API错误率告警: 错误率>5%时告警
- 延迟告警: P95延迟>500ms时告警

**文档更新**:
- `SKILL.md`: 添加Mem0记忆系统说明
- `README.md`: 更新架构图和特性列表
- `docs/MEM0-GUIDE.md`: 创建Mem0使用指南
- `docs/MEMORY-SYSTEM-EVALUATION.md`: 已完成

**输出**:
- 监控告警配置完成
- 文档更新完成
- 代码提交并推送
- Issue #025关闭

---

## 技术细节

### 集成架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Task Orchestrator                         │
│  (Supervisor + 10 Agents + 工作流引擎 + 监控系统)            │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    ┌───────────────┐
                    │  Mem0 Plugin  │
                    │  (统一记忆层)  │
                    └───────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌──────────────────┐                  ┌──────────────────┐
│  情境记忆层       │                  │  语义记忆层       │
│  (会话上下文)     │                  │  (长期知识)       │
└──────────────────┘                  └──────────────────┘
        ↓                                       ↓
┌─────────────────────────────────────────────────────────────┐
│           火山引擎 Mem0 Cloud (托管服务)                      │
│  - 向量检索                                                  │
│  - 自动去重合并                                              │
│  - 跨会话/跨Agent共享                                        │
│  - 监控告警                                                  │
└─────────────────────────────────────────────────────────────┘
```

### 10个Agent的userId配置

| Agent ID | userId | 用途 |
|---------|--------|------|
| main | task-orchestrator-main | 主Agent，任务分解 |
| architect | task-orchestrator-architect | 架构设计 |
| doc-engineer | task-orchestrator-doc-engineer | 文档工程 |
| research-analyst | task-orchestrator-research-analyst | 技术调研 |
| implementation-planner | task-orchestrator-implementation-planner | 实施规划 |
| ui-designer | task-orchestrator-ui-designer | UI/UX设计 |
| code-reviewer | task-orchestrator-code-reviewer | 代码审查 |
| security-monitor | task-orchestrator-security-monitor | 安全监控 |
| resource-manager | task-orchestrator-resource-manager | 资源管理 |
| strategic-advisor | task-orchestrator-strategic-advisor | 战略决策 |

### 自定义Prompt配置

推荐在Mem0控制台配置以下prompt：

```
你是一个Task Orchestrator系统的记忆提取专家，要求从对话中提取以下信息：

1. 项目上下文（项目名称、目标、状态）
2. 技术决策（架构选择、技术栈、关键决策）
3. 用户偏好（工作习惯、沟通风格、优先级）
4. 任务状态（进行中的任务、已完成的任务、待办事项）
5. 问题与解决方案（遇到的问题、解决方案、经验教训）

输出格式：
{
  "facts": [
    "项目名称: XXX",
    "技术栈: XXX",
    "当前状态: XXX",
    "关键决策: XXX",
    "用户偏好: XXX"
  ]
}
```

---

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| API稳定性问题 | 低 | 高 | 火山引擎SLA保障 + 本地缓存降级 |
| 成本超预算 | 中 | 中 | Token节省可抵消 + 设置用量告警 |
| 集成兼容性 | 低 | 中 | 官方插件 + 充分测试 |
| 数据隐私 | 低 | 高 | 企业级加密 + 权限控制 |
| 迁移成本 | 中 | 低 | 保留原生记忆作为备份 |

---

## 成本估算

**月度成本** (保守估计):
- 托管费: ¥500
- API调用 (10万次): ¥100
- 存储 (10GB): ¥1
- **总计**: ¥601/月

**预期收益**:
- Token节省 (59%): ¥1180/月
- **净收益**: ¥579/月
- **ROI**: 96%

---

## 参考资料

- [记忆系统升级评估报告](../docs/MEMORY-SYSTEM-EVALUATION.md)
- [MemMachine外挂大脑方案](https://my.feishu.cn/wiki/IeRywIJbeinwJTkl7Qgc8fdan0e)
- [Mem0内置企业级方案](https://my.feishu.cn/wiki/FIFHwuoHtiLa2akyY8ocvOqNnah)
- [火山引擎Mem0产品页](https://www.volcengine.com/product/mem0)
- [火山引擎Mem0文档](https://www.volcengine.com/docs/86722/1884417)

---

## 更新日志

- 2026-03-06: Issue创建，等待Milestone 4完成后启动
