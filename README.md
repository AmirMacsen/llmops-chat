# LlmOps - AI应用开发与管理平台

LlmOps是一个基于Flask框架构建的AI应用开发与管理平台，旨在简化大型语言模型（LLM）应用的创建、部署和管理。该平台提供了完整的工具集，用于构建、调试和发布AI应用。

## 功能特性

- **AI应用管理**：创建、编辑、发布和管理AI应用
- **内置工具广场**：提供丰富的内置工具，如Google搜索、DALL-E图像生成、维基百科查询等
- **自定义API工具**：支持通过OpenAPI规范创建自定义工具
- **知识库管理**：创建和管理知识库，支持文档上传和处理
- **对话管理**：完整的对话历史记录和管理功能
- **API密钥管理**：为外部调用提供API密钥管理
- **用户认证系统**：支持密码登录和OAuth认证

## 技术栈

- **后端框架**：Flask 3.1.2
- **数据库**：SQLAlchemy + PostgreSQL
- **AI框架**：LangChain
- **向量数据库**：Weaviate
- **消息队列**：Redis + Celery
- **前端支持**：Flask-WTF, Flask-CORS
- **API文档**：Flasgger (Swagger UI)

## 核心组件

### AI应用核心功能
- 应用创建与配置
- 草稿版本与发布版本管理
- 应用复制功能
- 应用调试会话
- 对话历史管理

### 工具系统
- 内置工具提供商（Google、DuckDuckGo、DALL-E、维基百科等）
- 自定义API工具（通过OpenAPI规范）
- 工具分类管理

### 知识库系统
- 数据集管理
- 文档上传与处理
- 文本分段与索引
- 语义检索与关键词检索

### 对话系统
- 实时对话流处理
- 对话摘要生成
- 建议问题生成
- 对话历史管理

## 安装与配置

1. 克隆项目代码：
```bash
git clone <repository-url>
cd llmops-chat
```

2. 安装依赖：
```bash
pip install -e .
```

3. 配置环境变量（创建.env文件）：
```env
SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost/dbname
REDIS_HOST=localhost
REDIS_PORT=6379
OPENAI_API_KEY=your_openai_api_key
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
```

4. 运行数据库迁移：
```bash
flask db upgrade
```

5. 启动服务：
```bash
python app.py
```

## API文档

项目集成了Swagger UI，启动服务后可通过以下地址访问API文档：
```
http://localhost:5000/apidocs
```

## 项目结构

```
llmops-chat/
├── app/                    # 应用入口
├── config/                 # 配置文件
├── internal/               # 核心业务逻辑
│   ├── core/              # 核心组件（Agent、工具等）
│   ├── entity/            # 数据实体定义
│   ├── extension/         # Flask扩展配置
│   ├── handler/           # 请求处理器
│   ├── model/             # 数据模型
│   ├── router/            # 路由配置
│   ├── schema/            # 数据验证模式
│   ├── server/            # 服务器配置
│   ├── service/           # 业务服务层
│   └── task/              # 异步任务
├── pkg/                    # 公共组件包
└── test/                   # 测试文件
```

## 开发指南

### 添加新的内置工具

1. 在[internal/core/tools/builtin_tools/providers/](file:///D:/workspace/py/PythonProject/llmops-chat/internal/core/tools/builtin_tools/providers)目录下创建新的工具提供商目录
2. 实现工具逻辑和参数定义
3. 在提供商配置文件中注册新工具

### 创建AI应用

1. 使用`POST /apps`创建新应用
2. 通过`POST /apps/{app_id}/draft-app-config`配置应用参数
3. 使用`POST /apps/{app_id}/publish`发布应用

### 知识库集成

1. 创建数据集：`POST /datasets`
2. 上传文档：`POST /datasets/{dataset_id}/documents`
3. 在应用配置中关联数据集

### 后续计划
- 添加更多内置工具
- 添加更多知识库集成
- 集成可视化工作流对接langgraph
- 多模型集成
- 多模态功能集成

## 许可证

[添加许可证信息]