from app.rag_services.intelligent_router import IntelligentQueryRouter
from app.rag_services.retrieval import RetrievalService
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import get_settings
import json
import asyncio

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

    async def chat_stream(self, user_query: str):
        """
        Async generator for streaming chat response
        """
        # 1. Route
        # Note: route_query calls LLM synchronously currently. 
        # Ideally this should be async but for now we wrap it or accept blocking.
        # Since this is a pair programming task, let's keep it simple.
        # Running in thread pool to avoid blocking the event loop
        strategy, analysis = await asyncio.to_thread(self.router.route_query, user_query)
        
        # 2. Retrieve (also blocking, run in thread)
        docs = await asyncio.to_thread(self.retriever.search, user_query, strategy.value)
        
        # 3. Generate
        context = "\n\n".join([f"[{i+1}] Title: {d.metadata.get('title', 'Unknown')}\nURL: {d.metadata.get('url', 'N/A')}\nType: {d.metadata.get('type', 'Unknown')}\nDuration: {d.metadata.get('duration', 'N/A')}\nContent: {d.page_content}" for i, d in enumerate(docs)])
        
        # DEBUG: Log the context to see what the LLM is actually seeing
        print("--- CHAT CONTEXT START ---", flush=True)
        print(context, flush=True)
        print("--- CHAT CONTEXT END ---", flush=True)
        
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
        - **IMPORTANT FOR VIDEO CITATIONS:** If the retrieved information comes from a YouTube video transcript (Type: Video) and the content contains timestamps (e.g., [00:02] or [01:05:30]), you MUST include the timestamp in your citation.
          - Format: 来源[视频名称] [HH:MM:SS] or [MM:SS]
          - **Link Formatting:** When providing the link to the video, append the `t` parameter to the URL.
            - Convert [MM:SS] to `MmSs` (e.g., [15:30] -> `15m30s`).
            - Convert [HH:MM:SS] to `HhMmSs` (e.g., [01:05:30] -> `1h5m30s`).
            - Convert [HH:MM:SS] to `HhMmSs` (e.g., [01:05:30] -> `1h5m30s`).
            - Citation Example: "...as explained by Andrej Karpathy (来源[Intro to LLMs] [15:30])... [观看视频](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=15m30s)"
        - **Anti-Hallucination:** Do NOT estimate or interpolate timestamps (e.g., do not invent [37:15] if the text says [37:10]). ALWAYS use the EXACT timestamp that appears at the **start** of the line/segment where the information is found.
        - **Duration Constraint:** Check the "Duration" field of the source. If a timestamp (e.g. [05:00]) exceeds the video duration (e.g. 00:44), it is HALUCINATED or from a mismatched source. DO NOT CITE IT. Instead, cite the source title without a timestamp.
        - **Detailed Summary Request:** If the user asks to "know more about" ("了解更多") a specific resource, you MUST provide a **Detailed Study Note** instead of a short summary. Structure it as follows:
          1. **Core Concept**: What is this resource about?
          2. **Key Features / Methodology**: How does it work? What are the technical details?
          3. **Significance**: Why is this important?
          4. **Key Takeaways**: What should the user remember?
          5. **Usage/Application**: How can this be used in AI Application Development?
        
        Answer:
        """)
        
        chain = prompt | self.llm
        
        full_answer = ""
        
        # Stream the response
        async for chunk in chain.astream({"context": context, "question": user_query}):
            if chunk.content:
                full_answer += chunk.content
                # Yield SSE format
                yield f"data: {json.dumps({'type': 'token', 'content': chunk.content}, ensure_ascii=False)}\n\n"
        
        # 4. Generate Suggested Questions (Async)
        # We can't use await inside the generator easily for the helper if it's sync, 
        # so we wrap the helper call.
        suggested_questions = await asyncio.to_thread(self._generate_suggested_questions, user_query, full_answer)
        
        # Yield suggestions
        yield f"data: {json.dumps({'type': 'suggestions', 'content': suggested_questions}, ensure_ascii=False)}\n\n"
        
        # Yield Done
        yield "data: [DONE]\n\n"

    def chat(self, user_query: str):
        # 1. Route
        strategy, analysis = self.router.route_query(user_query)
        
        # 2. Retrieve
        docs = self.retriever.search(user_query, strategy.value)
        
        # 3. Generate
        context = "\n\n".join([f"[{i+1}] Title: {d.metadata.get('title', 'Unknown')}\nURL: {d.metadata.get('url', 'N/A')}\nType: {d.metadata.get('type', 'Unknown')}\nDuration: {d.metadata.get('duration', 'N/A')}\nContent: {d.page_content}" for i, d in enumerate(docs)])

        # DEBUG: Log the context
        print("--- CHAT CONTEXT START (SYNC) ---", flush=True)
        print(context, flush=True)
        print("--- CHAT CONTEXT END (SYNC) ---", flush=True)
        
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
        - **IMPORTANT FOR VIDEO CITATIONS:** If the retrieved information comes from a YouTube video transcript (Type: Video) and the content contains timestamps (e.g., [00:02] or [01:05:30]), you MUST include the timestamp in your citation.
          - Format: 来源[视频名称] [HH:MM:SS] or [MM:SS]
          - Format: 来源[视频名称] [HH:MM:SS] or [MM:SS]
          - Example: "...as explained by Andrej Karpathy (来源[Intro to LLMs] [01:15:30])..."
        - **Anti-Hallucination:** Do NOT estimate or interpolate timestamps. ALWAYS use the EXACT timestamp that appears at the **start** of the line/segment where the information is found.
        - **Duration Constraint:** Check the "Duration" field of the source. If a timestamp (e.g. [05:00]) exceeds the video duration (e.g. 00:44), it is HALUCINATED or from a mismatched source. DO NOT CITE IT. Instead, cite the source title without the timestamp.
        - **Detailed Summary Request:** If the user asks to "know more about" ("了解更多") a specific resource, you MUST provide a **Detailed Study Note** instead of a short summary. Structure it as follows:
          1. **Core Concept**: What is this resource about?
          2. **Key Features / Methodology**: How does it work? What are the technical details?
          3. **Significance**: Why is this important?
          4. **Key Takeaways**: What should the user remember?
          5. **Usage/Application**: How can this be used in AI Application Development?
        
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

    def generate_questions_for_resource(self, title: str, summary: str = None) -> list[str]:
        """
        Generate 3 questions based on a specific resource title and summary.
        """
        try:
            prompt = f"""
            Generate 3 interesting questions a user might ask about the following AI resource.
            
            Resource Title: {title}
            Summary: {summary or "No summary available"}
            
            Return ONLY a JSON array of strings, e.g. ["Question 1?", "Question 2?", "Question 3?"].
            No markdown, no explanation.
            """
            
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            if "```" in content:
                content = content.replace("```json", "").replace("```", "")
            
            import json
            questions = json.loads(content)
            return questions[:3]
        except Exception as e:
            return [f"What is {title} about?", "How do I use this?", "Why is this important?"]

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
