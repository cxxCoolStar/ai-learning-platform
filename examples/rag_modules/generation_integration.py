"""
生成集成模块
"""

import logging
import os
import time
from typing import List

from openai import OpenAI
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class GenerationIntegrationModule:
    """生成集成模块 - 负责答案生成"""

    def __init__(self, model_name: str = "kimi-k2-0711-preview", temperature: float = 0.1, max_tokens: int = 2048):
        """
        初始化生成集成模块
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 统一的LLM客户端配置（支持所有兼容OpenAI格式的供应商）
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("请设置 OPENAI_API_KEY 环境变量")

        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.moonshot.cn/v1")

        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url
        )

        logger.info(f"生成模块初始化完成，模型: {model_name}, API地址: {self.base_url}")

    def _build_context_with_citations(self, documents: List[Document]) -> str:
        """构建带引用标记的上下文"""
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            content = doc.page_content.strip()
            if content:
                # 获取元数据信息用于展示
                source = doc.metadata.get('recipe_name', '未知来源')
                level = doc.metadata.get('retrieval_level', '')
                
                # 构建引用标记
                prefix = f"[{i}]"
                if level:
                    prefix += f" [{level.upper()}]"
                
                context_parts.append(f"{prefix} (来源: {source})\n{content}")
        
        return "\n\n".join(context_parts)

    def _build_prompt(self, question: str, context: str) -> str:
        """构建统一的提示词"""
        return f"""
        作为一位专业的烹饪助手，请基于以下信息回答用户的问题。
        
        检索到的相关信息（带有引用编号）：
        {context}

        用户问题：{question}

        请提供准确、实用的回答。要求：
        1. 引用依据：当你使用检索信息中的内容时，请在句子末尾标注引用编号，例如 [1] 或 [1][2]。
        2. 根据问题的性质：
           - 如果是询问多个菜品，请提供清晰的列表
           - 如果是询问具体制作方法，请提供详细步骤
           - 如果是一般性咨询，请提供综合性回答

        重要提醒：
        - 如果问题涉及之前对话中提到的具体菜谱或食材，请严格基于之前提供的信息回答。
        - 每一条关键信息都必须有引用支持。
        - 引用标记要放在句号之前。

        回答：
        """

    def generate_adaptive_answer(self, question: str, documents: List[Document]) -> str:
        """
        智能统一答案生成
        自动适应不同类型的查询，无需预先分类
        """
        # 构建带引用的上下文
        context = self._build_context_with_citations(documents)

        # 使用统一的提示词构建方法
        prompt = self._build_prompt(question, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LightRAG答案生成失败: {e}")
            return f"抱歉，生成回答时出现错误：{str(e)}"
    
    def generate_adaptive_answer_stream(self, question: str, documents: List[Document], max_retries: int = 3):
        """
        LightRAG风格的流式答案生成（带重试机制）
        """
        # 构建带引用的上下文
        context = self._build_context_with_citations(documents)

        # 使用统一的提示词构建方法
        prompt = self._build_prompt(question, context)
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    stream=True,
                    timeout=60  # 增加超时设置
                )
                
                if attempt == 0:
                    print("开始流式生成回答...\n")
                else:
                    print(f"第{attempt + 1}次尝试流式生成...\n")
                
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        yield content  # 使用yield返回流式内容
                
                # 如果成功完成，退出重试循环
                return
                
            except Exception as e:
                logger.warning(f"流式生成第{attempt + 1}次尝试失败: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 递增等待时间
                    print(f"⚠️ 连接中断，{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    # 所有重试都失败，使用非流式作为后备
                    logger.error(f"流式生成完全失败，尝试非流式后备方案")
                    print("⚠️ 流式生成失败，切换到标准模式...")
                    
                    try:
                        fallback_response = self.generate_adaptive_answer(question, documents)
                        yield fallback_response
                        return
                    except Exception as fallback_error:
                        logger.error(f"后备生成也失败: {fallback_error}")
                        error_msg = f"抱歉，生成回答时出现网络错误，请稍后重试。错误信息：{str(e)}"
                        yield error_msg
                        return 