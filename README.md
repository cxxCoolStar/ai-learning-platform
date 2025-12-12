# AI学习平台 🤖✨

> "The most important thing is to learn how to learn." — Sam Altman

一个专注、纯粹的AI学习平台，帮助你在信息洪流中保持专注，高效获取高质量AI知识。

---

## 🎯 项目简介

在这个信息爆炸的时代，我们常常面临这样的困境：

- 🎬 打开社交媒体想学习，却被娱乐内容吸引，浪费大量时间
- 📱 关注的AI博主分享了很多日常内容，但你只想获取有价值的技术洞察
- 🌊 优质资源分散在各个平台，难以系统化地学习和追踪

**AI学习平台**正是为解决这些问题而生。它通过智能爬取、过滤和推荐机制，为你打造一个无干扰的AI学习入口。

---

## ✨ 核心功能

### 📡 智能资源聚合
- 定期自动爬取AI领域的优质网站、博客、论文和项目
- 覆盖GitHub热门项目、技术博客、学术论文等多个来源
- 实时更新，确保内容的时效性

### 🎯 智能内容过滤
- 自动识别和过滤无关内容（娱乐、日常等）
- 只保留有价值的技术洞察、教程和项目
- 告别信息噪音，专注于真正重要的知识

### 📅 每日精选推荐
- **文章推荐**：每天精选最值得阅读的AI技术文章
- **视频推荐**：筛选高质量的AI教程和讲座视频
- **项目推荐**：发现最新的开源项目和实用工具

### 🧘 专注学习体验
- 极简界面设计，减少视觉干扰
- 无广告，无推送，无娱乐内容
- 让你的每一分钟都用在学习上

---

## 💡 为什么选择这个平台？

| 传统方式 | AI学习平台 |
|---------|-----------|
| 在社交媒体上搜索，容易被娱乐内容分散注意力 | 纯粹的学习环境，零干扰 |
| 手动收集和筛选资源，耗时费力 | 自动聚合和过滤，节省时间 |
| 信息分散在各个平台，难以系统学习 | 一站式学习入口，内容集中 |
| 关注的博主混杂大量日常内容 | 智能过滤，只保留有价值的内容 |

---

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/cxxCoolStar/ai-learning-platform.git

# 进入项目目录
cd ai-learning-platform

# 后端环境配置
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# 前端环境配置
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173` 即可开始使用。

---

## 🛠️ 技术栈

### 前端
- React
- TailwindCSS
- Axios

### 后端
- Python FastAPI
- RESTful API

### 爬虫引擎
- Crawl4AI
- BeautifulSoup4
- 定时任务调度

### 数据存储
- SQLite (Metadata)
- Milvus (Vector Database)
- Neo4j (Graph Database)

### AI内容过滤与RAG
- OpenAI / Moonshot API集成
- LangChain
- BM25 + Vector + Graph Hybrid Retrieval

---

## 📖 使用场景

- 🎓 **学生**：系统学习AI知识，准备面试或论文
- 👨‍💻 **开发者**：追踪最新技术趋势，发现实用工具
- 🔬 **研究者**：获取前沿论文和研究动态
- 🚀 **创业者**：了解AI行业动态和应用案例

---

## 🌟 核心理念

我们相信，在AI时代，**"学会如何学习"**比学习具体知识更重要。这个平台不仅仅是一个资源聚合工具，更是一个帮助你培养高效学习习惯的助手。

通过减少干扰、过滤噪音、精准推荐，我们让你能够：

- 💎 专注于真正有价值的内容
- ⚡ 提高学习效率和质量
- 🎯 建立系统化的知识体系
- 🔄 养成持续学习的习惯

---

## 📂 项目结构

```
ai-learning-platform/
├── frontend/          # 前端代码
│   ├── src/
│   ├── public/
│   └── package.json
├── app/               # 后端代码
│   ├── api/           # API 路由
│   ├── core/          # 核心配置
│   ├── services/      # 业务逻辑 (爬虫, 调度)
│   ├── rag_services/  # RAG 检索服务
│   ├── models/        # 数据库模型
│   └── db/            # 数据库连接
├── scripts/           # 实用脚本 (如数据填充)
├── docs/              # 文档
├── requirements.txt   # Python 依赖
└── README.md          # 项目文档
```

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

### 贡献方向

- 🐛 报告Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🌐 添加新的爬虫源
- 🎨 优化UI/UX设计



## 📞 联系方式

- 项目主页：[GitHub Repository](https://github.com/cxxCoolStar/ai-learning-platform)
- 问题反馈：[Issues](https://github.com/cxxCoolStar/ai-learning-platform/issues)
- 邮箱：your.email@example.com

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和支持者！

特别感谢：
- 所有开源项目的贡献者
- AI社区的知识分享者
- 提供宝贵反馈的用户们

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个Star！⭐**

</div>
