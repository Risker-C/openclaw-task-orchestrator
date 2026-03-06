# 飞书文档操作最佳实践

**来源**: 从 feishu-strategic-agent v2.5 提取的经验总结

---

## 🚨 核心原则

### 1. 强制 Subagent 执行

**问题**: 主会话执行飞书操作会阻断主流程响应，长时间 API 调用让用户等待。

**解决方案**: 所有飞书文档操作必须通过 `sessions_spawn` 启动 `doc-engineer` subagent 执行。

```javascript
// ✅ 正确：通过 doc-engineer subagent 执行
sessions_spawn({
  agentId: "doc-engineer",
  mode: "run",
  model: "openai/gpt-5.3-codex",
  task: `
使用飞书工具执行以下任务：
1. 读取飞书 Wiki
2. 生成本地校对文件
3. 按顺序写入：标题 -> 表格 -> 脚注
4. 提供详细统计反馈

所有工具调用必须添加 accountId: "main"
  `
});

// ❌ 错误：主会话直接执行（会阻断响应）
const blocks = await feishu_doc.list_blocks({ accountId: "main", doc_token: "xxx" });
```

**执行流程**:
```
用户请求 → 主会话接收 → sessions_spawn doc-engineer →
doc-engineer 执行飞书操作 → subagent 返回结果 → 主会话响应用户
```

**强制检查清单**:
- [ ] 是否在 subagent 中执行？
- [ ] 是否使用 `sessions_spawn`？
- [ ] 是否指定 `agentId: "doc-engineer"`？
- [ ] 是否设置 `model: "openai/gpt-5.3-codex"`？

---

## 📋 详细统计反馈

每次任务完成后，必须提供统计报告：

```markdown
## 📊 任务执行统计

### 基础指标
- **总耗时**: 45s
- **API 调用总数**: 12 次
- **字符总数**: 3,450 字符
- **Block 操作数**: 8 个

### 详细分解
- **读取操作**: 3 次（list_blocks × 2, read × 1）
- **写入操作**: 7 次（append × 5, Python脚本创建表格 × 2）
- **删除操作**: 0 次
- **表格创建**: 2 个（3×3 和 5×3 原生表格）

### 数据完整性
- ✅ 本地校对完成（/tmp/feishu_sync_20260228_101234.md）
- ✅ 无乱码字符
- ✅ 表格数据对齐
- ✅ 顺序逻辑正确（标题→表格→脚注）
```

---

## 🔍 预读校验

在任何写入/修改操作前，必须先执行校验流程：

```javascript
// Step 1: 获取文档现有结构
const blocks = await feishu_doc.list_blocks({
  accountId: "main",
  doc_token: "xxx"
});

// Step 2: 读取关键内容
const content = await feishu_doc.read({
  accountId: "main",
  doc_token: "xxx"
});

// Step 3: 检查是否存在重复内容
const hasTable = blocks.blocks.some(b => b.block_type === 31);
const hasTitle = content.includes("投资策略建议表");

// Step 4: 决策
if (hasTitle && hasTable) {
  console.log("⚠️ 检测到重复内容，跳过写入或执行更新");
  return;
}
```

**校验清单**:
- [ ] 获取当前 block 列表
- [ ] 读取关键段落内容
- [ ] 检查是否存在重复标题
- [ ] 检查是否存在重复表格
- [ ] 确认最后一个 block 的位置和类型
- [ ] 决定是追加、更新还是跳过

---

## 📏 严格顺序控制

**问题**: 表格在标题前面的顺序错误。

**原因**:
1. Python 脚本 `insert_native_table_fixed.py` 默认使用 `index: -1`（追加到末尾）
2. `feishu_doc.append` 也追加到末尾
3. 如果先调用 Python 脚本再调用 append，就会导致顺序错误

**解决方案 - 严格线性追加**:

```javascript
// Step 1: 追加标题
await feishu_doc.append({
  accountId: "main",
  doc_token: "xxx",
  content: "### 投资策略建议表"
});

// Step 2: 追加说明
await feishu_doc.append({
  accountId: "main",
  doc_token: "xxx",
  content: "以下表格展示针对不同类型投资者的策略建议："
});

// Step 3: 创建表格（会追加到说明后面）
await exec({
  command: `python3 insert_native_table_fixed.py xxx 4 3 '[[...]]'`
});

// Step 4: 追加脚注
await feishu_doc.append({
  accountId: "main",
  doc_token: "xxx",
  content: "---\n\n**免责声明**: ..."
});
```

**强制规则**:
- ✅ 标题必须先于表格追加
- ✅ 表格必须先于脚注追加
- ✅ 所有操作必须遵循线性时间顺序
- ❌ 禁止使用 `index` 参数插入到中间位置（API 不稳定）

---

## 📝 本地校对流程

在执行飞书同步前，必须先生成本地校对文档。

### Step 1: 生成本地文件

```javascript
const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
const localPath = `/tmp/feishu_sync_${timestamp}.md`;

await write({
  path: localPath,
  content: `# 报告标题

## 章节1
内容...

## 投资策略建议表

| 投资策略 | 适用人群 | 操作建议 |
|---------|---------|---------|
| 分批建仓 | 稳健投资者 | 回调时逐步增持 |

---

**免责声明**: 本报告仅供参考...
`
});

console.log(`✅ 本地校对文件已生成: ${localPath}`);
```

### Step 2: 自动校对

```javascript
const content = await read({ path: localPath });

const checks = {
  hasGarbledText: /[^\u4e00-\u9fa5\u0020-\u007e\n\r\t]/.test(content),
  hasMissingTitle: !content.includes("投资策略建议表"),
  hasIncompleteTable: (content.match(/\|/g) || []).length < 12,
  hasMissingDisclaimer: !content.includes("免责声明")
};

if (Object.values(checks).some(v => v === true)) {
  console.log("⚠️ 校对发现问题，请修复后再同步");
  console.log(checks);
  return;
}

console.log("✅ 校对通过，准备同步到飞书");
```

### Step 3: 同步到飞书

校对通过后，按照"严格顺序控制"规则同步到飞书。

---

## 🎯 性能标准

- 🟢 **Level 1（简单）**: ≤60秒 - 读取、追加、单表格
- 🟡 **Level 2（中等）**: ≤120秒 - 多表格、文档重组
- 🔴 **Level 3（复杂）**: ≤180秒 - 递归读取、大规模重构

---

## 🔧 强制配置

所有飞书工具调用必须使用：
- `accountId: "main"`
- Wiki 类型检查：只处理 `/wiki/` 类型链接
- 修复版脚本：`/root/.openclaw/workspace/insert_native_table_fixed.py`

---

**总结**: 通过 subagent 执行、预读校验、严格顺序、本地校对，确保飞书文档操作的可靠性和数据完整性。
