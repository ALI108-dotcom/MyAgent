"""Central router combining all API v1 endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, llm, memory, rag, reasoning, tools

api_router = APIRouter()
api_router.include_router(health.router, tags=["System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication Subsystem"])
api_router.include_router(llm.router, prefix="/agent/llm", tags=["LLM Subsystem"])
api_router.include_router(tools.router, prefix="/agent/tools", tags=["Tools Subsystem"])
api_router.include_router(
    reasoning.router, prefix="/agent/reasoning", tags=["Reasoning Subsystem"]
)
api_router.include_router(
    memory.router, prefix="/agent/memory", tags=["Memory & Context Subsystem"]
)
api_router.include_router(rag.router, prefix="/agent/rag", tags=["RAG & Vector Search Subsystem"])
