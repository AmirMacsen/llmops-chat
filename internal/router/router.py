from  dataclasses import dataclass

from flask import Flask, Blueprint

from internal.handler import AppHandler, BuiltinToolHandler, ApiToolHandler, UploadFileHandler, DatasetHandler, \
    DocumentHandler, SegmentHandler, OAuthHandler, AccountHandler, AuthHandler
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
    segment_handler: SegmentHandler
    oauth_handler: OAuthHandler
    account_handler: AccountHandler
    auth_handler: AuthHandler

    def register_router(self, app:Flask):
        """注册路由"""

        # 1. 创建蓝图
        bp = Blueprint('llmops', __name__, url_prefix='')

        # 2. 把url与对应的控制器方法绑定
        bp.add_url_rule("/ping", view_func=self.app_handler.ping)
        bp.add_url_rule("/apps", methods=["POST"], view_func=self.app_handler.create_app)
        bp.add_url_rule("/apps/<uuid:app_id>", view_func=self.app_handler.get_app)
        bp.add_url_rule("/apps/<uuid:app_id>/draft-app-config", view_func=self.app_handler.get_draft_app_config)
        bp.add_url_rule(
            "/apps/<uuid:app_id>/draft-app-config",
            methods=["POST"],
            view_func=self.app_handler.update_draft_app_config,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/publish",
            methods=["POST"],
            view_func=self.app_handler.publish,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/cancel-publish",
            methods=["POST"],
            view_func=self.app_handler.cancel_publish,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/publish-histories",
            view_func=self.app_handler.get_publish_histories_with_page,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/fallback-history",
            methods=["POST"],
            view_func=self.app_handler.fallback_history_to_draft,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/summary",
            view_func=self.app_handler.get_debug_conversation_summary,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/summary",
            methods=["POST"],
            view_func=self.app_handler.update_debug_conversation_summary,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/conversations/delete-debug-conversation",
            methods=["POST"],
            view_func=self.app_handler.delete_debug_conversation,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/conversations",
            methods=["POST"],
            view_func=self.app_handler.debug_chat,
        )

        # 3.内置插件广场模块
        bp.add_url_rule("/builtin-tools",
                        view_func=self.builtin_tool_handler.get_builtin_tools,
                        methods=['GET'])
        bp.add_url_rule("/builtin-tools/<string:provider_name>/<string:tool_name>",
                        view_func=self.builtin_tool_handler.get_provider_tool,
                        methods=['GET'])

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
        bp.add_url_rule("/upload-files/file",
                        methods=["POST"],
                        view_func=self.upload_file_handler.upload_file)
        bp.add_url_rule("/upload-files/image",
                        methods=["POST"],
                        view_func=self.upload_file_handler.upload_image)


        # 5. 知识库
        bp.add_url_rule("/datasets",
                        methods=["GET"],
                        view_func=self.dataset_handler.get_datasets_with_page)
        bp.add_url_rule("/datasets",
                        methods=["POST"],
                        view_func=self.dataset_handler.create_dataset)
        bp.add_url_rule("/datasets/<uuid:dataset_id>",
                        methods=["GET"],
                        view_func=self.dataset_handler.get_dataset)
        bp.add_url_rule("/datasets/<uuid:dataset_id>",
                        methods=["POST"],
                        view_func=self.dataset_handler.update_dataset)

        bp.add_url_rule("/datasets/embeddings",
                        methods=["GET"],
                        view_func=self.dataset_handler.embedding_query)

        bp.add_url_rule("/datasets/<uuid:dataset_id>/queries",
                        methods=["GET"],
                        view_func=self.dataset_handler.get_dataset_quires)

        bp.add_url_rule("/datasets/<uuid:dataset_id>/delete",
                        methods=["POST"],
                        view_func=self.dataset_handler.delete_dataset,)

        # 文档
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents",
                        methods=["POST"],
                        view_func=self.document_handler.create_documents)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/batch/<string:batch>",
                        methods=["GET"],
                        view_func=self.document_handler.get_documents_status)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents",
                        methods=["GET"],
                        view_func=self.document_handler.get_document_with_page)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>",
                        methods=["GET"],
                        view_func=self.document_handler.get_document)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/name",
                        methods=["POST"],
                        view_func=self.document_handler.update_document_name)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/enabled",
                        methods=["POST"],
                        view_func=self.document_handler.update_document_enabled)

        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/delete",
                        methods=["POST"],
                        view_func=self.document_handler.delete_document)


        # 片段
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments",
                        methods=["GET"],
                        view_func=self.segment_handler.get_segment_with_page)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>",
                        methods=["GET"],
                        view_func=self.segment_handler.get_segment)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>/enabled",
                        methods=["POST"],
                        view_func=self.segment_handler.update_segment_enabled)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments",
                        methods=["POST"],
                        view_func=self.segment_handler.create_segment)
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>",
            methods=["POST"],
            view_func=self.segment_handler.update_segment,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>/delete",
            methods=["POST"],
            view_func=self.segment_handler.delete_segment,
        )

        # 召回
        bp.add_url_rule("/datasets/<uuid:dataset_id>/hit",
                        methods=["POST"],
                        view_func=self.dataset_handler.hit)

        # 授权登录
        bp.add_url_rule("/oauth/<string:provider_name>",
                        methods=["GET"],
                        view_func=self.oauth_handler.provider)

        bp.add_url_rule(
            "/oauth/authorize/<string:provider_name>",
            methods=["POST"],
            view_func=self.oauth_handler.authorize,
        )
        bp.add_url_rule(
            "/auth/password-login",
            methods=["POST"],
            view_func=self.auth_handler.password_login,
        )
        bp.add_url_rule(
            "/auth/logout",
            methods=["POST"],
            view_func=self.auth_handler.logout,
        )

        bp.add_url_rule("/account", view_func=self.account_handler.get_current_user)
        bp.add_url_rule("/account/password", methods=["POST"], view_func=self.account_handler.update_password)
        bp.add_url_rule("/account/name", methods=["POST"], view_func=self.account_handler.update_name)
        bp.add_url_rule("/account/avatar", methods=["POST"], view_func=self.account_handler.update_avatar)

        # 3. 注册蓝图
        app.register_blueprint(bp)