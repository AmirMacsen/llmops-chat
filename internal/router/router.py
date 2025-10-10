from  dataclasses import dataclass

from flask import Flask, Blueprint

from internal.handler import AppHandler, BuiltinToolHandler, ApiToolHandler, UploadFileHandler, DatasetHandler, DocumentHandler
from injector import inject


@inject
@dataclass
class Router:
    app_handler: AppHandler
    builtin_tool_handler: BuiltinToolHandler
    api_tool_handler: ApiToolHandler
    upload_file_handler: UploadFileHandler
    dataset_handler: DatasetHandler
    document_handler: DocumentHandler

    def register_router(self, app:Flask):
        """注册路由"""

        # 1. 创建蓝图
        bp = Blueprint('llmops', __name__, url_prefix='')

        # 2. 把url与对应的控制器方法绑定
        bp.add_url_rule("/apps/<uuid:app_id>/debug", methods=["POST"], view_func=self.app_handler.debug)
        bp.add_url_rule('/create_app', view_func=self.app_handler.create_app, methods=['POST'])
        bp.add_url_rule('/get_app/<uuid:app_id>', view_func=self.app_handler.get_app, methods=['GET'])
        bp.add_url_rule('/update_app/<uuid:app_id>', view_func=self.app_handler.update_app, methods=['POST'])
        bp.add_url_rule('/delete_app/<uuid:app_id>', view_func=self.app_handler.delete_app, methods=['POST'])
        bp.add_url_rule('/ping', view_func=self.app_handler.ping)
        bp.add_url_rule('/completion', view_func=self.app_handler.completion, methods=['POST'])

        # 3.内置插件广场模块
        bp.add_url_rule("/builtin-tools", view_func=self.builtin_tool_handler.get_builtin_tools, methods=['GET'])
        bp.add_url_rule("/builtin-tools/<string:provider_name>/<string:tool_name>",
                        view_func=self.builtin_tool_handler.get_provider_tool, methods=['GET'])

        bp.add_url_rule('/builtin-tools/<string:provider_name>/icon',
                        view_func=self.builtin_tool_handler.get_provider_icon,
                        methods=["GET"])
        bp.add_url_rule('/builtin-tools/categories',
                        view_func=self.builtin_tool_handler.get_categories,
                        methods=['GET'])

        # 4. 自定义API插件模块
        bp.add_url_rule("/api-tools",
                        methods=["GET"],
                        view_func=self.api_tool_handler.get_api_tool_providers_with_page)

        bp.add_url_rule("/api-tools/<uuid:provider_id>/update",
                        methods=["POST"],
                        view_func=self.api_tool_handler.update_api_tool_provider)

        bp.add_url_rule("/api-tools/validate-openapi-schema",
                        methods=["POST"],
                        view_func=self.api_tool_handler.validate_open_ai_schema)

        bp.add_url_rule("/api-tools",
                        methods=["POST"],
                        view_func=self.api_tool_handler.create_open_api_tool_provider)

        bp.add_url_rule("/api-tools/<uuid:provider_id>",
                        methods=["GET"],
                        view_func=self.api_tool_handler.get_api_tool_provider)

        bp.add_url_rule("/api-tools/<uuid:provider_id>/<string:tool_name>",
                        methods=["GET"],
                        view_func=self.api_tool_handler.get_api_tool)

        bp.add_url_rule("/api-tools/<uuid:provider_id>/delete",
                        methods=["POST"],
                        view_func=self.api_tool_handler.delete_api_tool_provider)

       # 4. 文件上传
        bp.add_url_rule("/upload-files/file", methods=["POST"],
                        view_func=self.upload_file_handler.upload_file)
        bp.add_url_rule("/upload-files/image", methods=["POST"],
                        view_func=self.upload_file_handler.upload_image)


        # 5. 知识库
        bp.add_url_rule("/datasets", methods=["GET"],
                        view_func=self.dataset_handler.get_datasets_with_page)
        bp.add_url_rule("/datasets", methods=["POST"],
                        view_func=self.dataset_handler.create_dataset)
        bp.add_url_rule("/datasets/<uuid:dataset_id>", methods=["GET"],
                        view_func=self.dataset_handler.get_dataset)
        bp.add_url_rule("/datasets/<uuid:dataset_id>", methods=["POST"],
                        view_func=self.dataset_handler.update_dataset)

        bp.add_url_rule("/datasets/embeddings", methods=["GET"],
                        view_func=self.dataset_handler.embedding_query)

        # 文档
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents", methods=["POST"],
                        view_func=self.document_handler.create_documents)
        # 3. 注册蓝图
        app.register_blueprint(bp)