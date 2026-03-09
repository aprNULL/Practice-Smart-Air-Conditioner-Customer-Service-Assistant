import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from utils.path_tool import get_abs_path

# 数据库文件路径（放在项目根目录）
DB_PATH = get_abs_path("chat_history.db")

def init_db():
    """初始化数据库，创建表（如果不存在）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT
        )
    ''')
    # 创建索引加速查询
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_time ON conversations (session_id, timestamp)')
    conn.commit()
    conn.close()

def save_message(session_id: str, role: str, content: str, user_id: Optional[str] = None):
    """
    保存单条消息到数据库
    :param session_id: 会话ID
    :param role: 'user' 或 'assistant'
    :param content: 消息内容
    :param user_id: 可选，关联的用户ID
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (session_id, role, content, user_id) VALUES (?, ?, ?, ?)",
        (session_id, role, content, user_id)
    )
    conn.commit()
    conn.close()

def get_recent_messages(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    获取某个会话最近的若干条消息（按时间升序）
    :param session_id: 会话ID
    :param limit: 返回的最大条数
    :return: 消息列表，每条包含 role 和 content
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM conversations WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
        (session_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    # 按时间升序返回（从旧到新）
    messages = [{"role": row[0], "content": row[1]} for row in reversed(rows)]
    return messages

def clear_history(session_id: str):
    """清空指定会话的历史记录（可选功能）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()