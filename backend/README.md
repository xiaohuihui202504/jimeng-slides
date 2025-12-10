# Banana Slides Backend

即梦（Banana Slides）后端服务 - AI驱动的PPT生成系统

## 技术栈

- **框架**: Flask 3.0
- **数据库**: SQLite + SQLAlchemy ORM
- **AI服务**:
  - DeepSeek-V3.2 (文本生成、大纲生成、描述生成)
  - 即梦4.5 (图像生成，支持文生图)
- **PPT处理**: python-pptx
- **并发处理**: ThreadPoolExecutor
- **包管理**: uv
- **依赖管理**: OpenAI SDK (用于DeepSeek API)

## 项目结构

```
backend/
├── app.py                    # Flask应用入口
├── config.py                 # 配置文件
├── models/                   # 数据库模型
│   ├── __init__.py
│   ├── project.py           # Project模型
│   ├── page.py              # Page模型
│   └── task.py              # Task模型
├── services/                 # 服务层
│   ├── __init__.py
│   ├── ai_service.py        # AI相关服务
│   ├── file_service.py      # 文件管理服务
│   ├── export_service.py    # 导出服务
│   └── task_manager.py      # 异步任务管理
├── controllers/              # 控制器层
│   ├── __init__.py
│   ├── project_controller.py
│   ├── page_controller.py
│   ├── template_controller.py
│   ├── export_controller.py
│   └── file_controller.py
├── utils/                    # 工具函数
│   ├── __init__.py
│   ├── response.py          # 统一响应格式
│   └── validators.py        # 数据验证
├── instance/                 # 数据库文件目录（自动创建）
├── uploads/                  # 文件上传目录（自动创建）
├── .env.example             # 环境变量示例
└── README.md                # 本文件
```

## 快速开始

### 1. 安装依赖

本项目使用 [uv](https://github.com/astral-sh/uv) 管理 Python 依赖。所有依赖定义在项目根目录的 `pyproject.toml` 文件中。

在项目根目录下运行：
```bash
uv sync
```

这将自动安装所有必需的依赖包，包括：
- openai SDK (用于DeepSeek API)
- 其他核心依赖包

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# DeepSeek API配置（文本生成）
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_API_BASE=https://api-inference.modelscope.cn/v1
DEEPSEEK_MODEL=deepseek-ai/DeepSeek-V3.2

# 即梦API配置（图像生成）
JIMENG_API_KEY=your-jimeng-api-key
JIMENG_API_BASE=http://115.190.165.156:5100/v1
JIMENG_MODEL=jimeng-4.5
```

**注意**：
- 请将 `your-deepseek-api-key` 和 `your-jimeng-api-key` 替换为实际的API密钥
- 即梦API端点可能需要根据实际部署情况调整

### 3. 运行服务

使用 uv 运行：
```bash
cd backend
uv run python app.py
```
服务将在 `http://localhost:5000` 启动。

## API文档

完整的API文档请参考项目根目录的 `API设计文档.md`。

### 主要端点

#### 项目管理
- `POST /api/projects` - 创建项目
- `GET /api/projects/{project_id}` - 获取项目详情
- `PUT /api/projects/{project_id}` - 更新项目
- `DELETE /api/projects/{project_id}` - 删除项目

#### 大纲生成
- `POST /api/projects/{project_id}/generate/outline` - 生成大纲

#### 描述生成
- `POST /api/projects/{project_id}/generate/descriptions` - 批量生成描述（异步）
- `POST /api/projects/{project_id}/pages/{page_id}/generate/description` - 单页生成

#### 图片生成
- `POST /api/projects/{project_id}/generate/images` - 批量生成图片（异步）
- `POST /api/projects/{project_id}/pages/{page_id}/generate/image` - 单页生成
- `POST /api/projects/{project_id}/pages/{page_id}/edit/image` - 编辑图片

#### 模板管理
- `POST /api/projects/{project_id}/template` - 上传模板
- `DELETE /api/projects/{project_id}/template` - 删除模板

#### 导出
- `GET /api/projects/{project_id}/export/pptx` - 导出PPTX
- `GET /api/projects/{project_id}/export/pdf` - 导出PDF

#### 静态文件
- `GET /files/{project_id}/{type}/{filename}` - 获取文件

## 核心功能

### 1. AI驱动的内容生成

基于 DeepSeek-V3.2 和 即梦4.5 API，支持：

#### 文本生成功能 (DeepSeek-V3.2)
- 自动生成PPT大纲
- 并行生成页面描述
- 大纲解析和优化
- 描述内容优化
- 支持思考模式（thinking）以提升输出质量

#### 图像生成功能 (即梦4.5)
- 文本到图像生成
- 支持多种宽高比（16:9、4:3、1:1等）
- 支持多种分辨率（1K、2K、4K）
- 自动重试机制（最多3次）
- API失败时自动生成占位图
- 最大超时时间：5分钟

### 2. 异步任务处理

使用 `ThreadPoolExecutor` 实现简单但高效的异步任务处理：
- 并行生成多个页面描述
- 并行生成多个页面图片
- 实时任务进度跟踪

### 3. 文件管理

完整的文件管理系统：
- 项目级文件隔离
- 模板图片管理
- 生成图片管理
- 自动清理机制
- MinerU集成文档解析
- 图片自动描述生成（使用DeepSeek-V3.2）

### 4. 数据持久化

使用 SQLite + SQLAlchemy：
- 轻量级，无需额外配置
- 支持关系型数据操作
- 事务保证数据一致性

## 开发说明

### 数据模型

#### Project（项目）
- 项目基本信息
- 模板图片路径
- 项目状态
- 关联的页面和任务

#### Page（页面）
- 页面顺序
- 大纲内容（JSON）
- 描述内容（JSON）
- 生成的图片路径
- 页面状态

#### Task（任务）
- 任务类型（生成描述/生成图片）
- 任务状态
- 进度信息（JSON）
- 错误信息

### 状态机

#### 项目状态
```
DRAFT → OUTLINE_GENERATED → DESCRIPTIONS_GENERATED → GENERATING_IMAGES → COMPLETED
```

#### 页面状态
```
DRAFT → DESCRIPTION_GENERATED → GENERATING → COMPLETED | FAILED
```

#### 任务状态
```
PENDING → PROCESSING → COMPLETED | FAILED
```

### 扩展开发

#### 添加新的AI模型

在 `services/ai_service.py` 中已经集成了多个AI模型：

```python
class AIService:
    def __init__(self, deepseek_api_key: str, deepseek_api_base: str = None,
                 jimeng_api_key: str = None, jimeng_api_base: str = None):
        # DeepSeek for text generation
        # Jimeng for image generation
```

当前支持的模型：
- **DeepSeek-V3.2**: 文本生成，支持思考模式
- **即梦4.5**: 图像生成，支持文生图

如需添加新模型，请修改 `AIService` 类实现。

#### 自定义提示词模板

提示词模板位于 `services/prompts.py`，支持：
- 大纲生成提示词
- 页面描述生成提示词
- 图像生成提示词
- 大纲优化提示词
- 描述优化提示词

所有提示词都支持参考文件内容和思考模式。

#### 添加新的导出格式

在 `services/export_service.py` 中添加新的导出方法：

```python
class ExportService:
    @staticmethod
    def create_custom_format(image_paths, output_file):
        # 实现自定义格式导出
        pass
```


## 测试

### 健康检查

```bash
curl http://localhost:5000/health
```

### 创建项目

```bash
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"creation_type":"idea","idea_prompt":"生成环保主题ppt"}'
```

### 上传模板

```bash
curl -X POST http://localhost:5000/api/projects/{project_id}/template \
  -F "template_image=@template.png"
```

### 生成大纲

```bash
curl -X POST http://localhost:5000/api/projects/{project_id}/generate/outline \
  -H "Content-Type: application/json" \
  -d '{"idea_prompt":"生成环保主题ppt"}'
```

## 常见问题

### Q: 数据库文件在哪里？
A: 在 `backend/instance/database.db`，会自动创建。

### Q: 上传的文件存在哪里？
A: 在 `uploads/{project_id}/` 目录下，按项目隔离。

### Q: 如何修改并发数？
A: 在 `.env` 文件中修改 `MAX_DESCRIPTION_WORKERS` 和 `MAX_IMAGE_WORKERS`。

### Q: 如何切换到其他AI模型？
A: 修改 `services/ai_service.py` 中的 `AIService` 类实现，或通过环境变量配置不同的API端点和密钥。

### Q: 图像生成API失败怎么办？
A: 系统已实现自动降级机制：
- API调用失败时会自动生成占位图片
- 支持最多3次重试
- 不会中断PPT生成流程

### Q: DeepSeek API需要什么权限？
A: 需要魔搭社区的API权限，支持思考模式（thinking）。

### Q: 支持哪些图片格式？
A: PNG, JPG, JPEG, GIF, WEBP。在 `config.py` 中的 `ALLOWED_EXTENSIONS` 配置。

## 许可证

MIT

## 联系方式

如有问题或建议，请通过 GitHub Issues 反馈。

