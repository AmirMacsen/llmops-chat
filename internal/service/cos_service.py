import hashlib
import os
import uuid
from datetime import datetime

from injector import inject
from dataclasses import dataclass

from qcloud_cos import CosS3Client, CosConfig
from werkzeug.datastructures import FileStorage

from internal.entity.upload_file_entity import ALLOW_FILE_EXTENSIONS, ALLOW_IMAGE_EXTENSIONS
from internal.exception import FailedException
from internal.model import UploadFile
from internal.service import UploadFileService


@inject
@dataclass
class CosService:
    """腾讯云COS服务"""
    upload_file_service: UploadFileService

    @classmethod
    def _get_client(cls) -> CosS3Client:
        conf = CosConfig(
            Region=os.getenv("COS_REGION"),
            SecretId=os.getenv("COS_SECRET_ID"),
            SecretKey=os.getenv("COS_SECRET_KEY"),
            Token=None,
            Scheme=os.getenv("COS_SCHEME", "https")
        )

        return CosS3Client(conf)

    @classmethod
    def _get_bucket(cls)->str:
        return os.getenv("COS_BUCKET")


    def get_file_url(self, key:str)->str:
        """获取文件访问地址"""

        domain = os.getenv("COS_DOMAIN")
        if not domain:
            bucket = self._get_bucket()
            scheme = os.getenv("COS_SCHEME")
            region = os.getenv("COS_REGION")
            return f"{scheme}://{bucket}.cos.{region}.myqcloud.com/{key}"
        else:
            return f"{domain}/{key}"


    def download_file(self, key:str, target_file_path:str):
        """下载cos的文件到本地路径"""
        client = self._get_client()
        bucket = self._get_bucket()
        client.download_file(bucket, key, target_file_path)



    def upload_file(self, file:FileStorage, only_image:bool=False)->UploadFile:
        """上传文件到cos"""
        account_id="b03d55b5-895e-47c8-b767-6d0015ae60a1"

        filename = file.filename
        extension = filename.split(".", 1)[-1]  if '.' in filename else ""
        if extension.lower() not in (ALLOW_FILE_EXTENSIONS+ALLOW_IMAGE_EXTENSIONS):
            raise FailedException("文件格式错误")
        elif only_image and extension not in ALLOW_IMAGE_EXTENSIONS:
            raise FailedException("图片格式错误")

        client = self._get_client()
        bucket = self._get_bucket()

        # 生成一个随机名字
        random_filename = str(uuid.uuid4()) + "." + extension
        now = datetime.now()
        upload_filename = f"{now.year}/{now.month:02d}/{now.day:02d}/{random_filename}"
        # 流式读取上传的数据并上传到cos
        file_content = file.stream.read()

        # 将数据上传到cos存储桶中
        try:
            client.put_object(bucket, file_content, upload_filename)
        except Exception as e:
            raise FailedException("上传文件失败")

        # 记录数据
        return self.upload_file_service.create_upload_file(
            account_id=account_id,
            name=filename,
            key=upload_filename,
            size=len(file_content),
            extension=extension,
            mime_type=file.content_type,
            hash=hashlib.sha3_256(file_content).hexdigest()
        )


