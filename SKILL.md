---
name: task-orchestrator
description: 异步任务编排系统，解决主Agent阻塞问题。使用场景：(1) 复杂任务需要多Agent协作时，(2) 长耗时任务需要异步执行时，(3) 需要飞书工单可视化管理时，(4) 用户明确要求"使用Task Orchestrator"或"任务编排"时。支持L1/L2/L3复杂度分流，事件驱动执行，飞书Bitable状态同步。
---

# OpenClaw Task Orchestrator

**基于 OpenClaw 原生工具的异步任务编排 Skill（文档驱动、单一版本维护）**

## 🎯 核心目标

把“阻塞式对话执行”改造成“异步工单执行”：

```text
用户请求 → 主Agent即时响应并建单 → 后台Agent并行处理 → 飞书看板同步 → 结果通知
```

主Agent始终可交互，不因长任务阻塞。

## 🧠 核心能力

1. **复杂度分流（L1/L2/L3）**
   - L1：直接处理或单步处理
   - L2：单专业Agent处理
   - L3：拆分子任务，多Agent协作

2. **异步工单机制（飞书Bitable）**
   - 创建任务记录、推进状态、记录进度
   - 可视化看板与状态追踪

3. **事件驱动执行（sessions_send 优先）**
   - 优先使用稳定通信路径
   - 支持失败重试与主Agent兜底

4. **智能监控系统（按需启动）**
   - 零token消耗的subagent失败检测
   - 按需启停，没有任务时零资源消耗
   - 30秒内检测状态变化并自动恢复

5. **数据准确性保障**
   - 时间字段必须写入（创建/更新/完成）
   - 必填字段完整性校验

## ⚙️ 标准执行流程（SOP）

1. 解析需求并判断复杂度
2. 选择Agent与执行模式
3. 创建飞书工单（状态=待处理）
4. 分发执行（单Agent或多Agent）
5. 实时回写状态（处理中/阻塞中/已完成）
6. 汇总结果并通知
7. 写入复盘信息（失败原因/恢复策略/耗时）

## 🧩 十项目技巧映射（上午沉淀）

已将上午十个参考项目的可复用技巧整理为可执行规则，见：

- [十项目技巧映射](project-techniques.md)

> 仅保留“可落地、可验证、低冗余”的技巧；避免过度工程化。

## 🛠 OpenClaw 原生工具约束

- 工单与状态：`feishu_bitable_*`
- 消息通知：`message`
- Agent调度：`sessions_send`（必要时 `sessions_spawn`）
- 知识/文档：`feishu_doc` / `feishu_wiki`

禁止重复实现与上述原生能力重叠的私有脚本。

## 📍 文档创建位置约束

如需创建飞书文档，必须在指定 Wiki Space：
- `space_id = 7606712982797552581`

## ✅ 质量门槛

- 状态字段完整率：100%
- 时间字段完整率：100%
- 异常任务可恢复率：≥95%
- 主Agent响应：不因后台任务阻塞

## 📚 相关文档

- [复杂度判断指南](complexity-guide.md)
- [Agent选择规则](agent-selection.md)
- [执行模板](execution-templates.md)
- [飞书配置说明](feishu-config.md)
- [飞书文档最佳实践](FEISHU-DOC-BEST-PRACTICES.md)
- [使用示例](examples.md)
- [十项目技巧映射](project-techniques.md)
- [Subagent监控系统](monitoring-system.md)

---

**OpenClaw Task Orchestrator：异步优先、事件驱动、数据准确、持续可用。**
