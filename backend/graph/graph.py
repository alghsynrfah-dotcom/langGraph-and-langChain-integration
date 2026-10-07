from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from backend.graph.state import ResearchState

from backend.nodes.agent_node import agent_node
from backend.nodes.article_processing import article_processing
from backend.nodes.article_selection import article_selection
from backend.nodes.branch_failure import branch_failure
from backend.nodes.human_review import human_review
from backend.nodes.quality_check import quality_check
from backend.nodes.report_generation import report_generation
from backend.nodes.research_planning import research_planning
from backend.nodes.summarization import summarization
from backend.nodes.validation import validate_results
from backend.nodes.state_validation import validate_state


# ============================================================
# ROUTERS
# ============================================================


def state_validation_router(state: ResearchState):

    status = state.get(
        "workflow_status",
        "",
    )

    if status == "state_valid":
        return "research_planning"

    if status == "state_invalid":
        return "branch_failure"

    return "branch_failure"


def research_planning_router(state: ResearchState):

    status = state.get(
        "workflow_status",
        "",
    )

    if status == "planning_completed":
        return "agent"

    if status == "invalid_input":
        return END

    return "branch_failure"


def agent_router(state: ResearchState):

    status = state.get(
        "workflow_status",
        "",
    )

    if status == "agent_completed":
        return "validation"

    if status == "agent_failed":
        return END

    return "branch_failure"


def validation_router(state: ResearchState):

    status = state.get(
        "workflow_status",
        "",
    )

    if status == "validation_completed":
        return "article_selection"

    if status == "validation_failed_retry":
        return "agent"

    if status == "validation_failed":
        return END

    return "branch_failure"


def article_selection_router(state: ResearchState):

    status = state.get(
        "workflow_status",
        "",
    )

    if status == "article_selection_completed":
        return "human_review"

    if status == "article_selection_failed":
        return END

    return "branch_failure"

def human_review_router(state: ResearchState):
    decision = state.get("human_review", "")

    if decision == "approved":
        return "article_processing"

    if decision == "rejected":
        return "article_selection"

    return "branch_failure"


def summarization_router(state: ResearchState):

    status = state.get(
        "workflow_status",
        "",
    )

    if status == "summarization_completed":
        return "report_generation"

    if status == "summarization_failed":
        return END

    return "branch_failure"


def report_generation_router(state: ResearchState):

    status = state.get(
        "workflow_status",
        "",
    )

    if status == "report_generated":
        return "quality_check"

    if status == "report_generation_failed":
        return END

    return "branch_failure"


def quality_check_router(state: ResearchState):

    status = state.get(
        "workflow_status",
        "",
    )

    if status == "quality_check_passed":
        return END

    if status == "quality_check_failed_retry":
        return "report_generation"

    if status == "quality_check_failed":
        return END

    return "branch_failure"


# ============================================================
# GRAPH
# ============================================================


builder = StateGraph(ResearchState)


# ------------------------------------------------------------
# Nodes
# ------------------------------------------------------------

builder.add_node(
    "state_validation",
    validate_state,
)

builder.add_node(
    "research_planning",
    research_planning,
)

builder.add_node(
    "agent",
    agent_node,
)

builder.add_node(
    "validation",
    validate_results,
)

builder.add_node(
    "article_selection",
    article_selection,
)

builder.add_node(
    "human_review",
    human_review,
)

builder.add_node(
    "article_processing",
    article_processing,
)

builder.add_node(
    "summarization",
    summarization,
)

builder.add_node(
    "report_generation",
    report_generation,
)

builder.add_node(
    "quality_check",
    quality_check,
)

builder.add_node(
    "branch_failure",
    branch_failure,
)


# ============================================================
# EDGES
# ============================================================


# START
builder.add_edge(
    START,
    "state_validation",
)


# ------------------------------------------------------------
# State Validation
# ------------------------------------------------------------

builder.add_conditional_edges(
    "state_validation",
    state_validation_router,
    {
        "research_planning": "research_planning",
        "branch_failure": "branch_failure",
    },
)


# ------------------------------------------------------------
# Research Planning
# ------------------------------------------------------------

builder.add_conditional_edges(
    "research_planning",
    research_planning_router,
    {
        "agent": "agent",
        "branch_failure": "branch_failure",
        END: END,
    },
)


# ------------------------------------------------------------
# LangChain Agent
# ------------------------------------------------------------

builder.add_conditional_edges(
    "agent",
    agent_router,
    {
        "validation": "validation",
        "branch_failure": "branch_failure",
        END: END,
    },
)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

builder.add_conditional_edges(
    "validation",
    validation_router,
    {
        "article_selection": "article_selection",
        "agent": "agent",
        "branch_failure": "branch_failure",
        END: END,
    },
)


# ------------------------------------------------------------
# Article Selection
# ------------------------------------------------------------

builder.add_conditional_edges(
    "article_selection",
    article_selection_router,
    {
        "human_review": "human_review",
        "branch_failure": "branch_failure",
        END: END,
    },
)


# ------------------------------------------------------------
# Human Review
# ------------------------------------------------------------

builder.add_conditional_edges(
    "human_review",
    human_review_router,
    {
        "article_processing": "article_processing",
        "article_selection": "article_selection",
        "branch_failure": "branch_failure",
    },
)


# ------------------------------------------------------------
# Article Processing
# ------------------------------------------------------------

builder.add_edge(
    "article_processing",
    "summarization",
)


# ------------------------------------------------------------
# Summarization
# ------------------------------------------------------------

builder.add_conditional_edges(
    "summarization",
    summarization_router,
    {
        "report_generation": "report_generation",
        "branch_failure": "branch_failure",
        END: END,
    },
)


# ------------------------------------------------------------
# Report Generation
# ------------------------------------------------------------

builder.add_conditional_edges(
    "report_generation",
    report_generation_router,
    {
        "quality_check": "quality_check",
        "branch_failure": "branch_failure",
        END: END,
    },
)


# ------------------------------------------------------------
# Quality Check
# ------------------------------------------------------------

builder.add_conditional_edges(
    "quality_check",
    quality_check_router,
    {
        "report_generation": "report_generation",
        "branch_failure": "branch_failure",
        END: END,
    },
)


# ------------------------------------------------------------
# Failure Branch
# ------------------------------------------------------------

builder.add_edge(
    "branch_failure",
    END,
)


# ============================================================
# CHECKPOINT
# ============================================================

checkpointer = InMemorySaver()


graph = builder.compile(
    checkpointer=checkpointer,
)
