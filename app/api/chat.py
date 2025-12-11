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
    
    # Extract sources from context if possible, for now we return generic source structure
    # In a real implementation, ChatService should return structure with sources
    # Since ChatService currently returns a raw string (AIMessage or str), we need to adapt.
    
    answer_text = response.content if hasattr(response, 'content') else str(response)
    
    return ChatResponse(
        answer=answer_text,
        sources=[], # TODO: Pass source docs through from service
        strategy_used="hybrid" # Placeholder
    )
