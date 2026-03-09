# utils/cache_utils.py
import diskcache as dc
from utils.path_tool import get_abs_path
import hashlib
import logging
from utils.config_handler import chroma_conf  # 假设配置放在 chroma_conf 中

logger = logging.getLogger(__name__)


class RAGCache:
    """RAG 检索结果缓存，基于 diskcache，支持过期时间"""

    def __init__(self, cache_dir="cache/rag", expire=3600):
        """
        :param cache_dir: 缓存目录，相对于项目根目录
        :param expire: 默认过期时间，单位秒，默认1小时
        """
        self.cache_dir = get_abs_path(cache_dir)
        self.cache = dc.Cache(self.cache_dir)
        self.default_expire = expire
        logger.info(f"RAG缓存初始化，目录：{self.cache_dir}，默认过期时间：{expire}秒")
        cache_dir = chroma_conf.get("cache", {}).get("rag_cache_dir", "cache/rag")
        expire = chroma_conf.get("cache", {}).get("rag_cache_expire", 3600)

    def _make_key(self, query: str) -> str:
        """生成缓存键，使用 query 的 MD5 哈希，避免特殊字符问题"""
        return hashlib.md5(query.encode('utf-8')).hexdigest()

    def get(self, query: str):
        """根据 query 获取缓存结果，若不存在或已过期返回 None"""
        key = self._make_key(query)
        value = self.cache.get(key, default=None, retry=True)
        if value is not None:
            logger.debug(f"缓存命中，query：{query[:50]}...")
        else:
            logger.debug(f"缓存未命中，query：{query[:50]}...")
        return value

    def set(self, query: str, result: str, expire=None):
        """存入缓存，expire 覆盖默认过期时间"""
        key = self._make_key(query)
        expire = expire if expire is not None else self.default_expire
        self.cache.set(key, result, expire=expire, retry=True)
        logger.debug(f"缓存已设置，query：{query[:50]}...，过期时间：{expire}秒")

    def clear(self):
        """清空所有缓存（谨慎使用）"""
        self.cache.clear()
        logger.warning("RAG缓存已清空")

    def close(self):
        """关闭缓存（程序退出时调用）"""
        self.cache.close()


# 为了方便，创建一个全局单例
_rag_cache = None


def get_rag_cache():
    global _rag_cache
    if _rag_cache is None:
        _rag_cache = RAGCache()
    return _rag_cache