import os
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from model.factory import embed_model
from langchain_chroma import Chroma
from utils.config_handler import chroma_conf
from utils.file_handler import get_file_md5_hex, listdir_with_allowed_type, csv_loader, pdf_loader, txt_loader
from utils.logger_handler import logger
from utils.path_tool import get_abs_path

# ========== MD5 辅助函数（模块级） ==========
def _check_md5_hex(md5_for_check: str, filepath: str) -> bool:
    """
    检查 MD5 和文件路径是否已存在（MD5 文件格式：MD5|文件路径）
    """
    md5_file = get_abs_path(chroma_conf["md5_hex_store"])
    if not os.path.exists(md5_file):
        return False
    with open(md5_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == f"{md5_for_check}|{filepath}":
                return True
    return False

def _save_md5_hex(md5_for_save: str, filepath: str):
    """保存 MD5 和文件路径到记录文件"""
    md5_file = get_abs_path(chroma_conf["md5_hex_store"])
    with open(md5_file, "a", encoding="utf-8") as f:
        f.write(f"{md5_for_save}|{filepath}\n")

def _remove_md5_by_filepath(filepath: str):
    """根据文件路径删除对应的 MD5 记录行"""
    md5_file = get_abs_path(chroma_conf["md5_hex_store"])
    if not os.path.exists(md5_file):
        return
    with open(md5_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open(md5_file, "w", encoding="utf-8") as f:
        for line in lines:
            if not line.endswith(f"|{filepath}\n"):
                f.write(line)

# ========== 文件加载辅助函数（复用原有） ==========
def get_file_documents(read_path: str) -> list[Document]:
    if read_path.endswith("txt"):
        return txt_loader(read_path)
    elif read_path.endswith("pdf"):
        return pdf_loader(read_path)
    elif read_path.endswith("csv"):
        return csv_loader(read_path)
    else:
        return []

# ========== VectorStoreService 类 ==========
class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name=chroma_conf["collection_name"],
            embedding_function=embed_model,
            persist_directory=get_abs_path(chroma_conf["persist_directory"]),
        )
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            separators=chroma_conf["separators"],
            length_function=len,
        )

    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_conf["k"]})

    # ---------- 删除文档（根据文件路径） ----------
    def delete_documents_by_filepath(self, filepath: str):
        """
        根据文件路径删除向量库中属于该文件的所有文档
        """
        # 获取集合中所有文档的元数据（如果数据量太大，建议分页，这里简化）
        all_docs = self.vector_store.get(include=["metadatas"])
        ids_to_delete = []
        for doc_id, metadata in zip(all_docs["ids"], all_docs["metadatas"]):
            if metadata and metadata.get("source") == filepath:
                ids_to_delete.append(doc_id)
        if ids_to_delete:
            self.vector_store.delete(ids_to_delete)
            logger.info(f"[向量库] 已删除文件 {filepath} 对应的 {len(ids_to_delete)} 个文档")
        else:
            logger.info(f"[向量库] 文件 {filepath} 在向量库中无对应文档，无需删除")

    # ---------- 单个文件添加到向量库（新增/更新） ----------
    def add_file_to_vector_store(self, filepath: str):
        """
        处理单个文件的添加/更新
        """
        # 1. 计算文件 MD5
        md5_hex = get_file_md5_hex(filepath)
        if not md5_hex:
            logger.warning(f"[向量库] 计算 MD5 失败，跳过：{filepath}")
            return

        # 2. 检查是否已存在且未变化
        if _check_md5_hex(md5_hex, filepath):
            logger.info(f"[向量库] 文件 {filepath} 未变化（MD5 匹配），跳过")
            return

        # 3. 先删除该文件原有的所有文档（如果存在）
        self.delete_documents_by_filepath(filepath)

        # 4. 加载文档
        try:
            documents = get_file_documents(filepath)
            if not documents:
                logger.warning(f"[向量库] 文件 {filepath} 无有效内容，跳过")
                return
            split_docs = self.spliter.split_documents(documents)
            if not split_docs:
                logger.warning(f"[向量库] 文件 {filepath} 分片后无内容，跳过")
                return

            # 5. 为每个文档添加 source 元数据（用于后续删除）
            for doc in split_docs:
                if doc.metadata is None:
                    doc.metadata = {}
                doc.metadata["source"] = filepath

            # 6. 添加到向量库
            self.vector_store.add_documents(split_docs)

            # 7. 保存新的 MD5 记录（先删除旧的，再保存新的）
            #    由于我们已经在第3步删除了旧文档，但 MD5 记录可能残留，这里先尝试删除旧的 MD5 记录
            _remove_md5_by_filepath(filepath)
            _save_md5_hex(md5_hex, filepath)

            logger.info(f"[向量库] 文件 {filepath} 加载成功")
        except Exception as e:
            logger.error(f"[向量库] 文件 {filepath} 加载失败：{e}", exc_info=True)

    # ---------- 单个文件从向量库删除 ----------
    def remove_file_from_vector_store(self, filepath: str):
        """
        处理文件被删除：删除向量库中对应的文档，并移除 MD5 记录
        """
        # 1. 删除向量库中的文档
        self.delete_documents_by_filepath(filepath)
        # 2. 移除 MD5 记录
        _remove_md5_by_filepath(filepath)
        logger.info(f"[向量库] 文件 {filepath} 已从向量库移除")

    # ---------- 全量加载（原有功能，现在复用 add_file） ----------
    def load_document(self):
        """
        扫描 data 目录，将所有允许类型的文件加载到向量库
        """
        allowed_files_path = listdir_with_allowed_type(
            get_abs_path(chroma_conf["data_path"]),
            tuple(chroma_conf["allow_knowledge_file_type"])
        )
        for path in allowed_files_path:
            self.add_file_to_vector_store(path)