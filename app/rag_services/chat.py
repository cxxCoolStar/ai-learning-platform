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
        - If the user asks for recommendations, select the most relevant resources from the context and explain WHY they are good fits.
        - When recommending a resource, ALWAYS provide its specific URL from the context. Do not use generic homepage links.
        - If the user asks a technical question, synthesize the answer from the context.
        - ALWAYS cite your sources using the numbers [1], [2], etc.
        - If the context is empty or irrelevant, politely say you don't have that information in your knowledge base yet.
        
        Answer:
        """)
        
        chain = prompt | self.llm
        
        return chain.invoke({"context": context, "question": user_query})
