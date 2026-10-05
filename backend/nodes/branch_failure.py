from backend.graph.state import ResearchState


def branch_failure(state: ResearchState) -> dict:
    """
    Handle unexpected conditional branch failures.

    This node is reached when a router returns an unexpected
    branch status that is not part of the normal workflow.
    """

    current_node = state.get("current_node", "unknown")

    return {
        "current_node": current_node,
        "workflow_status": "branch_failed",
        "error": "Unexpected workflow branch encountered.",
    }