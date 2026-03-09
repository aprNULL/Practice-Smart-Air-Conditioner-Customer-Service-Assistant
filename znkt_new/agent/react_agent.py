from langchain.agents import create_agent
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch
from agent.tools.agent_tools import (
    rag_summarize, get_weather, get_user_location, get_user_id, get_current_month,
    fetch_external_data, fill_context_for_report
)
from model.factory import chat_model
from utils.prompt_loader import load_system_prompt


class ReactAgent(object):
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompt(),
            tools=[rag_summarize, get_weather, get_user_location, get_user_id, get_current_month,
                   fetch_external_data, fill_context_for_report],
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
        )

    def execute_stream(self, query: str, history: list = None):
        messages = []
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": query})

        input_dict = {"messages": messages}

        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]

            # 只输出最终答案：AIMessage 且没有工具调用，并且内容非空
            if latest_message.type == "ai" and not latest_message.tool_calls and latest_message.content:
                yield latest_message.content.strip() + "\n"

if __name__ == '__main__':
    agent = ReactAgent()
    # 测试：无历史
    for chunk in agent.execute_stream("给我生成我的使用报告"):
        print(chunk, end="", flush=True)