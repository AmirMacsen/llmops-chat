from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed, FileSize
from marshmallow import Schema, fields, pre_dump

from internal.entity.upload_file_entity import ALLOW_FILE_EXTENSIONS, ALLOW_IMAGE_EXTENSIONS
from internal.model import UploadFile


class UploadFileRequest(FlaskForm):
    """上传文件请求"""
    file = FileField("file", validators=[
        FileRequired(message="请选择文件"),
        FileSize(max_size=1024 * 1024 * 15, message="文件大小不能超过15M"),
        FileAllowed(ALLOW_FILE_EXTENSIONS, message=f"仅允许上传{'/'.join(ALLOW_FILE_EXTENSIONS)}")
    ])


class UploadFileResponse(Schema):
    """上传文件响应"""
    id = fields.UUID(dump_default='')
    account_id = fields.UUID(dump_default='')
    name = fields.String(dump_default='')
    key = fields.String(dump_default='')
    size = fields.Integer(dump_default=0)
    extension = fields.String(dump_default='')
    mime_type = fields.String(dump_default='')
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def pre_dump(self, data:UploadFile, **kwargs):
        """
        预处理数据
        :param data:
        :param kwargs:
        :return:
        """
        return {
            "id": str(data.id),
            "account_id": str(data.account_id),
            "name": data.name,
            "key": data.key,
            "size": data.size,
            "extension": data.extension,
            "mime_type": data.mime_type,
            "created_at": int(data.created_at.timestamp())
        }


class UploadImageRequest(FlaskForm):
    """上传图片请求"""
    file = FileField("file", validators=[
        FileRequired(message="请选择图片"),
        FileSize(max_size=1024 * 1024 * 15, message="请选择图片不能超过15M"),
        FileAllowed(ALLOW_IMAGE_EXTENSIONS, message=f"仅允许上传{'/'.join(ALLOW_IMAGE_EXTENSIONS)}")
    ])
