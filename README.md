# jimeng-slides

> 基于 DeepSeek-V3.2 和即梦 4.5 的原生 AI PPT 生成应用，支持想法/大纲/页面描述生成完整 PPT，让 PPT 创作像做梦代码一样简单

![GitHub Stars](https://img.shields.io/github/stars/xiaohuihui202504/jimeng-slides?style=square)
![GitHub Forks](https://img.shields.io/github/forks/xiaohuihui202504/jimeng-slides?style=square)
![Version](https://img.shields.io/badge/version-v0.1.0-4CAF50.svg)
![Docker](https://img.shields.io/badge/Docker-Build-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/github/license/xiaohuihui202504/jimeng-slides?color=FFD54F)

---

## 项目介绍

jimeng-slides 是一个专业的 AI 驱动 PPT 生成应用，致力于降低 PPT 制作门槛，让每个人都能快速创作出美观专业的演示文稿。

### 核心特性

- **三种生成路径**: 支持从「想法 / 大纲 / 页面描述」三种方式起步
- **智能大纲生成**: DeepSeek-V3.2 驱动的结构化大纲和页面描述生成
- **高清页面生成**: 基于即梦 4.5 生成高清、风格统一的页面设计
- **文件自动解析**: 支持 PDF/DOCX/MD/TXT 等格式文件自动解析
- **文本链接提取**: 自动从文本中提取要点、图片链接等信息
- **素材管理系统**: 支持上传参考图片、示例 PPT 等作为风格参考
- **自然语言修改**: 支持对单页或局部进行口头式自然语言修改
- **多格式导出**: 一键导出 PPTX / PDF，16:9 比例开箱即用

### 适用场景

| 用户类型 | 使用场景 |
|---------|---------|
| 小白 | 零门槛快速生成美观 PPT，无需设计经验 |
| PPT 专业人士 | 参考生成的布局和图文元素组合，获取设计灵感 |
| 教育工作者 | 将教学内容快速转换为配图教案 PPT |
| 学生 | 快速完成作业 Pre，专注内容而非排版 |
| 职场人士 | 商业提案、产品介绍快速可视化 |

---

## 在线体验

| 访问方式 | 地址 |
|---------|------|
| 🦆 DuckCloud 域名 | https://jimeng-slides.duckcloud.fun/ |
| 🌐 IP 直连 | http://115.190.165.156:3002/ |

⚡ 即开即用，体验 AI PPT 创作！

---

## 效果展示

| 钱的演变：从贝壳到纸币的旅程 | AI 技术发展历程 |
|:---:|:---:|
| <img src="https://github.com/user-attachments/assets/1a63afc9-ad05-4755-8480-fc4aa64987f1" width="500" alt="案例1"> | <img src="https://github.com/user-attachments/assets/c64cd952-2cdf-4a92-8c34-0322cbf3de4e" width="500" alt="案例2"> |

| 人类对生态环境的影响 | 预制菜智能产线装备研发和产业化 |
|:---:|:---:|
| <img src="https://github.com/user-attachments/assets/d1e15604-767c-42f8-bb41-a2568f18bc2b" width="500" alt="案例3"> | <img src="https://github.com/user-attachments/assets/383eb011-a167-4343-99eb-e1d0568830c7" width="500" alt="案例4"> |

更多案例请查看 [使用案例](https://github.com/xiaohuihui202504/jimeng-slides/issues/2)

---

## 功能清单

| 功能名称 | 功能说明 | 技术栈 | 状态 |
|---------|---------|--------|------|
| 三种创建方式 | 想法/大纲/页面描述三种生成路径 | DeepSeek-V3.2 | ✅ 稳定 |
| 智能大纲生成 | AI 生成结构清晰的大纲和页面描述 | DeepSeek-V3.2 | ✅ 稳定 |
| 高清页面生成 | 基于即梦 4.5 生成风格统一页面 | 即梦 4.5 | ✅ 稳定 |
| 文件自动解析 | PDF/DOCX/MD/TXT 等格式自动解析 | MinerU + 多模态 LLM | ✅ 稳定 |
| 文本链接提取 | 自动提取要点、图片链接 | Python | ✅ 稳定 |
| 素材上传管理 | 上传参考图片、示例 PPT 等 | Flask + Pillow | ✅ 稳定 |
| 自然语言修改 | 口头式自然语言修改与重生成 | DeepSeek-V3.2 | ✅ 稳定 |
| 多格式导出 | PPTX / PDF 一键导出 | python-pptx + reportlab | ✅ 稳定 |

---

## 技术架构

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.2+ | 前端框架 |
| TypeScript | 5.2+ | 类型系统 |
| Vite | 5.0+ | 构建工具 |
| Zustand | 4.4+ | 状态管理 |
| React Router | 6.20+ | 路由管理 |
| Tailwind CSS | 3.3+ | UI 框架 |
| @dnd-kit | 6.1+ | 拖拽功能 |
| Axios | 1.6+ | HTTP 客户端 |

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 主要开发语言 |
| Flask | 3.0+ | Web 框架 |
| SQLAlchemy | 3.1+ | ORM 数据库 |
| OpenAI SDK | 1.0+ | DeepSeek API 调用 |
| python-pptx | 1.0+ | PPTX 导出 |
| reportlab | 4.1+ | PDF 导出 |
| Pillow | 12.0+ | 图片处理 |
| markitdown | latest | 文件解析 |

---

## 安装说明

### 环境要求

- Python 3.10+
- Node.js 16+
- Docker / Docker Compose（推荐）
- 有效的 DeepSeek API 密钥
- 有效的即梦 API 密钥

### 方式一：Docker Compose 部署（推荐）

**0. 克隆代码仓库**

```bash
git clone https://github.com/xiaohuihui202504/jimeng-slides.git
cd jimeng-slides
```

**1. 配置环境变量**

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
JIMENG_API_KEY=your-jimeng-sessionid
JIMENG_API_BASE=http://localhost:8000/v1
JIMENG_MODEL=jimeng-4.5

# 其他配置
PORT=5000
```

**2. 部署即梦 API 服务**

基于 [jimeng-free-api-all](https://github.com/wwwzhouhui/jimeng-free-api-all) 的免费即梦 API 服务。

**Docker 部署：**

```bash
docker pull wwwzhouhui569/jimeng-free-api-all:latest

docker run -it -d --init --name jimeng-free-api-all \
  -p 8000:8000 \
  -e TZ=Asia/Shanghai \
  wwwzhouhui569/jimeng-free-api-all:latest
```

**获取即梦 SessionID：**

1. 访问即梦官网 (https://jimeng.jianying.com/)
2. 登录账号
3. 在浏览器开发者工具中获取 `sessionid` cookie 值
4. 将该值作为 `JIMENG_API_KEY` 使用

**3. 启动服务**

```bash
docker compose up -d
```

访问：
- 前端：http://localhost:3000
- 后端 API：http://localhost:5000

### 方式二：本地开发部署

**后端安装**

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env

# 启动后端
cd backend
uv run python app.py
```

**前端安装**

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:3000

---

## 使用说明

### 基础使用

```
选择创建方式 → 生成大纲 → 编辑确认 → 生成页面 → 导出 PPT
```

1. **选择创建方式**
   - **从构想生成**: 输入一句话/一段想法
   - **从大纲生成**: 粘贴已有大纲
   - **从描述生成**: 直接提供每页描述

2. **生成大纲**
   - AI 自动生成 PPT 大纲与页面结构
   - 支持删除、拖拽、调整顺序
   - 可单个编辑逐步补充和细化

3. **编辑确认**
   - 既可以一次性批量生成
   - 也可以单个编辑逐步补充

4. **生成页面**
   - 基于即梦 4.5 生成高清页面
   - 支持并发生成提升速度
   - 智能降级确保流程不中断

5. **导出 PPT**
   - 一键导出 PPTX / PDF
   - 默认 16:9 比例
   - 开箱即用

### 高级功能

- **文件上传解析**: 支持 PDF/DOCX/MD/TXT 等格式自动解析
- **素材管理**: 上传参考图片、示例 PPT 作为风格参考
- **自然语言修改**: 对单页或局部进行口头式修改
- **版本管理**: 支持历史版本管理和回滚

---

## 配置说明

### 即梦 API 配置

本项目使用基于 [jimeng-free-api-all](https://github.com/wwwzhouhui/jimeng-free-api-all) 的免费即梦 API 服务。

**支持的模型：**
- `jimeng-4.5`: 即梦 4.5 文生图模型
- `jimeng-video-3.0`: 即梦视频 3.0 模型（视频生成）

**注意事项：**
- 确保即梦 API 服务在端口 8000 上运行
- `JIMENG_API_KEY` 应填入从即梦官网获取的 `sessionid`
- API 与 OpenAI 接口格式完全兼容

### DeepSeek API 配置

使用魔搭社区的 DeepSeek-V3.2 模型进行文本生成、大纲生成和描述生成。

---

## 项目结构

```
jimeng-slides/
├── frontend/                  # React 前端应用
│   ├── src/
│   │   ├── pages/            # 页面组件
│   │   ├── components/       # UI 组件
│   │   ├── store/            # Zustand 状态管理
│   │   ├── api/              # API 接口
│   │   ├── types/            # TypeScript 类型定义
│   │   └── utils/            # 工具函数
│   ├── public/               # 静态资源
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── backend/                   # Flask 后端应用
│   ├── app.py                # Flask 应用入口
│   ├── config.py             # 配置文件
│   ├── models/               # 数据库模型
│   ├── services/             # 服务层
│   ├── controllers/          # API 控制器
│   └── utils/                # 工具函数
├── tests/                     # 测试文件
├── v0_demo/                   # 早期演示版本
├── docker-compose.yml         # Docker Compose 配置
├── .env.example               # 环境变量示例
├── pyproject.toml             # Python 项目配置
└── README.md
```

---

## 开发指南

### 本地开发

```bash
# 后端开发
uv sync
cd backend
uv run python app.py

# 前端开发
cd frontend
npm install
npm run dev
```

### Docker 开发

```bash
# 生产环境
docker compose up -d

# 开发环境
docker compose -f docker-compose-dev.yml up -d --build

# 查看日志
docker compose logs -f
```

### 常用命令

```bash
# 停止服务
docker compose down

# 重新构建并启动
docker compose up -d --build

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
```

---

## 开发计划

| 状态 | 里程碑 |
| --- | --- |
| ✅ 已完成 | 从想法、大纲、页面描述三种路径创建 PPT |
| ✅ 已完成 | 解析文本中的 Markdown 格式图片 |
| ✅ 已完成 | PPT 单页添加更多素材 |
| ✅ 已完成 | PPT 单页框选区域 Vibe 口头编辑 |
| ✅ 已完成 | 素材模块：生成、上传等 |
| ✅ 已完成 | 支持多种文件的上传 + 解析 |
| ✅ 已完成 | 支持 Vibe 口头调整大纲和描述 |
| 🔄 进行中 | 支持已生成图片的元素分割和进一步编辑 |
| 🔄 进行中 | 网络搜索 |
| 🔄 进行中 | Agent 模式 |
| 🧭 规划中 | 优化前端加载速度 |
| 🧭 规划中 | 在线播放功能 |
| 🧭 规划中 | 简单的动画和页面切换效果 |
| 🧭 规划中 | 多语种支持 |
| 🧭 规划中 | 用户系统 |

---

## 常见问题

<details>
<summary>Q: 如何获取 DeepSeek API Key？</summary>

A: 访问魔搭社区 (https://modelscope.cn/) 注册账号，获取 API Key。
</details>

<details>
<summary>Q: 如何获取即梦 SessionID？</summary>

A:
1. 访问即梦官网 (https://jimeng.jianying.com/)
2. 登录账号
3. 在浏览器开发者工具中获取 `sessionid` cookie 值
</details>

<details>
<summary>Q: 支持哪些文件格式？</summary>

A: 支持 PDF、DOCX、DOC、MD、TXT 等格式文件的自动解析。
</details>

<details>
<summary>Q: 可以自定义页面风格吗？</summary>

A: 可以上传参考图片、示例 PPT 作为风格参考，系统会根据参考素材生成风格统一的页面。
</details>

<details>
<summary>Q: 生成的 PPT 是什么比例？</summary>

A: 默认 16:9 比例，保证在主流显示设备上的观感。
</details>

---

## 贡献指南

欢迎通过 [Issue](https://github.com/xiaohuihui202504/jimeng-slides/issues) 和 [Pull Request](https://github.com/xiaohuihui202504/jimeng-slides/pulls) 为本项目贡献力量！

---

## 开源协议

MIT License

---

## 项目统计

### Star History

如果觉得项目不错，欢迎点个 Star ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=xiaohuihui202504/jimeng-slides&type=Date)](https://star-history.com/#xiaohuihui202504/jimeng-slides&Date)

---

## 致谢

本项目基于以下开源项目的二次开发和改造：

- **[banana-slides](https://github.com/Anionex/banana-slides)**

---

## 技术交流群

欢迎加入技术交流群，分享你的使用心得和反馈建议：

![技术交流群](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/image-20260809134347048.png)

---

## 作者联系

- **微信**: laohaibao2025
- **邮箱**: 75271002@qq.com

![微信二维码](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Screenshot_20260123_095617_com.tencent.mm.jpg)

---

## 打赏

如果这个项目对你有帮助，欢迎请我喝杯咖啡 ☕

**微信支付**

![微信支付](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/image-20250914152855543.png)
