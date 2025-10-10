from celery import shared_task
from uuid import UUID


@shared_task
def build_document(document_ids:list[UUID]) ->None:
    """根据文档传递的文档ID列表构建文档"""
    from app.http.module import injector
    from internal.service import IndexingService

    indexing_service = injector.get(IndexingService)
    indexing_service.build_documents(document_ids)




