from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse, ResourceResponse, GenerateQuestionsRequest, GenerateQuestionsResponse
from app.rag_services.chat import ChatService

router = APIRouter()
chat_service = ChatService()

@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    RAG Chat Streaming Endpoint (SSE).
    Returns a stream of events:
    - {"type": "token", "content": "..."}
    - {"type": "suggestions", "content": [...]}
    """
    return StreamingResponse(
        chat_service.chat_stream(request.message),
        media_type="text/event-stream"
    )

@router.post("/generate_questions", response_model=GenerateQuestionsResponse)
async def generate_questions_endpoint(request: GenerateQuestionsRequest):
    """
    Generate 3 suggested questions based on a specific resource.
    """
    questions = chat_service.generate_questions_for_resource(
        request.resource_title, 
        request.resource_summary
    )
    return GenerateQuestionsResponse(questions=questions)

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
