from backend.graph.state import ResearchState


def quality_check(state: ResearchState) -> dict:
    """
    Check the quality of the final research report.

    The quality check verifies that:
    - A research topic exists.
    - Article summaries exist.
    - A final report exists.
    - The final report contains enough information.

    If the check fails and retries are still available,
    retry Report Generation.

    If the retry limit is reached, the workflow stops.
    """

    final_report = state.get("final_report", "").strip()
    summaries = state.get("summaries", [])
    topic = state.get("topic", "").strip()

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    quality_feedback = []

    # Check topic
    if not topic:
        quality_feedback.append("Research topic is missing.")

    # Check summaries
    if not summaries:
        quality_feedback.append(
            "No article summaries are available."
        )

    # Check final report
    if not final_report:
        quality_feedback.append("Final report is empty.")

    # Check report length
    if final_report and len(final_report) < 200:
        quality_feedback.append(
            "Final report is too short."
        )

    # Quality passed
    if not quality_feedback:
        return {
            "quality_feedback": "Quality check passed.",
            "current_node": "quality_check",
            "workflow_status": "quality_check_passed",
            "error": "",
        }

    # Quality failed.
    # Allow another retry only if the current retry count
    # is still below the maximum allowed retries.
    if retry_count < max_retries:
        return {
            "quality_feedback": " ".join(quality_feedback),
            "retry_count": retry_count + 1,
            "current_node": "quality_check",
            "workflow_status": "quality_check_failed_retry",
            "error": "",
        }

    # Retry limit reached
    return {
        "quality_feedback": " ".join(quality_feedback),
        "current_node": "quality_check",
        "workflow_status": "quality_check_failed",
        "error": "Maximum retry limit reached during quality check.",
    }