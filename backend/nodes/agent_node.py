from backend.agent.agent import agent
from backend.graph.state import ResearchState


def agent_node(state: ResearchState) -> dict:
    """
    Run the LangChain Agent as a LangGraph node.

    The node reads the research topic from the shared state,
    sends it to the LangChain Agent, and stores the agent
    results back into the LangGraph state.
    """

    topic = state.get(
        "topic",
        "",
    )

    # --------------------------------------------------------
    # Validate topic
    # --------------------------------------------------------

    if not isinstance(topic, str):

        error_message = (
            "Research topic must be a text value."
        )

        return {
            "agent_answer": "",
            "agent_steps": 0,
            "tools_used": [],
            "sources": [],
            "search_results": [],
            "agent_error": error_message,
            "current_node": "agent",
            "workflow_status": "agent_failed",
            "error": error_message,
        }

    topic = topic.strip()

    if not topic:

        error_message = (
            "Research topic is required."
        )

        return {
            "agent_answer": "",
            "agent_steps": 0,
            "tools_used": [],
            "sources": [],
            "search_results": [],
            "agent_error": error_message,
            "current_node": "agent",
            "workflow_status": "agent_failed",
            "error": error_message,
        }

    # --------------------------------------------------------
    # Run LangChain Agent
    # --------------------------------------------------------

    try:

        result = agent(topic)

    except Exception as error:

        error_message = (
            f"Agent execution failed: {str(error)}"
        )

        return {
            "agent_answer": "",
            "agent_steps": 0,
            "tools_used": [],
            "sources": [],
            "search_results": [],
            "agent_error": error_message,
            "current_node": "agent",
            "workflow_status": "agent_failed",
            "error": error_message,
        }

    # --------------------------------------------------------
    # Read Agent Result
    # --------------------------------------------------------

    agent_answer = result.get(
        "answer",
        "",
    )

    agent_steps = result.get(
        "agent_steps",
        0,
    )

    tools_used = result.get(
        "tools_used",
        [],
    )

    sources = result.get(
        "sources",
        [],
    )

    agent_error = result.get(
        "error",
        "",
    )

    # --------------------------------------------------------
    # Safety checks
    # --------------------------------------------------------

    if not isinstance(
        tools_used,
        list,
    ):
        tools_used = []

    if not isinstance(
        sources,
        list,
    ):
        sources = []

    # --------------------------------------------------------
    # Agent failed
    # --------------------------------------------------------

    if agent_error:

        return {
            "agent_answer": agent_answer,
            "agent_steps": agent_steps,
            "tools_used": tools_used,
            "sources": sources,

            # Keep compatibility with the existing
            # validation node.
            "search_results": sources,

            "agent_error": agent_error,
            "current_node": "agent",
            "workflow_status": "agent_failed",
            "error": agent_error,
        }

    # --------------------------------------------------------
    # Agent completed successfully
    # --------------------------------------------------------

    return {
        "agent_answer": agent_answer,
        "agent_steps": agent_steps,
        "tools_used": tools_used,
        "sources": sources,

        # The existing validation node expects
        # search_results.
        #
        # The Agent's news sources are therefore passed
        # into the workflow using this state field.
        "search_results": sources,

        "agent_error": "",
        "current_node": "agent",
        "workflow_status": "agent_completed",
        "error": "",
    }