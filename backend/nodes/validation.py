from backend.graph.state import ResearchState


def validate_results(state: ResearchState) -> dict:
    """
    Validate the search results before moving to article selection.

    The validation checks whether:
    - Search results exist.
    - There are enough results to continue.
    - Each result has the required article information.

    If the results are invalid and retries are still available,
    the workflow retries the Search node.

    If the retry limit is reached, the workflow stops.
    """

    search_results = state.get("search_results", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    validation_errors = []

    if not search_results:
        validation_errors.append("No search results were found.")

    elif len(search_results) < 3:
        validation_errors.append(
            "Not enough search results were found."
        )

    else:
        for index, article in enumerate(search_results):
            if not article.get("title"):
                validation_errors.append(
                    f"Article {index + 1} is missing a title."
                )

            if not article.get("url"):
                validation_errors.append(
                    f"Article {index + 1} is missing a URL."
                )

    # Validation passed
    if not validation_errors:
        return {
            "validation_errors": [],
            "current_node": "validation",
            "workflow_status": "validation_completed",
            "error": "",
        }

    # Validation failed.
    # Allow another retry only if the current retry count
    # is still below the maximum allowed retries.
    if retry_count < max_retries:
        return {
            "validation_errors": validation_errors,
            "retry_count": retry_count + 1,
            "current_node": "validation",
            "workflow_status": "validation_failed_retry",
            "error": "",
        }

    # Retry limit reached
    return {
        "validation_errors": validation_errors,
        "current_node": "validation",
        "workflow_status": "validation_failed",
        "error": "Maximum retry limit reached during validation.",
    }