from uuid import UUID

from dns.e164 import query
from flask import request
from injector import inject
from dataclasses import dataclass

from weaviate.collections.classes.filters import Filter

from internal.core.file_extractor import FileExtractor
from internal.schema.dataset_schema import CreateDatasetRequest, UpdateDatasetRequest, GetDatasetsWithPageRequest, \
    GetDatasetResponse, GetDatasetsWithPageResponse
from internal.service import EmbeddingsService, JiebaService
from internal.service.dataset_service import DatasetService
from internal.service.vector_database_service import VectorDatabaseService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_json, success_message


@inject
@dataclass
class DatasetHandler:
    """数据集处理类"""
    dataset_service: DatasetService
    embeddings_service: EmbeddingsService
    jieba_service: JiebaService
    file_extractor: FileExtractor
    vector_database_service: VectorDatabaseService

    def embedding_query(self):
        query = request.args.get("query")
        vectors = self.embeddings_service.embeddings.embed_query(query)
        keywords = self.jieba_service.extract_keywords(query)
        return success_json({"vectors":vectors, "keywords":keywords })


    def hit(self, dataset_id:UUID):
        """文档召回测试"""
        query="Allows you to animate without code. Don't need to use this if you plan to start the animation in code."
        retriever = self.vector_database_service.vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 10,
                "filters":Filter.all_of([
                    Filter.by_property("document_enabled").equal(True),
                    Filter.by_property("segment_enabled").equal(True),
                    Filter.any_of([
                        Filter.by_property("dataset_id").equal("b86cfc41-ca11-4a7c-8167-b032cbcd100d"),
                        Filter.by_property("dataset_id").equal("b86cfc41-ca11-4a7c-8167-b032cbcd100f"),
                    ])
                ])
            },
        )
        documents = retriever.invoke(query)
        return success_json({"documents":[
            {
                "metadata": document.metadata,
                "page_content":document.page_content,
            } for document in documents
        ]})

    def create_dataset(self):
        """创建知识库"""
        # 1.提取请求并校验
        req = CreateDatasetRequest()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务创建知识库
        self.dataset_service.create_dataset(req)

        # 3.返回成功调用提示
        return success_message("创建知识库成功")

    def get_dataset(self, dataset_id: UUID):
        """根据传递的知识库id获取详情"""
        dataset = self.dataset_service.get_dataset(dataset_id)
        resp = GetDatasetResponse()

        return success_json(resp.dump(dataset))

    def update_dataset(self, dataset_id: UUID):
        """根据传递的知识库id+信息更新知识库"""
        # 1.提取请求并校验
        req = UpdateDatasetRequest()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务创建知识库
        self.dataset_service.update_dataset(dataset_id, req)

        # 3.返回成功调用提示
        return success_message("更新知识库成功")

    def get_datasets_with_page(self):
        """获取知识库分页+搜索列表数据"""
        # 1.提取query数据并校验
        req = GetDatasetsWithPageRequest(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务获取分页数据
        datasets, paginator = self.dataset_service.get_datasets_with_page(req)

        # 3.构建响应
        resp = GetDatasetsWithPageResponse(many=True)

        return success_json(PageModel(list=resp.dump(datasets), paginator=paginator))

