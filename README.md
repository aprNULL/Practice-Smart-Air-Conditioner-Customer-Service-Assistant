智能空调客服助手

一个基于 LangChain + RAG 的智能空调领域对话式客服系统。用户可以通过自然语言询问空调故障、保养、选购等问题，系统自动调用工具获取天气、用户信息，并检索知识库生成专业回答。支持生成个性化空调使用报告，并持久化对话历史。

https://img.shields.io/badge/python-3.13-blue.svg
https://img.shields.io/badge/Streamlit-1.28+-red.svg
https://img.shields.io/badge/LangChain-0.2+-green.svg
https://img.shields.io/badge/License-MIT-yellow.svg

✨ 功能特性

智能问答：使用 ReAct Agent 自主决定调用工具或检索知识库，回答空调相关问题。

RAG 知识库：内置故障排除、保养维护、选购指南等 200+ 条专业知识，支持 TXT/PDF/CSV 文档热更新。

工具集成：
天气查询（模拟数据）
用户位置/ID 获取
空调使用报告生成（基于 CSV 数据）

多轮对话记忆：基于 SQLite 持久化存储会话历史，刷新页面后历史不丢失。

动态提示词：根据意图自动切换普通问答提示词和报告生成提示词。

工程化设计：
装饰器工具注册，解耦工具与 Agent
中间件监控工具调用、日志记录
YAML 配置文件管理
分级日志记录（含敏感信息脱敏）
diskcache 缓存 RAG 检索结果
watchdog 监控知识库文件变化，自动更新向量库


🛠️ 技术栈

前端：Streamlit
后端：Python, LangChain, LangGraph
向量库：Chroma
数据库：SQLite
缓存：diskcache
监控：watchdog
配置：PyYAML
日志：Python logging (自定义脱敏)


🚀 快速开始
环境要求
Python 3.13+
通义千问 API 密钥（或替换为其他 LLM）


📁 安装步骤
克隆仓库：
bash
git clone https://github.com/yourname/smart-ac-assistant.git
cd smart-ac-assistant

安装依赖：
bash
pip install -r requirements.txt

配置 API 密钥：
设置环境变量 DASHSCOPE_API_KEY（推荐）：
bash
export DASHSCOPE_API_KEY="你的通义千问API密钥"
或在 config/rag.yml 中直接修改模型名称（默认使用通义千问）。

准备知识库文件：
将您的 TXT/PDF/CSV 文档放入 data/ 目录（已包含示例文件）。

运行应用：
bash
streamlit run app.py
打开浏览器访问 http://localhost:8501。

使用示例：
询问故障：“空调漏水怎么办？”
生成报告：“给我生成我的使用报告”
天气相关：“今天深圳天气适合开空调吗？”


⚙️ 配置说明
config/chroma.yml：向量库路径、分块参数、缓存设置。
config/rag.yml：模型名称。
config/agent.yml：外部数据路径（用于报告生成）。
config/prompts.yml：提示词文件路径。


🔧 自定义扩展
添加新工具:
1.在 agent/tools/ 下新建函数（或直接在现有文件中添加）。
2.使用 @register_tool() 装饰器，并编写函数文档字符串（作为工具描述）。
3.工具会自动注册，无需修改 react_agent.py。

修改提示词:
编辑 prompts/ 目录下的对应文件：
main_prompt.txt：通用问答提示词
report_prompt.txt：报告生成提示词
rag_summarize.txt：RAG 总结提示词

更换 LLM
修改 model/factory.py 中的模型实例化部分，例如替换为 OpenAI.


🙏 致谢
Python
LangChain
Streamlit
Chroma
黑马程序员
