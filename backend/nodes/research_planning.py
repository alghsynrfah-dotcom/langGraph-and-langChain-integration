from backend.graph.state import ResearchState


def research_planning(state: ResearchState) -> dict:
    """
    Prepare the research plan for the given topic.

    This node also validates the initial user input.
    Invalid input stops the workflow before the Search node.
    """

    topic = state.get("topic", "")

    # Invalid input: topic is missing or not a string
    if not isinstance(topic, str):
        return {
            "research_plan": "",
            "current_node": "research_planning",
            "workflow_status": "invalid_input",
            "error": "Research topic must be a text value.",
        }

    # Remove unnecessary spaces
    topic = topic.strip()

    # Invalid input: empty topic
    if not topic:
        return {
            "research_plan": "",
            "current_node": "research_planning",
            "workflow_status": "invalid_input",
            "error": "Research topic is required.",
        }

    # Invalid input: topic is too short
    if len(topic) < 3:
        return {
            "research_plan": "",
            "current_node": "research_planning",
            "workflow_status": "invalid_input",
            "error": "Research topic is too short.",
        }

    research_plan = (
        f"Research the topic '{topic}' by finding recent and relevant "
        "news and articles, validating the results, selecting suitable "
        "articles, analyzing them, and preparing a final report."
    )

    return {
        "research_plan": research_plan,
        "current_node": "research_planning",
        "workflow_status": "planning_completed",
        "error": "",
    }