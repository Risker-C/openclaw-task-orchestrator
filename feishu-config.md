# OpenClaw飞书配置指南

## 📋 概述

本文档说明如何配置OpenClaw的飞书集成，以支持Task Orchestrator的Bitable和消息功能。

## 🚀 OpenClaw飞书配置

### 1. 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 获取 `App ID` 和 `App Secret`

### 2. 配置应用权限

在应用管理页面，添加以下权限：

**机器人权限**:
- `im:message` - 发送消息
- `im:message.group_at_msg` - 群组@消息
- `im:chat` - 获取群组信息

**多维表格权限**:
- `bitable:app` - 访问多维表格应用
- `bitable:app:readonly` - 读取多维表格
- `bitable:app:readwrite` - 读写多维表格

**文档权限**:
- `docx:document` - 访问文档
- `docx:document:readonly` - 读取文档
- `docx:document:readwrite` - 读写文档

### 3. OpenClaw配置文件

在OpenClaw的配置文件中添加飞书账户配置：

#### 配置文件位置
- Linux: `~/.openclaw/config.yaml`
- macOS: `~/.openclaw/config.yaml`
- Windows: `%USERPROFILE%\.openclaw\config.yaml`

#### 配置示例
```yaml
channels:
  feishu:
    accounts:
      main:
        appId: "cli_xxxxxxxxxx"
        appSecret: "your_app_secret_here"
        domain: "feishu"  # 或 "lark" (国际版)
        # 可选配置
        defaultChatId: "oc_xxxxxxxxxx"  # 默认通知群组
```

#### 多账户配置
```yaml
channels:
  feishu:
    accounts:
      main:
        appId: "cli_xxxxxxxxxx"
        appSecret: "your_main_app_secret"
        domain: "feishu"
      work:
        appId: "cli_yyyyyyyyyy"
        appSecret: "your_work_app_secret"
        domain: "feishu"
    # 默认使用的账户
    defaultAccount: "main"
```

### 4. 环境变量配置（可选）

也可以通过环境变量配置：

```bash
export OPENCLAW_FEISHU_APP_ID="cli_xxxxxxxxxx"
export OPENCLAW_FEISHU_APP_SECRET="your_app_secret_here"
export OPENCLAW_FEISHU_DOMAIN="feishu"
```

## 📊 Bitable表格设置

### 1. 创建多维表格应用

1. 在飞书中创建新的多维表格
2. 复制应用Token（URL中的app_token部分）
3. 创建"任务管理"数据表
4. 复制表格ID（URL中的table参数）

### 2. 配置必需字段

Task Orchestrator需要以下字段：

| 字段名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| 任务ID | 单行文本 | ✅ | 唯一标识符 |
| 任务标题 | 单行文本 | ✅ | 任务名称 |
| 任务描述 | 多行文本 | ✅ | 详细描述 |
| 复杂度 | 单选 | ✅ | L1/L2/L3 |
| 状态 | 单选 | ✅ | 待处理/进行中/已完成/失败 |
| 优先级 | 单选 | ❌ | 低/中/高/紧急 |
| 分配Agent | 单行文本 | ✅ | 负责的Agent |
| 创建时间 | 日期时间 | ❌ | 自动填充 |
| 更新时间 | 日期时间 | ❌ | 自动更新 |
| 进度百分比 | 数字 | ❌ | 0-100 |
| Token消耗 | 数字 | ❌ | 资源统计 |
| 结果文档 | 超链接 | ❌ | 文档链接 |

### 3. 单选字段选项配置

**复杂度字段选项**:
- L1 (简单)
- L2 (中等)  
- L3 (复杂)

**状态字段选项**:
- 待处理
- 进行中
- 已完成
- 失败
- 已取消

**优先级字段选项**:
- 低
- 中
- 高
- 紧急

### 4. 创建看板视图

1. 创建新视图，选择"看板"
2. 按"状态"字段分组
3. 设置筛选条件（可选）
4. 保存视图设置

## 🔧 OpenClaw工具使用

### 验证配置

使用OpenClaw的feishu工具验证配置：

```javascript
// 测试Bitable连接
feishu_bitable_get_meta({
  url: "https://your-domain.feishu.cn/base/your_app_token?table=your_table_id"
})

// 测试消息发送
message({
  action: "send",
  message: "配置测试消息",
  channel: "feishu"
})
```

### 获取配置信息

```javascript
// 查看当前飞书应用权限
feishu_app_scopes()

// 获取Bitable表格字段信息
feishu_bitable_list_fields({
  app_token: "your_app_token",
  table_id: "your_table_id"
})
```

## 🚨 故障排除

### 常见错误

**1. 认证失败**
```
❌ auth failed: {"code": 99991663, "msg": "app access token invalid"}
```
**解决方案**:
- 检查 `appId` 和 `appSecret` 是否正确
- 确认应用状态为"已启用"
- 验证配置文件格式是否正确

**2. 权限不足**
```
❌ permission denied: {"code": 230002, "msg": "permission denied"}
```
**解决方案**:
- 检查应用权限配置
- 确认机器人已加入目标群组
- 验证Bitable应用的访问权限

**3. 表格不存在**
```
❌ app not found: {"code": 1254006, "msg": "app not found"}
```
**解决方案**:
- 检查 `app_token` 和 `table_id` 是否正确
- 确认应用有访问该表格的权限
- 验证表格是否已删除或移动

### 调试方法

**1. 检查OpenClaw日志**
```bash
# 查看OpenClaw日志
openclaw gateway logs

# 过滤飞书相关日志
openclaw gateway logs | grep feishu
```

**2. 测试工具调用**
```javascript
// 在OpenClaw中测试单个工具
feishu_app_scopes()  // 查看权限
```

**3. 验证网络连接**
```bash
# 测试飞书API连接
curl -H "Authorization: Bearer your_token" \
  https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal
```

## 🔐 安全注意事项

### 1. 敏感信息保护
- **不要将 `appSecret` 提交到版本控制**
- **使用环境变量存储敏感配置**
- **定期轮换应用密钥**

### 2. 权限最小化
- **只申请必要的API权限**
- **定期审查权限使用情况**
- **限制应用访问范围**

### 3. 网络安全
- **使用HTTPS进行API调用**
- **验证SSL证书**
- **设置合理的超时时间**

## 📚 参考资源

- [飞书开放平台文档](https://open.feishu.cn/document/)
- [多维表格API](https://open.feishu.cn/document/server-docs/docs/bitable-v1/)
- [消息API](https://open.feishu.cn/document/server-docs/im-v1/message/)
- [OpenClaw官方文档](https://docs.openclaw.ai)

## ✅ 配置检查清单

完成配置后，请确认以下项目：

- [ ] 飞书应用已创建并获取App ID和App Secret
- [ ] 应用权限已正确配置（机器人、Bitable、文档权限）
- [ ] OpenClaw配置文件已更新
- [ ] Bitable表格已创建并配置必需字段
- [ ] 单选字段选项已设置
- [ ] 看板视图已创建
- [ ] 配置测试通过

**配置完成后，Task Orchestrator就可以使用OpenClaw的原生飞书工具了！** 🎉