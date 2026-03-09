#from langchain_core.tools import tool
from langgraph.prebuilt.tool_node import ToolCallRequest

from agent.tool_registry import register_tool
from rag.vector_store import VectorStoreService
from rag.rag_service import RagSummarizeService
import random, os
from utils.config_handler import agent_conf
from utils.path_tool import get_abs_path
from utils.logger_handler import logger


vector_store = VectorStoreService()
rag = RagSummarizeService(vector_store)

user_ids = ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010",]
month_arr = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
             "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12", ]

external_data = {}

@register_tool()
def rag_summarize(query: str) -> str:
    """从向量存储中检索参考资料"""  # 函数文档字符串会被用作工具描述
    return rag.rag_summarize(query)


@register_tool()
def get_weather(city: str) -> str:
    """获取指定城市的天气，以消息字符形式返回"""
    return f"城市{city}天气为晴天，气温26摄氏度，空气湿度50%，南风1级，AQI21，最近6小时内降雨概率极低"


@register_tool()
def get_user_location() -> str:
    """获取用户所在城市名称，以纯字符形式返回"""
    return random.choice(["深圳", "合肥", "杭州"])


@register_tool()
def get_user_id() -> str:
    """获取用户ID，以纯字符形式返回"""
    return random.choice(user_ids)


@register_tool()
def get_current_month() -> str:
    """获取当前月份，以纯字符形式返回"""
    return random.choice(month_arr)


def generate_external_data():
    if not external_data:
        if "external_data_path" not in agent_conf:
            raise KeyError("配置中缺少 external_data_path 字段")

        external_data_path = get_abs_path(agent_conf["external_data_path"])

        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"外部数据文件不存在: {external_data_path}")

        with open(external_data_path, "r", encoding="utf-8") as f:
            for line in f.readlines()[1:]:
                arr = line.strip().split(",")

                user_id = arr[0].replace('"', "")
                feature = arr[1].replace('"', "")
                efficiency = arr[2].replace('"', "")
                consumables = arr[3].replace('"', "")
                comparison = arr[4].replace('"', "")
                time = arr[5].replace('"', "")

                if user_id not in external_data:
                    external_data[user_id] = {}

                external_data[user_id][time] = {
                    "房间特征": feature,
                    "运行效率": efficiency,
                    "耗材": consumables,
                    "对比": comparison,
                }



@register_tool()
def fetch_external_data(user_id: str, month: str) -> str:
    """检索指定用户在指定月份的智能空调完整使用记录，以纯字符形式返回，如未检索到返回空字符串"""
    generate_external_data()
    try:
        return external_data[user_id][month]
    except KeyError:
        logger.warn(f"[fetch_external_data]未能检索到用户:{user_id}在{month}的数据。")
        return ""


@register_tool()
def fill_context_for_report():
    """无入参，无返回值，调用后触发中间件自动为报告生成场景动态注入上下文信息，为后续提示词切换提供上下文支撑"""
    return "fill_context_for_report已调用"
