# agent/tool_registry.py
from typing import Dict, Callable, Any
from langchain_core.tools import tool as langchain_tool

# 全局工具注册表
_TOOL_REGISTRY: Dict[str, Any] = {}

def register_tool(name: str = None):
    """
    装饰器：注册工具到全局注册表。
    用法：@register_tool(name="optional_name")  # name可选，默认为函数名
    """
    def decorator(func: Callable):
        # 首先使用 LangChain 的 @tool 装饰器包装函数
        tool_obj = langchain_tool(func)
        tool_name = name if name is not None else tool_obj.name
        # 存入注册表
        _TOOL_REGISTRY[tool_name] = tool_obj
        return tool_obj
    return decorator

def get_all_tools() -> list:
    """返回所有已注册的工具列表"""
    return list(_TOOL_REGISTRY.values())

def get_tool(name: str):
    """根据名称获取工具"""
    return _TOOL_REGISTRY.get(name)