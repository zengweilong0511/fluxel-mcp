# ApiCargo MCP Server

通过 MCP 协议让 AI Agent 完全控制 ApiCargo API 路由器。

## 功能

- 管理 Providers（服务商）- 增删改查、连通性测试
- 管理 SubKeys（子 Key）- 创建、更新、限额设置、重新生成
- 全局设置 - 修改压缩阈值、缓存策略等
- 用量统计 - 查看请求数、Token 消耗、成本

## 安装

```bash
pip install -r requirements.txt
```

## 配置

环境变量：
- `APICARGO_API_BASE` - ApiCargo 管理 API 地址（默认：http://localhost:8082）
- `APICARGO_ADMIN_TOKEN` - 管理 API Token
- `MCP_PORT` - MCP Server 监听端口（默认：3000）

## 运行

```bash
python server.py
```

## 在 OpenClaw 中配置

编辑 `~/.openclaw/mcp.json`：

```json
{
  "mcpServers": {
    "apicargo": {
      "command": "python",
      "args": ["C:\\Users\\用户名\\apicargo\\server.py"],
      "env": {
        "APICARGO_API_BASE": "http://localhost:8082",
        "APICARGO_ADMIN_TOKEN": "flx_your_token"
      }
    }
  }
}
```

## 可用工具

### Providers
- `list_providers` - 列出所有服务商
- `get_provider` - 获取服务商详情
- `add_provider` - 添加服务商
- `update_provider` - 更新服务商
- `delete_provider` - 删除服务商
- `test_provider` - 测试连通性

### SubKeys
- `list_subkeys` - 列出子 Key
- `get_subkey` - 获取子 Key 详情
- `create_subkey` - 创建子 Key
- `update_subkey` - 更新子 Key
- `delete_subkey` - 删除子 Key
- `regenerate_subkey` - 重新生成 Key

### Settings
- `get_settings` - 获取全局设置
- `update_settings` - 更新设置

### Stats
- `get_stats` - 统计概览
- `get_daily_stats` - 每日统计
- `get_stats_by_subkey` - 按子 Key 统计
- `get_stats_by_provider` - 按服务商统计

## 示例对话

配置好后，你可以对 AI 说：

> "帮我看看 ApiCargo 里有哪些服务商"

> "给我创建一个新子 Key，绑定到阿里百炼，日限额 10000 tokens"

> "把提示词压缩阈值改成 3000"

## 许可证

MIT
