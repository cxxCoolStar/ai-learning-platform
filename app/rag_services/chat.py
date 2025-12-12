from app.rag_services.intelligent_router import IntelligentQueryRouter
from app.rag_services.retrieval import RetrievalService
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import get_settings

class ChatService:
    def __init__(self):
        self.router = IntelligentQueryRouter()
        self.retriever = RetrievalService()
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )

    def chat(self, user_query: str):
        # 1. Route
        strategy, analysis = self.router.route_query(user_query)
        
        # 2. Retrieve
        docs = self.retriever.search(user_query, strategy.value)
        
        # 3. Generate
        context = "\n\n".join([f"[{i+1}] Title: {d.metadata.get('title', 'Unknown')}\nURL: {d.metadata.get('url', 'N/A')}\nType: {d.metadata.get('type', 'Unknown')}\nContent: {d.page_content}" for i, d in enumerate(docs)])
        
        prompt = ChatPromptTemplate.from_template("""
        You are an intelligent AI Learning Assistant. Your goal is to help users learn about AI Application Development.
        
        **Capabilities:**
        1. Answer technical questions based on the provided context.
        2. Recommend learning resources (Articles, Code, Videos) from the context.
        3. Explain concepts (e.g., RAG, Agents) using the provided materials.

        **Context:**
        {context}
        
        **User Query:** {question}
        
        **Instructions:**
        - If the user asks for recommendations, select the most relevant resources from the context.
        - Pay attention to the user's requested type (e.g., "GitHub projects", "articles", "videos"). If they ask for "GitHub projects", ONLY recommend resources where Type is "Code".
        - When recommending a resource, format it as follows:
          **[Resource Title]**
          [Summary of the resource]
          [访问链接](URL)
        - Do NOT repeat the title in the link text.
        - If the user asks a technical question, synthesize the answer from the context and cite sources using [1], [2] notation.
        
        Answer:
        """)
        
        chain = prompt | self.llm
        
        response = chain.invoke({"context": context, "question": user_query})
        
        # 4. Generate Suggested Questions (Async or Sequential)
        suggested_questions = self._generate_suggested_questions(user_query, response.content)
        
        # Return object with content and suggested questions
        return {
            "content": response.content,
            "suggested_questions": suggested_questions
        }

    def _generate_suggested_questions(self, user_query: str, answer: str) -> list[str]:
        """
        Generate 3 follow-up questions based on the interaction.
        """
        try:
            prompt = f"""
            Based on the user's query and your answer, suggest 3 relevant follow-up questions the user might want to ask next.
            
            User Query: {user_query}
            Answer: {answer}
            
            Return ONLY a JSON array of strings, e.g. ["Question 1?", "Question 2?", "Question 3?"].
            No markdown, no explanation.
            """
            
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Simple cleanup if LLM returns markdown code block
            if "```" in content:
                content = content.replace("```json", "").replace("```", "")
            
            import json
            questions = json.loads(content)
            return questions[:3]
        except Exception as e:
            # Fallback
            return ["Tell me more", "Explain the code", "Show examples"]
