from langgraph.types import interrupt

from backend.graph.state import ResearchState


def human_review(state: ResearchState) -> dict:
    """
    Pause the workflow and wait for human approval or rejection
    of the selected articles.
    """

    selected_articles = state.get("selected_articles", [])

    if not selected_articles:
        return {
            "current_node": "human_review",
            "workflow_status": "human_review_failed",
            "error": "No selected articles available for human review.",
        }

    review_data = {
        "message": "Please review the selected articles and approve or reject them.",
        "articles": selected_articles,
    }

    human_decision = interrupt(review_data)

    if human_decision == "approve":
        return {
            "human_review": "approve",
            "approved_articles": selected_articles,
            "current_node": "human_review",
            "workflow_status": "human_review_approved",
            "error": "",
        }

    if human_decision == "reject":
        return {
            "human_review": "reject",
            "approved_articles": [],
            "current_node": "human_review",
            "workflow_status": "human_review_rejected",
            "error": "",
        }

    return {
        "human_review": "",
        "approved_articles": [],
        "current_node": "human_review",
        "workflow_status": "human_review_failed",
        "error": "Invalid human review decision.",
    }