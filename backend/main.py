
import time
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langgraph.types import Command

from backend.graph.graph import graph


app = FastAPI(
    title="LangGraph News Research Workflow API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    thread_id: str | None = None


class ReviewRequest(BaseModel):
    thread_id: str
    decision: str


def create_initial_state(topic: str) -> dict:
    return {
        "topic": topic,
        "research_plan": "",
        "search_results": [],
        "selected_articles": [],
        "human_review": "",
        "approved_articles": [],
        "processed_articles": [],
        "summaries": [],
        "final_report": "",
        "validation_errors": [],
        "quality_feedback": "",
        "current_node": "",
        "workflow_status": "starting",
        "retry_count": 0,
        "max_retries": 3,
        "error": "",
    }


def get_state_from_graph(config: dict) -> dict:
    snapshot = graph.get_state(config)
    return dict(snapshot.values)


def is_human_review_pending(config: dict) -> bool:
    """Check whether the graph is paused for human review."""
    try:
        snapshot = graph.get_state(config)
        next_nodes = getattr(snapshot, "next", ()) or ()

        if "human_review" in next_nodes:
            return True

        tasks = getattr(snapshot, "tasks", ()) or ()
        for task in tasks:
            interrupts = getattr(task, "interrupts", ()) or ()
            if interrupts:
                return True

        return False
    except Exception:
        return False


def build_response(
    state: dict,
    thread_id: str,
    execution_time: float,
    human_review_required: bool = False,
) -> dict:
    completed_steps = []

    if state.get("research_plan"):
        completed_steps.append("research_planning")

    # Agent execution produces search_results.
    if state.get("search_results"):
        completed_steps.append("agent")

    # Validation may have succeeded even if the status later changed.
    if (
        state.get("validation_errors")
        or state.get("selected_articles")
        or state.get("workflow_status") in {
            "validation_completed",
            "validation_failed_retry",
            "validation_failed",
        }
    ):
        completed_steps.append("validation")

    if state.get("selected_articles"):
        completed_steps.append("article_selection")

    if state.get("human_review"):
        completed_steps.append("human_review")

    if state.get("processed_articles"):
        completed_steps.append("article_processing")

    if state.get("summaries"):
        completed_steps.append("summarization")

    if state.get("final_report"):
        completed_steps.append("report_generation")

    if state.get("quality_feedback"):
        completed_steps.append("quality_check")

    return {
        "thread_id": thread_id,
        "topic": state.get("topic", ""),
        "current_node": state.get("current_node", ""),
        "workflow_status": state.get("workflow_status", ""),
        "completed_steps": completed_steps,
        "validation_errors": state.get("validation_errors", []),
        "selected_articles": state.get("selected_articles", []),
        "approved_articles": state.get("approved_articles", []),
        "processed_articles": state.get("processed_articles", []),
        "summaries": state.get("summaries", []),
        "final_report": state.get("final_report", ""),
        "quality_feedback": state.get("quality_feedback", ""),
        "error": state.get("error", ""),
        "execution_time": round(execution_time, 3),
        "human_review_required": human_review_required,
    }


@app.get("/")
def root():
    return {
        "message": "LangGraph News Research Workflow API is running."
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/research")
def start_research(request: ResearchRequest):
    topic = request.topic.strip()
    thread_id = request.thread_id or str(uuid.uuid4())

    config = {"configurable": {"thread_id": thread_id}}
    initial_state = create_initial_state(topic)
    start_time = time.perf_counter()

    try:
        result = graph.invoke(initial_state, config=config)
        execution_time = time.perf_counter() - start_time
        state = get_state_from_graph(config)
        human_review_required = is_human_review_pending(config)

        if isinstance(result, dict) and result.get("__interrupt__"):
            human_review_required = True

        return build_response(
            state=state,
            thread_id=thread_id,
            execution_time=execution_time,
            human_review_required=human_review_required,
        )

    except Exception as exc:
        execution_time = time.perf_counter() - start_time
        return {
            "thread_id": thread_id,
            "topic": topic,
            "current_node": "backend",
            "workflow_status": "backend_failed",
            "completed_steps": [],
            "validation_errors": [],
            "selected_articles": [],
            "approved_articles": [],
            "processed_articles": [],
            "summaries": [],
            "final_report": "",
            "quality_feedback": "",
            "error": str(exc),
            "execution_time": round(execution_time, 3),
            "human_review_required": False,
        }


@app.post("/research/review")
def review_research(request: ReviewRequest):
    decision = request.decision.strip().lower()

    if decision not in {"approve", "reject"}:
        return {
            "thread_id": request.thread_id,
            "workflow_status": "invalid_review",
            "error": "Decision must be 'approve' or 'reject'.",
        }

    config = {"configurable": {"thread_id": request.thread_id}}
    start_time = time.perf_counter()

    try:
        result = graph.invoke(Command(resume=decision), config=config)
        execution_time = time.perf_counter() - start_time
        state = get_state_from_graph(config)
        human_review_required = is_human_review_pending(config)

        if isinstance(result, dict) and result.get("__interrupt__"):
            human_review_required = True

        return build_response(
            state=state,
            thread_id=request.thread_id,
            execution_time=execution_time,
            human_review_required=human_review_required,
        )

    except Exception as exc:
        execution_time = time.perf_counter() - start_time
        return {
            "thread_id": request.thread_id,
            "workflow_status": "backend_failed",
            "completed_steps": [],
            "error": str(exc),
            "execution_time": round(execution_time, 3),
            "human_review_required": False,
        }


@app.get("/research/{thread_id}")
def get_research_state(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    try:
        state = get_state_from_graph(config)
        human_review_required = is_human_review_pending(config)

        return build_response(
            state=state,
            thread_id=thread_id,
            execution_time=0,
            human_review_required=human_review_required,
        )

    except Exception as exc:
        return {
            "thread_id": thread_id,
            "workflow_status": "backend_failed",
            "error": str(exc),
        }
