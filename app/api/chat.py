from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse, ResourceResponse
from app.rag_services.chat import ChatService

router = APIRouter()
chat_service = ChatService()

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    RAG Chat Endpoint.
    1. Analyzes query.
    2. Retrieves context (Graph + Vector).
    3. Generates answer.
    """
    # Simply call the service
    response = chat_service.chat(request.message)
    
    # Extract answer and suggestions
    answer_text = response.get("content", "")
    suggested_questions = response.get("suggested_questions", [])
    
    return ChatResponse(
        answer=answer_text,
        sources=[], # TODO: Pass source docs through from service
        strategy_used="hybrid", # Placeholder
        suggested_questions=suggested_questions
    )
