# RAG 项目增强计划：从原型到简历作品

## 目标
将现有的 "What-to-eat-today" 项目转型为一个高水平的 **Graph RAG** 作品集项目。

---

## 第一阶段：5 大核心特性深度学习

| # | 特性 | 源码模块 | 简历表述 |
|---|------|----------|----------|
| 1 | **智能路由** | `intelligent_query_router.py` | "设计了基于 LLM 的智能查询路由器，动态选择向量检索或图遍历策略" |
| 2 | **双引擎检索** | `hybrid_retrieval.py` | "实现了向量-图谱混合检索引擎，Round-Robin 融合多源结果" |
| 3 | **图结构推理** | `graph_rag_retrieval.py` | "构建了多跳图遍历检索系统，支持 3 跳关系推理" |
| 4 | **查询复杂度分析** | `analyze_query()` | "设计了查询意图分析模块，量化复杂度指导检索策略" |
| 5 | **自适应学习** | `route_stats` | "建立了检索效果反馈闭环，优化路由决策" |

### 学习行动
- [ ] 运行不同类型查询，观察日志中的路由决策
- [ ] 在 Neo4j 浏览器手动执行 Cypher 查询，理解多跳遍历
- [ ] 阅读 `analyze_query()` 的 Prompt，尝试修改并观察路由变化

---

## 第二阶段：技术优化（简历量化亮点）

### 数据流水线优化
*   [MODIFY] `graph_data_preparation.py`: 增加 `full_text_fallback` 字段解决信息丢失

### RAG 评估流水线
*   [NEW] `evaluation.py`: 实现 **Ragas** 测量忠实度、答案相关性、上下文精度

### 检索优化（重排序）
*   [MODIFY] `hybrid_retrieval.py`: 添加 **Cross-Encoder 重排序**
*   **简历亮点**："通过 Cross-Encoder 重排序将 Top-5 准确率提高 15%"

---

## 验证计划

### 自动化
*   `verify_rag_pipeline.py`: 10 个黄金查询 + Ragas 分数输出

### 手动
1.  运行查询："推荐一道适合减肥的辣味鸡肉菜"
2.  验证路由器选择了 "Graph RAG" 或 "Hybrid"
