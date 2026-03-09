# ApiCargo MCP Server
# 通过 MCP 协议�?AI Agent 完全控制 ApiCargo

import asyncio
import json
import os
from typing import Any, Optional
from urllib.parse import urljoin

import httpx
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool
from starlette.applications import Starlette
from starlette.routing import Mount, Route

# ApiCargo API 配置
ApiCargo_API_BASE = os.getenv("ApiCargo_API_BASE", "http://localhost:8082")


class ApiCargoClient:
    """ApiCargo 管理 API 客户�?""
    
    def __init__(self, base_url: str = ApiCargo_API_BASE):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """发�?HTTP 请求�?ApiCargo API"""
        url = urljoin(f"{self.base_url}/", path.lstrip("/"))
        response = await self.client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    # ========== Providers ==========
    
    async def list_providers(self) -> list[dict]:
        """列出所有服务商"""
        result = await self._request("GET", "/api/management/providers")
        return result.get("data", [])
    
    async def get_provider(self, provider_id: str) -> dict:
        """获取单个服务商详�?""
        result = await self._request("GET", f"/api/management/providers/{provider_id}")
        return result.get("data", {})
    
    async def add_provider(self, name: str, api_base_url: str, api_key: str, 
                          models: list[str], provider_type: str = "openai") -> dict:
        """创建新服务商"""
        data = {
            "name": name,
            "apiBaseUrl": api_base_url,
            "apiKey": api_key,
            "models": models,
            "type": provider_type,
            "isEnabled": True
        }
        result = await self._request("POST", "/api/management/providers", json=data)
        return result.get("data", {})
    
    async def update_provider(self, provider_id: str, **kwargs) -> dict:
        """更新服务�?""
        result = await self._request("PUT", f"/api/management/providers/{provider_id}", json=kwargs)
        return result.get("data", {})
    
    async def delete_provider(self, provider_id: str) -> dict:
        """删除服务�?""
        result = await self._request("DELETE", f"/api/management/providers/{provider_id}")
        return result.get("data", {})
    
    async def test_provider(self, provider_id: str) -> dict:
        """测试服务商连通�?""
        result = await self._request("POST", f"/api/management/providers/{provider_id}/test")
        return result.get("data", {})
    
    # ========== SubKeys ==========
    
    async def list_subkeys(self, page: int = 1, page_size: int = 20) -> dict:
        """列出所有子 Key"""
        result = await self._request("GET", "/api/management/subkeys", 
                                     params={"page": page, "pageSize": page_size})
        return result.get("data", {})
    
    async def get_subkey(self, subkey_id: str) -> dict:
        """获取�?Key 详情"""
        result = await self._request("GET", f"/api/management/subkeys/{subkey_id}")
        return result.get("data", {})
    
    async def create_subkey(self, name: str, provider_ids: list[str], 
                           daily_limit: Optional[int] = None,
                           monthly_limit: Optional[int] = None,
                           allowed_models: Optional[list[str]] = None) -> dict:
        """创建�?Key"""
        data = {
            "name": name,
            "providerIds": provider_ids,  # 驼峰命名
            "isEnabled": True
        }
        if daily_limit is not None:
            data["dailyLimit"] = daily_limit  # 驼峰命名
        if monthly_limit is not None:
            data["monthlyLimit"] = monthly_limit  # 驼峰命名
        if allowed_models is not None:
            data["allowedModels"] = allowed_models  # 驼峰命名
        
        result = await self._request("POST", "/api/management/subkeys", json=data)
        return result.get("data", {})
    
    async def update_subkey(self, subkey_id: str, **kwargs) -> dict:
        """更新�?Key"""
        result = await self._request("PUT", f"/api/management/subkeys/{subkey_id}", json=kwargs)
        return result.get("data", {})
    
    async def delete_subkey(self, subkey_id: str) -> dict:
        """删除�?Key"""
        result = await self._request("DELETE", f"/api/management/subkeys/{subkey_id}")
        return result.get("data", {})
    
    async def regenerate_subkey(self, subkey_id: str) -> dict:
        """重新生成�?Key"""
        result = await self._request("POST", f"/api/management/subkeys/{subkey_id}/regenerate")
        return result.get("data", {})
    
    # ========== Settings ==========
    
    async def get_settings(self) -> dict:
        """获取全局设置"""
        result = await self._request("GET", "/api/management/settings")
        return result.get("data", {})
    
    async def update_settings(self, **kwargs) -> dict:
        """更新全局设置"""
        result = await self._request("PUT", "/api/management/settings", json=kwargs)
        return result.get("data", {})
    
    # ========== Stats ==========
    
    async def get_stats(self) -> dict:
        """获取用量统计概览"""
        result = await self._request("GET", "/api/management/stats")
        return result.get("data", {})
    
    async def get_daily_stats(self) -> list[dict]:
        """获取每日统计"""
        result = await self._request("GET", "/api/management/stats/daily")
        return result.get("data", [])
    
    async def get_stats_by_subkey(self) -> list[dict]:
        """按子 Key 统计"""
        result = await self._request("GET", "/api/management/stats/by-subkey")
        return result.get("data", [])
    
    async def get_stats_by_provider(self) -> list[dict]:
        """按服务商统计"""
        result = await self._request("GET", "/api/management/stats/by-provider")
        return result.get("data", [])


# 创建 MCP Server
app = Server("ApiCargo-mcp")
ApiCargo = ApiCargoClient()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工�?""
    return [
        # Providers
        Tool(
            name="list_providers",
            description="列出所有服务商 (Providers)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_provider",
            description="获取单个服务商详�?,
            inputSchema={
                "type": "object",
                "properties": {
                    "provider_id": {"type": "string", "description": "服务�?ID"}
                },
                "required": ["provider_id"]
            }
        ),
        Tool(
            name="add_provider",
            description="添加新服务商",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "服务商名�?},
                    "api_base_url": {"type": "string", "description": "API 基础地址"},
                    "api_key": {"type": "string", "description": "API Key"},
                    "models": {"type": "array", "items": {"type": "string"}, "description": "支持的模型列�?},
                    "provider_type": {"type": "string", "description": "服务商类�?, "default": "openai"}
                },
                "required": ["name", "api_base_url", "api_key", "models"]
            }
        ),
        Tool(
            name="update_provider",
            description="更新服务商配�?,
            inputSchema={
                "type": "object",
                "properties": {
                    "provider_id": {"type": "string", "description": "服务�?ID"},
                    "name": {"type": "string", "description": "新名�?},
                    "api_base_url": {"type": "string", "description": "�?API 地址"},
                    "api_key": {"type": "string", "description": "�?API Key"},
                    "models": {"type": "array", "items": {"type": "string"}, "description": "新模型列�?},
                    "is_enabled": {"type": "boolean", "description": "是否启用"}
                },
                "required": ["provider_id"]
            }
        ),
        Tool(
            name="delete_provider",
            description="删除服务�?,
            inputSchema={
                "type": "object",
                "properties": {
                    "provider_id": {"type": "string", "description": "服务�?ID"}
                },
                "required": ["provider_id"]
            }
        ),
        Tool(
            name="test_provider",
            description="测试服务商连通�?,
            inputSchema={
                "type": "object",
                "properties": {
                    "provider_id": {"type": "string", "description": "服务�?ID"}
                },
                "required": ["provider_id"]
            }
        ),
        
        # SubKeys
        Tool(
            name="list_subkeys",
            description="列出所有子 Key",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "页码", "default": 1},
                    "page_size": {"type": "integer", "description": "每页数量", "default": 20}
                }
            }
        ),
        Tool(
            name="get_subkey",
            description="获取�?Key 详情",
            inputSchema={
                "type": "object",
                "properties": {
                    "subkey_id": {"type": "string", "description": "�?Key ID"}
                },
                "required": ["subkey_id"]
            }
        ),
        Tool(
            name="create_subkey",
            description="创建�?Key",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "�?Key 名称/备注"},
                    "provider_ids": {"type": "array", "items": {"type": "string"}, "description": "绑定的服务商 ID 列表"},
                    "daily_limit": {"type": "integer", "description": "日限额（tokens），null 表示无限�?},
                    "monthly_limit": {"type": "integer", "description": "月限额（tokens�?},
                    "allowed_models": {"type": "array", "items": {"type": "string"}, "description": "白名单模�?}
                },
                "required": ["name", "provider_ids"]
            }
        ),
        Tool(
            name="update_subkey",
            description="更新�?Key",
            inputSchema={
                "type": "object",
                "properties": {
                    "subkey_id": {"type": "string", "description": "�?Key ID"},
                    "name": {"type": "string", "description": "新名�?},
                    "provider_ids": {"type": "array", "items": {"type": "string"}, "description": "新绑定服务商"},
                    "daily_limit": {"type": "integer", "description": "新日限额"},
                    "monthly_limit": {"type": "integer", "description": "新月限额"},
                    "allowed_models": {"type": "array", "items": {"type": "string"}, "description": "新白名单"},
                    "is_enabled": {"type": "boolean", "description": "是否启用"}
                },
                "required": ["subkey_id"]
            }
        ),
        Tool(
            name="delete_subkey",
            description="删除�?Key",
            inputSchema={
                "type": "object",
                "properties": {
                    "subkey_id": {"type": "string", "description": "�?Key ID"}
                },
                "required": ["subkey_id"]
            }
        ),
        Tool(
            name="regenerate_subkey",
            description="重新生成�?Key",
            inputSchema={
                "type": "object",
                "properties": {
                    "subkey_id": {"type": "string", "description": "�?Key ID"}
                },
                "required": ["subkey_id"]
            }
        ),
        
        # Settings
        Tool(
            name="get_settings",
            description="获取全局设置",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="update_settings",
            description="更新全局设置",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt_compression_threshold": {"type": "integer", "description": "提示词压缩触发阈�?},
                    "response_cache_enabled": {"type": "boolean", "description": "是否启用响应缓存"},
                    "response_cache_ttl": {"type": "integer", "description": "缓存 TTL（秒�?},
                    "default_routing_strategy": {"type": "string", "description": "默认路由策略"}
                }
            }
        ),
        
        # Stats
        Tool(
            name="get_stats",
            description="获取用量统计概览",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_daily_stats",
            description="获取每日统计",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_stats_by_subkey",
            description="按子 Key 统计",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_stats_by_provider",
            description="按服务商统计",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """处理工具调用"""
    try:
        result = None
        
        # Providers
        if name == "list_providers":
            result = await ApiCargo.list_providers()
        elif name == "get_provider":
            result = await ApiCargo.get_provider(arguments["provider_id"])
        elif name == "add_provider":
            result = await ApiCargo.add_provider(
                name=arguments["name"],
                api_base_url=arguments["api_base_url"],
                api_key=arguments["api_key"],
                models=arguments["models"],
                provider_type=arguments.get("provider_type", "openai")
            )
        elif name == "update_provider":
            provider_id = arguments.pop("provider_id")
            result = await ApiCargo.update_provider(provider_id, **arguments)
        elif name == "delete_provider":
            result = await ApiCargo.delete_provider(arguments["provider_id"])
        elif name == "test_provider":
            result = await ApiCargo.test_provider(arguments["provider_id"])
        
        # SubKeys
        elif name == "list_subkeys":
            result = await ApiCargo.list_subkeys(
                page=arguments.get("page", 1),
                page_size=arguments.get("page_size", 20)
            )
        elif name == "get_subkey":
            result = await ApiCargo.get_subkey(arguments["subkey_id"])
        elif name == "create_subkey":
            result = await ApiCargo.create_subkey(
                name=arguments["name"],
                provider_ids=arguments["provider_ids"],
                daily_limit=arguments.get("daily_limit"),
                monthly_limit=arguments.get("monthly_limit"),
                allowed_models=arguments.get("allowed_models")
            )
        elif name == "update_subkey":
            subkey_id = arguments.pop("subkey_id")
            result = await ApiCargo.update_subkey(subkey_id, **arguments)
        elif name == "delete_subkey":
            result = await ApiCargo.delete_subkey(arguments["subkey_id"])
        elif name == "regenerate_subkey":
            result = await ApiCargo.regenerate_subkey(arguments["subkey_id"])
        
        # Settings
        elif name == "get_settings":
            result = await ApiCargo.get_settings()
        elif name == "update_settings":
            result = await ApiCargo.update_settings(**arguments)
        
        # Stats
        elif name == "get_stats":
            result = await ApiCargo.get_stats()
        elif name == "get_daily_stats":
            result = await ApiCargo.get_daily_stats()
        elif name == "get_stats_by_subkey":
            result = await ApiCargo.get_stats_by_subkey()
        elif name == "get_stats_by_provider":
            result = await ApiCargo.get_stats_by_provider()
        
        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]
        
        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
    
    except Exception as e:
        return [TextContent(type="text", text=f"错误: {str(e)}")]


# 创建 SSE 传输
sse = SseServerTransport("/messages")


async def handle_sse(request):
    """处理 SSE 连接"""
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await app.run(
            streams[0], streams[1], app.create_initialization_options()
        )


# 创建 Starlette 应用
starlette_app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages", app=sse.handle_post_message),
    ],
)


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("MCP_PORT", "3000"))
    print(f"[ApiCargo MCP] Server starting at http://localhost:{port}/sse")
    print(f"[ApiCargo MCP] API Base: {ApiCargo_API_BASE}")
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
