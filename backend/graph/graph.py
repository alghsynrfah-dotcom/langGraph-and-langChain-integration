from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from backend.graph.state import ResearchState
from backend.nodes.article_processing import article_processing
from backend.nodes.article_selection import article_selection
from backend.nodes.branch_failure import branch_failure
from backend.nodes.human_review import human_review
from backend.nodes.quality_check import quality_check
from backend.nodes.report_generation import report_generation
from backend.nodes.research_planning import research_planning
from backend.nodes.search import search_news
from backend.nodes.summarization import summarization
from backend.nodes.validation import validate_results
from backend.nodes.state_validation import validate_state


def research_planning_router(state: ResearchState) -> str:
    """
    Decide where to go after Research Planning.

    Valid input -> Search
    Invalid input -> End
    Unexpected status -> Branch Failure
    """

    status = state.get("workflow_status", "")

    if status == "planning_completed":
        return "search"

    if status == "invalid_input":
        return END

    return "branch_failure"


def validation_router(state: ResearchState) -> str:
    """
    Decide where to go after validation.

    Valid results -> Article Selection
    Invalid results with retries available -> Search
    Retry limit reached -> End
    Unexpected status -> Branch Failure
    """

    status = state.get("workflow_status", "")

    if status == "validation_completed":
        return "article_selection"

    if status == "validation_failed_retry":
        return "search"

    if status == "validation_failed":
        return END

    return "branch_failure"


def article_selection_router(state: ResearchState) -> str:
    """
    Decide where to go after Article Selection.

    Successful selection -> Human Review
    LLM failure -> End
    Unexpected status -> Branch Failure
    """

    status = state.get("workflow_status", "")

    if status == "article_selection_completed":
        return "human_review"

    if status == "article_selection_failed":
        return END

    return "branch_failure"


def human_review_router(state: ResearchState) -> str:
    """
    Decide where to go after Human Review.

    Approved -> Article Processing
    Rejected -> Article Selection
    Invalid decision -> End
    Unexpected status -> Branch Failure
    """

    status = state.get("workflow_status", "")

    if status == "human_review_approved":
        return "article_processing"

    if status == "human_review_rejected":
        return "article_selection"

    if status == "human_review_failed":
        return END

    return "branch_failure"


def summarization_router(state: ResearchState) -> str:
    """
    Decide where to go after Summarization.

    Successful summarization -> Report Generation
    LLM failure -> End
    Unexpected status -> Branch Failure
    """

    status = state.get("workflow_status", "")

    if status == "summarization_completed":
        return "report_generation"

    if status == "summarization_failed":
        return END

    return "branch_failure"


def report_generation_router(state: ResearchState) -> str:
    """
    Decide where to go after Report Generation.

    Successful report generation -> Quality Check
    LLM failure -> End
    Unexpected status -> Branch Failure
    """

    status = state.get("workflow_status", "")

    if status == "report_generation_completed":
        return "quality_check"

    if status == "report_generation_failed":
        return END

    return "branch_failure"


def quality_check_router(state: ResearchState) -> str:
    """
    Decide where to go after Quality Check.

    Passed -> End
    Failed with retries available -> Report Generation
    Retry limit reached -> End
    Unexpected status -> Branch Failure
    """

    status = state.get("workflow_status", "")

    if status == "quality_check_passed":
        return END

    if status == "quality_check_failed_retry":
        return "report_generation"

    if status == "quality_check_failed":
        return END

    return "branch_failure"


builder = StateGraph(ResearchState)


# Add nodes
builder.add_node("research_planning", research_planning)
builder.add_node("search", search_news)
builder.add_node("validation", validate_results)
builder.add_node("article_selection", article_selection)
builder.add_node("human_review", human_review)
builder.add_node("article_processing", article_processing)
builder.add_node("summarization", summarization)
builder.add_node("report_generation", report_generation)
builder.add_node("quality_check", quality_check)
builder.add_node("branch_failure", branch_failure)
builder.add_node("state_validation", validate_state)


# START -> Research Planning
builder.add_edge(START, "state_validation")


def state_validation_router(state: ResearchState) -> str:
    """
    Decide whether the initial State is valid.

    Valid State -> Research Planning
    Invalid State -> Branch Failure
    """

    status = state.get("workflow_status", "")

    if status == "state_valid":
        return "research_planning"

    if status == "invalid_state":
        return "branch_failure"

    return "branch_failure"


builder.add_conditional_edges(
    "state_validation",
    state_validation_router,
    {
        "research_planning": "research_planning",
        "branch_failure": "branch_failure",
    },
)


# Research Planning branching
builder.add_conditional_edges(
    "research_planning",
    research_planning_router,
    {
        "search": "search",
        "branch_failure": "branch_failure",
        END: END,
    },
)


# Search -> Validation
builder.add_edge("search", "validation")


# Validation branching
builder.add_conditional_edges(
    "validation",
    validation_router,
    {
        "article_selection": "article_selection",
        "search": "search",
        "branch_failure": "branch_failure",
        END: END,
    },
)


# Article Selection branching
builder.add_conditional_edges(
    "article_selection",
    article_selection_router,
    {
        "human_review": "human_review",
        "branch_failure": "branch_failure",
        END: END,
    },
)


# Human Review branching
builder.add_conditional_edges(
    "human_review",
    human_review_router,
    {
        "article_processing": "article_processing",
        "article_selection": "article_selection",
        "branch_failure": "branch_failure",
        END: END,
    },
)


# Article Processing -> Summarization
builder.add_edge("article_processing", "summarization")


# Summarization branching
builder.add_conditional_edges(
    "summarization",
    summarization_router,
    {
        "report_generation": "report_generation",
        "branch_failure": "branch_failure",
        END: END,
    },
)


# Report Generation branching
builder.add_conditional_edges(
    "report_generation",
    report_generation_router,
    {
        "quality_check": "quality_check",
        "branch_failure": "branch_failure",
        END: END,
    },
)


# Quality Check branching
builder.add_conditional_edges(
    "quality_check",
    quality_check_router,
    {
        "report_generation": "report_generation",
        "branch_failure": "branch_failure",
        END: END,
    },
)


# Branch Failure -> End
builder.add_edge("branch_failure", END)


# Checkpointer for interrupt/resume
checkpointer = InMemorySaver()

graph = builder.compile(checkpointer=checkpointer)