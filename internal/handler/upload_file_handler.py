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
        """
        上传文件接口
        ---
        tags:
          - Upload
        summary: 上传文件
        description: 上传文件到系统中，支持多种文件格式
        requestBody:
          content:
            multipart/form-data:
              schema:
                type: object
                properties:
                  file:
                    type: string
                    format: binary
                    description: 要上传的文件
                required:
                  - file
        responses:
          200:
            description: 文件上传成功
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "success"
                    data:
                      type: object
                      properties:
                        id:
                          type: string
                          format: uuid
                          example: "b03d55b5-895e-47c8-b767-6d0015ae60a1"
                        account_id:
                          type: string
                          format: uuid
                          example: "b03d55b5-895e-47c8-b767-6d0015ae60a1"
                        name:
                          type: string
                          example: "example.pdf"
                        key:
                          type: string
                          example: "2025/04/15/123e4567-e89b-12d3-a456-426614174000.pdf"
                        size:
                          type: integer
                          example: 1024
                        extension:
                          type: string
                          example: "pdf"
                        mime_type:
                          type: string
                          example: "application/pdf"
                        created_at:
                          type: integer
                          example: 1713110400
          400:
            description: 请求参数错误
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "validate_error"
                    message:
                      type: string
                      example: "请选择文件"
                    data:
                      type: object
        """
        request = UploadFileRequest ()
        if not request.validate():
            return validate_error_json(request.errors)

        # 构建请求并校验
        file = self.cos_service.upload_file(request.file.data)
        # 调用服务上传文件
        response = UploadFileResponse()

        return success_json(data=response.dump(file))


    def upload_image(self):
        """
        上传图片接口
        ---
        tags:
          - Upload
        summary: 上传图片
        description: 上传图片到系统中，支持常见图片格式
        requestBody:
          content:
            multipart/form-data:
              schema:
                type: object
                properties:
                  file:
                    type: string
                    format: binary
                    description: 要上传的图片文件
                required:
                  - file
        responses:
          200:
            description: 图片上传成功
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "success"
                    data:
                      type: object
                      properties:
                        image_url:
                          type: string
                          example: "https://example.cos.ap-beijing.myqcloud.com/2025/04/15/123e4567-e89b-12d3-a456-426614174000.jpg"
          400:
            description: 请求参数错误
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    code:
                      type: string
                      example: "validate_error"
                    message:
                      type: string
                      example: "请选择图片"
                    data:
                      type: object
        """
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