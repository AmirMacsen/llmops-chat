from uuid import UUID

from injector import inject
from dataclasses import dataclass

from internal.schema.document_schema import CreateDocumentsRequest, CreateDocumentsResponse
from internal.service import DocumentService
from pkg.response import validate_error_json, success_json


@inject
@dataclass
class DocumentHandler:
    """文档处理服务"""
    document_service: DocumentService

    def create_documents(self, dataset_id:UUID):
        """创建文档 列表"""
        # 校验请求
        request = CreateDocumentsRequest()

        if not request.validate():
            return validate_error_json(request.errors)

        # 调用服务并创建文档，返回文档信息列表+批次
        documents,batch = self.document_service.create_document(
            dataset_id=dataset_id,
            **request.data
        )

        response = CreateDocumentsResponse()
        return success_json(response.dump((documents, batch)))


