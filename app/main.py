"""FastAPI application entry point."""

import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app import __version__
from app.config import get_settings
from app.graph import get_full_graph, get_generate_graph, get_predict_graph
from app.retriever.vector_store import get_vector_store
from app.schemas import (
    DashboardResponse,
    EmailInput,
    EvaluateRequest,
    EvaluateResponse,
    GenerateResponse,
    HealthResponse,
    PredictRequest,
    PredictResponse,
)
from app.services.dashboard import DashboardService, get_dashboard_service
from app.state import EmailState
from app.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown."""
    setup_logging()
    logger.info("Starting AI Email Intelligence Platform v%s", __version__)

    vector_store = get_vector_store()
    if vector_store.document_count == 0:
        logger.info("Vector store empty, ingesting knowledge policies...")
        count = vector_store.ingest_policies()
        logger.info("Ingested %d documents", count)

    yield
    logger.info("Shutting down AI Email Intelligence Platform")


app = FastAPI(
    title="AI Email Intelligence Platform",
    description="Production-quality AI email reply system powered by LangGraph and Claude",
    version=__version__,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
    return round(
        sum(m.get("latency_ms", 0) for m in node_metrics.values()),
        2,
    )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    settings = get_settings()
    vector_store = get_vector_store()
    return HealthResponse(
        status="healthy",
        version=__version__,
        model=settings.anthropic_model if settings.anthropic_api_key else settings.gemini_model,
        chroma_available=vector_store.document_count > 0,
        llm_provider="claude" if settings.anthropic_api_key else "gemini",
        fallback_available=bool(settings.gemini_api_key),
    )


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest) -> PredictResponse:
    """Classify intent, priority, sentiment, and customer type."""
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
    dashboard: DashboardService = Depends(get_dashboard_service),
) -> GenerateResponse:
    """Generate a validated support reply."""
    start = time.perf_counter()
    state = _build_state(
        request.subject,
        request.email,
        request.customer_name,
        request.company,
    )
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
    dashboard: DashboardService = Depends(get_dashboard_service),
) -> EvaluateResponse:
    """Full pipeline with evaluation metrics."""
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
async def dashboard(
    dashboard_svc: DashboardService = Depends(get_dashboard_service),
) -> DashboardResponse:
    """Get aggregated dashboard metrics."""
    metrics = dashboard_svc.save_dashboard()
    return DashboardResponse(metrics=metrics.model_dump(mode="json"))
