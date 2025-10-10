import os.path
import tempfile
from dataclasses import dataclass
from pathlib import Path

import requests
from injector import inject
from langchain_community.document_loaders import (
    UnstructuredFileLoader,
    TextLoader,
    UnstructuredPowerPointLoader,
    UnstructuredMarkdownLoader,
    UnstructuredCSVLoader,
    UnstructuredExcelLoader,
    UnstructuredHTMLLoader,
    UnstructuredPDFLoader,
    UnstructuredXMLLoader
)
from langchain_core.documents import Document

from internal.model import UploadFile
from internal.service import CosService

@inject
@dataclass
class FileExtractor:
    """文件提取器，把远程文件记录加载成Langchain对应的文档或者字符串"""
    cos_service: CosService

    def load(self,
             upload_file:UploadFile,
             return_text:bool=False,
             is_unstructured:bool=False) -> list[Document] | str:
        """加载文件"""
        # 1.创建一个临时文件夹
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 构建一个临时文件路径
            file_path = os.path.join(tmp_dir, os.path.basename(upload_file.key))
            # 从cos中下载文件
            self.cos_service.download_file(upload_file.key, file_path)

            # 加载文件
            return self.load_from_file(file_path, return_text, is_unstructured)

    @classmethod
    def load_from_file(cls,
                       file_path:str,
                       return_text:bool=False,
                       is_unstructured:bool=False) -> list[Document] | str:
        """从文件加载"""
        # 获取文件的扩展名
        delimiter = "\n\n"
        file_extension = Path(file_path).suffix.lower()

        # 根据不同的文件扩展名选择不同的文件加载器
        if file_extension in [".xlsx", ".xls"]:
            loader = UnstructuredExcelLoader(file_path)
        elif file_extension in [".pdf"]:
            loader = UnstructuredPDFLoader(file_path)
        elif file_extension in [".txt"]:
            loader = TextLoader(file_path)
        elif file_extension in [".csv"]:
            loader = UnstructuredCSVLoader(file_path)
        elif file_extension in [".md", ".markdown"]:
            loader = UnstructuredMarkdownLoader(file_path, )
        elif file_extension in [".html"]:
            loader = UnstructuredHTMLLoader(file_path)
        elif file_extension in [".ppt", ".pptx"]:
            loader = UnstructuredPowerPointLoader(file_path)
        elif file_extension in [".doc", ".docx"]:
            loader = UnstructuredFileLoader(file_path)
        elif file_extension in [".xml"]:
            loader = UnstructuredXMLLoader(file_path)
        else:
            loader = UnstructuredFileLoader(file_path) if not is_unstructured else TextLoader(file_path)

        # 返回加载的文档列表或者文本
        return delimiter.join([document.page_content for document in loader.load()]) if return_text else loader.load()


    @classmethod
    def load_from_url(cls,url:str,return_text:bool=False,) -> list[Document] | str:
        """从URL加载"""
        # 下载远程文本到本地
        response = requests.get(url)
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 构建临时存储路径
            file_path = os.path.join(tmp_dir, os.path.basename(url))
            with open(file_path, "wb") as f:
                f.write(response.content)

        return cls.load_from_file(file_path, return_text, True)