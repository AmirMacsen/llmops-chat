from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, AnyOf, Optional
from uuid import UUID

from internal.entity.dataset_entity import DocumentProcessType, DEFAULT_PROCESS_RULE
from internal.model import Document
from internal.schema import ListField
from internal.schema.schema import DictField
from internal.exception import ValidationException


class CreateDocumentsRequest(FlaskForm):
    """创建文档请求"""
    upload_file_ids = ListField("upload_file_ids", validators=[
        DataRequired("文件id列表不能为空"),
    ])
    process_type = StringField("process_type", validators=[
        DataRequired("文件处理类型不能为空"),
        AnyOf(values=[DocumentProcessType.AUTOMIC, DocumentProcessType.CUSTOM], message="处理类型格式错误"),
    ])
    rule = DictField("process_rule", validators=[
        Optional(),
    ])

    def validate_upload_file_ids(self, field: ListField) -> None:
        """校验上传文件id列表"""
        if not isinstance(field.data, list):
            raise ValidationException("文件id列表格式错误")

        if len(field.data) == 0 or len(field.data) > 10:
            raise ValidationException("文档数量0-10")

        for upload_file_id in field.data:
            try:
                UUID(upload_file_id)
            except:
                raise ValidationException("文件id格式错误")

        field.data = list(dict.fromkeys(field.data))

    def validate_rule(self, field: DictField) -> None:
        """校验处理规则"""
        if self.process_type.data == DocumentProcessType.AUTOMIC:
            field.data = DEFAULT_PROCESS_RULE["rule"]
        else:
            if not isinstance(field.data, dict) or len(field.data) == 0:
                raise ValidationException("处理规则不能为空")

            if "pre_process_rules" not in field.data or not isinstance(field.data['pre_process_rules'], list):
                raise ValidationException("pre_process_rules必须是列表")

            unique_pre_process_rules = {}
            for pre_process_rule in field.data['pre_process_rules']:
                if "id" not in pre_process_rule or pre_process_rule["id"] not in ["remove_extra_space",
                                                                                  "remove_url_and_email"]:
                    raise ValidationException("pre_process_rules格式错误")

                if "enabled" not in pre_process_rule or not isinstance(pre_process_rule["enabled"], bool):
                    raise ValidationException("pre_process_rules格式错误")

                unique_pre_process_rules[pre_process_rule["id"]] = {
                    "id": pre_process_rule["id"],
                    "enabled": pre_process_rule["enabled"]
                }

            if len(unique_pre_process_rules) != 2:
                raise ValidationException("pre_process_rules格式错误")

            field.data["pre_process_rules"] = list(unique_pre_process_rules.values())

            # 校验分段参数
            if "segment" not in field.data or not isinstance(field.data['segment'], dict):
                raise ValidationException("segment格式错误")

            if "separators" not in field.data['segment'] or not isinstance(field.data['segment']['separators'], list):
                raise ValidationException("separators格式错误")
            for separator in field.data['segment']['separators']:
                if not isinstance(separator, str):
                    raise ValidationException("separators格式错误")

            if len(field.data['segment']['separators']) == 0:
                raise ValidationException("separators不能为空")

            if "chunk_size" not in field.data['segment'] or not isinstance(field.data['segment']['chunk_size'], int):
                raise ValidationException("chunk_size格式错误")

            if field.data['segment']['chunk_size'] < 100 or field.data['segment']['chunk_size'] >= 1000:
                raise ValidationException("chunk_size范围100-1000")

            if "overlap" not in field.data['segment'] or not isinstance(field.data['segment']['overlap'], int):
                raise ValidationException("overlap格式错误")

            if not (0 <= field.data['segment']['overlap'] <= field.data['segment']['chunk_size'] * 0.5):
                raise ValidationException("overlap范围0-[chunk_size.length*0.5]")

            field.data = {
                "pre_process_rules": field.data['pre_process_rules'],
                "segment": {
                    "separators": field.data['segment']['separators'],
                    "chunk_size": field.data['segment']['chunk_size'],
                    "overlap": field.data['segment']['overlap']
                }
            }


class CreateDocumentsResponse(Schema):
    """创建文档响应"""
    documents = fields.List(fields.Dict, default=[])
    batch = fields.String(dump_default="")

    @pre_dump
    def process_data(self, data: tuple[list[Document], str], **kwargs):
        return {
            "documents": [{
                "id": document.id,
                "name": document.name,
                "status": document.status,
                "created_at": int(document.created_at.timestamp()),
            } for document in data[0]],
            "batch": data[1]
        }
