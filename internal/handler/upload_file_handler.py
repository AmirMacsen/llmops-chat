from injector import inject
from dataclasses import dataclass

from internal.schema.upload_file_schema import UploadFileRequest, UploadFileResponse, UploadImageRequest
from internal.service import CosService


@inject
@dataclass
class UploadFileHandler:
    """上传文件处理器"""
    cos_service: CosService


    def upload_file(self):
        """上传文件"""
        request = UploadFileRequest ()
        if not request.validate():
            return validate_error_json(request.errors)

        # 构建请求并校验
        file = self.cos_service.upload_file(request.file.data)
        # 调用服务上传文件
        response = UploadFileResponse()

        return success_json(data=response.dump(file))


    def upload_image(self):
        """上传图片"""
        request = UploadImageRequest()
        if not request.validate():
            return validate_error_json(request.errors)
        upload_file = self.cos_service.upload_file(request.file.data, only_image=True)

        # 获取图片的实际URL地址
        url = self.cos_service.get_file_url(upload_file.key)
        return success_json(data={
            "image_url": url
        })


from pkg.response import validate_error_json, success_json