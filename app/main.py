"""FastAPI application entry point."""

from __future__ import annotations

import sys
import time
import traceback
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

# --- bootstrap: validate env and import dependencies with visible tracebacks ---
try:
    from app.startup_validation import validate_production_env

    validate_production_env()

    from fastapi import Depends, FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import ORJSONResponse

    from app import __version__
    from app.auth.clerk import get_current_user_id
    from app.config import get_settings
    from app.db.database import database_enabled, init_db
    from app.graph import get_full_graph, get_generate_graph, get_predict_graph
    from app.retriever.vector_store import get_vector_store
    from app.schemas import (
        DashboardResponse,
        EmailInput,
        EvaluateRequest,
        EvaluateResponse,
        GenerateResponse,
        PredictRequest,
        PredictResponse,
    )
    from app.services.dashboard import get_dashboard_service
    from app.state import EmailState
    from app.utils.logger import setup_logging, get_logger
except Exception:
    traceback.print_exc()
    sys.exit(1)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown — defer heavy init; never crash on optional deps."""
    setup_logging()
    settings = get_settings()
    logger.info("Starting AI Email Intelligence Platform v%s", __version__)

    if not settings.has_llm_provider:
        logger.warning("No LLM API key configured — generation endpoints will fail")

    try:
        init_db()
    except Exception as exc:
        logger.warning("Database init skipped: %s", exc)

    try:
        vector_store = get_vector_store()
        if vector_store.document_count == 0:
            logger.info("Vector store empty, ingesting knowledge policies...")
            count = vector_store.ingest_policies()
            logger.info("Ingested %d documents", count)
    except Exception as exc:
        logger.warning("ChromaDB init/ingest skipped: %s", exc)

    yield
    logger.info("Shutting down AI Email Intelligence Platform")


app = FastAPI(
    title="AI Email Intelligence Platform",
    description="Production-quality AI email reply system powered by LangGraph and Claude",
    version=__version__,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list(),
    allow_origin_regex=_settings.cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_state(
    subject: str,
    email: str,
    customer_name: str = "Customer",
    company: str = "",
    expected_response: str = "",
) -> EmailState:
    return EmailState(
        subject=subject,
        email=email,
        customer_name=customer_name,
        company=company,
        expected_response=expected_response,
        node_metrics={},
        errors=[],
    )


def _total_latency(node_metrics: dict[str, Any]) -> float:
    return round(sum(m.get("latency_ms", 0) for m in node_metrics.values()), 2)


@app.get("/")
async def root() -> dict[str, str]:
    """Lightweight root probe — no DB, LLM, or auth."""
    return {"status": "ok"}


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Render health check — env flags only, no DB/LLM/Chroma calls."""
    settings = get_settings()
    return {
        "status": "healthy",
        "version": __version__,
        "model": settings.anthropic_model if settings.anthropic_api_key else settings.gemini_model,
        "chroma_available": False,
        "llm_provider": "claude" if settings.anthropic_api_key else ("gemini" if settings.effective_gemini_key else "none"),
        "fallback_available": bool(settings.effective_gemini_key),
        "providers": {
            "anthropic": bool(settings.anthropic_api_key),
            "gemini": bool(settings.effective_gemini_key),
            "chromadb": False,
            "postgresql": database_enabled(),
        },
    }


@app.post("/predict", response_model=PredictResponse)
async def predict(
    request: PredictRequest,
    user_id: str = Depends(get_current_user_id),
) -> PredictResponse:
    """Classify intent, priority, sentiment, and customer type."""
    _ = user_id
    start = time.perf_counter()
    state = _build_state(request.subject, request.email)
    graph = get_predict_graph()

    try:
        result = await graph.ainvoke(state)
    except Exception as exc:
        logger.error("Predict pipeline failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    latency = round((time.perf_counter() - start) * 1000, 2)
    return PredictResponse(
        intent=result.get("intent", ""),
        priority=result.get("priority", ""),
        sentiment=result.get("sentiment", ""),
        customer_type=result.get("customer_type", ""),
        latency_ms=latency,
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate(
    request: EmailInput,
    user_id: str = Depends(get_current_user_id),
) -> GenerateResponse:
    """Generate a validated support reply."""
    dashboard = get_dashboard_service(user_id)
    state = _build_state(request.subject, request.email, request.customer_name, request.company)
    graph = get_generate_graph()

    try:
        result = await graph.ainvoke(state)
    except Exception as exc:
        logger.error("Generate pipeline failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    node_metrics = result.get("node_metrics", {})
    latency = _total_latency(node_metrics)

    response_data = {
        "subject": request.subject,
        "intent": result.get("intent", ""),
        "generated_reply": result.get("generated_reply", {}),
        "overall_latency_ms": latency,
    }
    dashboard.append_generation(response_data)

    return GenerateResponse(
        subject=request.subject,
        email=request.email,
        intent=result.get("intent", ""),
        priority=result.get("priority", ""),
        sentiment=result.get("sentiment", ""),
        customer_type=result.get("customer_type", ""),
        retrieved_documents=result.get("retrieved_documents", []),
        generated_reply=result.get("generated_reply", {}),
        validated_reply=result.get("validated_reply", {}),
        overall_latency_ms=latency,
    )


@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(
    request: EvaluateRequest,
    user_id: str = Depends(get_current_user_id),
) -> EvaluateResponse:
    """Full pipeline with evaluation metrics."""
    dashboard = get_dashboard_service(user_id)
    state = _build_state(
        request.subject,
        request.email,
        request.customer_name,
        request.company,
        request.expected_response,
    )
    graph = get_full_graph()

    try:
        result = await graph.ainvoke(state)
    except Exception as exc:
        logger.error("Evaluate pipeline failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    eval_result = {
        "subject": request.subject,
        "intent": result.get("intent", ""),
        "generated_reply": result.get("generated_reply", {}),
        "validated_reply": result.get("validated_reply", {}),
        "bertscore": result.get("bertscore", {}),
        "embedding_score": result.get("embedding_score", {}),
        "judge_score": result.get("judge_score", {}),
        "overall_score": result.get("overall_score", 0.0),
        "feedback": result.get("feedback", ""),
        "node_metrics": result.get("node_metrics", {}),
    }
    dashboard.append_evaluation(eval_result)

    return EvaluateResponse(
        subject=request.subject,
        email=request.email,
        generated_reply=result.get("generated_reply", {}),
        validated_reply=result.get("validated_reply", {}),
        bertscore=result.get("bertscore", {}),
        embedding_score=result.get("embedding_score", {}),
        judge_score=result.get("judge_score", {}),
        overall_score=result.get("overall_score", 0.0),
        feedback=result.get("feedback", ""),
        node_metrics=result.get("node_metrics", {}),
    )


@app.get("/dashboard", response_model=DashboardResponse)
async def dashboard(user_id: str = Depends(get_current_user_id)) -> DashboardResponse:
    """Get aggregated dashboard metrics for the authenticated user."""
    dashboard_svc = get_dashboard_service(user_id)
    metrics = dashboard_svc.save_dashboard()
    return DashboardResponse(metrics=metrics.model_dump(mode="json"))


@app.get("/evaluations")
async def list_evaluations(user_id: str = Depends(get_current_user_id)) -> dict[str, Any]:
    """Return evaluation history for the authenticated user only."""
    dashboard_svc = get_dashboard_service(user_id)
    return {"evaluations": dashboard_svc.list_evaluations()}
