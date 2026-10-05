from backend.graph.state import ResearchState


def validate_state(state: ResearchState) -> dict:
    """
    Validate the workflow State before starting the main workflow.

    The workflow requires:
    - topic to be a string
    - search_results to be a list
    - selected_articles to be a list
    - approved_articles to be a list
    - processed_articles to be a list
    - summaries to be a list
    - validation_errors to be a list
    - retry_count to be an integer
    - max_retries to be an integer
    """

    required_fields = [
        "topic",
        "search_results",
        "selected_articles",
        "approved_articles",
        "processed_articles",
        "summaries",
        "validation_errors",
        "retry_count",
        "max_retries",
    ]

    for field in required_fields:
        if field not in state:
            return {
                "current_node": "state_validation",
                "workflow_status": "invalid_state",
                "error": f"Required state field is missing: {field}",
            }

    if not isinstance(state.get("topic"), str):
        return {
            "current_node": "state_validation",
            "workflow_status": "invalid_state",
            "error": "State field 'topic' must be a string.",
        }

    list_fields = [
        "search_results",
        "selected_articles",
        "approved_articles",
        "processed_articles",
        "summaries",
        "validation_errors",
    ]

    for field in list_fields:
        if not isinstance(state.get(field), list):
            return {
                "current_node": "state_validation",
                "workflow_status": "invalid_state",
                "error": f"State field '{field}' must be a list.",
            }

    if not isinstance(state.get("retry_count"), int):
        return {
            "current_node": "state_validation",
            "workflow_status": "invalid_state",
            "error": "State field 'retry_count' must be an integer.",
        }

    if not isinstance(state.get("max_retries"), int):
        return {
            "current_node": "state_validation",
            "workflow_status": "invalid_state",
            "error": "State field 'max_retries' must be an integer.",
        }

    if state.get("retry_count") < 0:
        return {
            "current_node": "state_validation",
            "workflow_status": "invalid_state",
            "error": "State field 'retry_count' cannot be negative.",
        }

    if state.get("max_retries") < 0:
        return {
            "current_node": "state_validation",
            "workflow_status": "invalid_state",
            "error": "State field 'max_retries' cannot be negative.",
        }

    return {
        "current_node": "state_validation",
        "workflow_status": "state_valid",
        "error": "",
    }