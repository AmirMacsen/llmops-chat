from uuid import UUID

from injector import inject
from dataclasses import dataclass
from flask import request

from internal.schema.document_schema import CreateDocumentsRequest, CreateDocumentsResponse, GetDocumentResponse, \
    UpdateDocumentNameRequest, GetDocumentsWithPageRequest, GetDocumentsWithPageResponse, UpdateDocumentEnabledRequest
from internal.service import DocumentService
from pkg.paginator import PageModel
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


    def get_documents_status(self, dataset_id:UUID, batch:str):
        """根据传递的知识库id和批处理标识获取文档的状态"""
        documents_status = self.document_service.get_documents_status(dataset_id, batch)

        return success_json(documents_status)


    def get_document(self, dataset_id:UUID, document_id:UUID):
        """根据传递的知识库ID和文档iD获取文档"""
        document = self.document_service.get_document(dataset_id, document_id)
        response = GetDocumentResponse()
        return success_json(response.dump(document))


    def update_document_name(self, dataset_id:UUID, document_id:UUID):
        """更新文档"""
        request = UpdateDocumentNameRequest()
        if not request.validate():
            return validate_error_json(request.errors)
        self.document_service.update_document(dataset_id, document_id,
                                                   name=request.name.data)
        return success_json(data="更新数据成功")


    def get_document_with_page(self, dataset_id:UUID):
        """根据传递的知识库ID获取文档分页"""

        req = GetDocumentsWithPageRequest(request.args)
        if not req.validate():
            return validate_error_json(req.errors)
        documents, paginator = self.document_service.get_documents_with_page(dataset_id, req)
        response = GetDocumentsWithPageResponse(many=True)
        return success_json(PageModel(list=response.dump(documents), paginator=paginator))


    def update_document_enabled(self, dataset_id:UUID, document_id:UUID):
        """根据传递的documentid和datasetid启用文档"""
        req = UpdateDocumentEnabledRequest(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务更改指定文档的状态
        self.document_service.update_document_enabled(dataset_id, document_id, req.enabled.data)
        return success_json(data="更改文档启用状态成功")


    def delete_document(self, dataset_id:UUID, document_id:UUID):
        """根据传递的documentid和datasetid删除文档"""
        self.document_service.delete_document(dataset_id, document_id)
        return success_json(data="删除文档成功")








