import time
import uuid
import streamlit as st
from agent.react_agent import ReactAgent
import atexit
from utils.cache_utils import get_rag_cache
from rag.vector_store import VectorStoreService
from utils.knowledge_watcher import start_watching
from utils.db_handler import init_db, save_message, get_recent_messages

# ========== 页面配置（必须在最前面） ==========
st.set_page_config(
    page_title="清平乐智能客服",
    page_icon="❄️",
    layout="wide"
)

# 初始化数据库
init_db()

# ========== 会话管理：使用 query_params 持久化 session_id ==========
query_params = st.query_params
if "session_id" in query_params:
    raw = query_params["session_id"]
    session_id = raw[0] if isinstance(raw, list) else raw
else:
    session_id = str(uuid.uuid4())
    st.query_params["session_id"] = session_id
st.session_state["session_id"] = session_id

# ========== 侧边栏 ==========
with st.sidebar:
    st.header("❄️ 清平乐智能空调助手")
    st.divider()

    # 新会话按钮
    if st.button("🆕 新会话", use_container_width=True):
        new_session_id = str(uuid.uuid4())
        st.query_params["session_id"] = new_session_id
        st.rerun()

    st.divider()
    st.caption(f"当前会话ID: {session_id[:8]}...")
    st.caption("© 2026 清平乐")

st.title("清平乐智能客服")
st.divider()

# ========== 知识库监控（第3步） ==========
if 'observer' not in st.session_state:
    vector_service = VectorStoreService()
    vector_service.load_document()
    observer = start_watching(vector_service)
    st.session_state['observer'] = observer
    st.session_state['vector_service'] = vector_service

# ========== 初始化消息列表（第4步） ==========
if "message" not in st.session_state:
    recent = get_recent_messages(st.session_state["session_id"], limit=20)
    if recent:
        st.session_state["message"] = recent
    else:
        welcome_msg = {"role": "assistant", "content": "你好，我是清平乐智能客服，请问有什么可以帮助你？"}
        st.session_state["message"] = [welcome_msg]
        save_message(st.session_state["session_id"], welcome_msg["role"], welcome_msg["content"])

if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()

# 显示历史消息
for message in st.session_state["message"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ========== 用户输入 ==========
prompt = st.chat_input("请输入您的问题...")

if prompt:
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)

    # 保存用户消息
    save_message(st.session_state["session_id"], "user", prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    # 准备历史（最近20条）
    history = st.session_state["message"][-20:]

    # 调用 Agent 生成回复（流式）
    with st.spinner("智能客服思考中..."):
        res_stream = st.session_state["agent"].execute_stream(prompt, history=history)

        # 显示助手回复（流式）
        with st.chat_message("assistant"):
            full_response = st.write_stream(res_stream)

        # 保存助手回复
        if full_response:
            save_message(st.session_state["session_id"], "assistant", full_response)
            st.session_state["message"].append({"role": "assistant", "content": full_response})

        # 刷新页面（Streamlit 自动处理，但为了立即显示新消息，可以保留 rerun）
        st.rerun()


# ========== 关闭缓存（第2步） ==========
def close_cache():
    get_rag_cache().close()


atexit.register(close_cache)