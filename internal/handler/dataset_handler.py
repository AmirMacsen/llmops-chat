from dataclasses import dataclass
from uuid import UUID

from flask import request
from injector import inject
from flask_login import login_required

from internal.core.file_extractor import FileExtractor
from internal.schema.dataset_schema import CreateDatasetRequest, UpdateDatasetRequest, GetDatasetsWithPageRequest, \
    GetDatasetResponse, GetDatasetsWithPageResponse, HitRequest, GetDatasetQueriesResponse
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

    @login_required
    def embedding_query(self):
        query = request.args.get("query")
        vectors = self.embeddings_service.embeddings.embed_query(query)
        keywords = self.jieba_service.extract_keywords(query)
        return success_json({"vectors":vectors, "keywords":keywords })


    @login_required
    def hit(self, dataset_id:UUID):
        """文档召回测试"""
        req = HitRequest()
        if not req.validate():
            return validate_error_json(req.errors)
        # 调用服务执行检索策略
        hit_result = self.dataset_service.hit(dataset_id, req)
        return success_json(hit_result)

    @login_required
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

    @login_required
    def get_dataset(self, dataset_id: UUID):
        """根据传递的知识库id获取详情"""
        dataset = self.dataset_service.get_dataset(dataset_id)
        resp = GetDatasetResponse()

        return success_json(resp.dump(dataset))

    @login_required
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

    @login_required
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


    @login_required
    def get_dataset_quires(self, dataset_id: UUID):
        """根据传递的知识库ID获取最近的10条查寻记录"""
        dataset_quires = self.dataset_service.get_dataset_quires(dataset_id)
        response = GetDatasetQueriesResponse(many=True)
        return success_json(response.dump(dataset_quires))


    @login_required
    def delete_dataset(self, dataset_id: UUID):
        """根据传递的知识库id删除知识库"""
        self.dataset_service.delete_dataset(dataset_id)
        return success_message("删除知识库成功")