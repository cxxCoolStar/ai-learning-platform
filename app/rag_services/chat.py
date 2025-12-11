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
        context = "\n\n".join([f"[{i+1}] {d.page_content}" for i, d in enumerate(docs)])
        
        prompt = ChatPromptTemplate.from_template("""
        You are an AI Learning Assistant. Answer based on the context.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer (cite sources like [1]):
        """)
        
        chain = prompt | self.llm
        
        return chain.invoke({"context": context, "question": user_query})
