import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.logger_handler import logger
from rag.vector_store import VectorStoreService
from utils.path_tool import get_abs_path
from utils.config_handler import chroma_conf

class KnowledgeBaseHandler(FileSystemEventHandler):
    """自定义文件事件处理器"""

    def __init__(self, vector_service: VectorStoreService):
        super().__init__()
        self.vector_service = vector_service
        # 允许的文件类型，从配置中获取（tuple 形式）
        self.allowed_types = tuple(chroma_conf["allow_knowledge_file_type"])

    def on_created(self, event):
        """文件创建时触发"""
        if not event.is_directory and event.src_path.endswith(self.allowed_types):
            logger.info(f"[监控] 检测到新文件创建：{event.src_path}")
            # 延迟一下，等待文件写入完成
            time.sleep(1)
            self.vector_service.add_file_to_vector_store(event.src_path)

    def on_modified(self, event):
        """文件修改时触发"""
        if not event.is_directory and event.src_path.endswith(self.allowed_types):
            logger.info(f"[监控] 检测到文件修改：{event.src_path}")
            time.sleep(1)
            self.vector_service.add_file_to_vector_store(event.src_path)

    def on_deleted(self, event):
        """文件删除时触发"""
        if not event.is_directory and event.src_path.endswith(self.allowed_types):
            logger.info(f"[监控] 检测到文件删除：{event.src_path}")
            self.vector_service.remove_file_from_vector_store(event.src_path)


def start_watching(vector_service: VectorStoreService, path_to_watch=None):
    """
    启动文件监控
    :param vector_service: VectorStoreService 实例
    :param path_to_watch: 要监控的目录，默认为 data 目录
    :return: Observer 对象，可用于停止监控
    """
    if path_to_watch is None:
        path_to_watch = get_abs_path(chroma_conf["data_path"])

    event_handler = KnowledgeBaseHandler(vector_service)
    observer = Observer()
    observer.schedule(event_handler, path_to_watch, recursive=False)  # 不递归子目录，如需递归设为 True
    observer.start()
    logger.info(f"[监控] 已启动，监控目录：{path_to_watch}")

    return observer

def stop_watching(observer):
    """停止监控"""
    observer.stop()
    observer.join()
    logger.info("[监控] 已停止")