import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from backend.graph.state import ResearchState


load_dotenv()


def report_generation(state: ResearchState) -> dict:
    """
    Generate a final research report from the article summaries.

    The LLM combines the summaries into one coherent research report
    based on the original research topic.
    """

    topic = state["topic"]
    summaries = state.get("summaries", [])

    if not summaries:
        return {
            "final_report": "",
            "current_node": "report_generation",
            "workflow_status": "report_generation_failed",
            "error": "No summaries available for report generation.",
        }

    api_url = os.getenv("VLLM_API_URL")
    api_key = os.getenv("VLLM_API_KEY")
    model_name = os.getenv("MODEL_NAME")

    if not api_url or not api_key or not model_name:
        return {
            "final_report": "",
            "current_node": "report_generation",
            "workflow_status": "report_generation_failed",
            "error": "LLM configuration is missing.",
        }

    try:
        llm = ChatOpenAI(
            model=model_name,
            temperature=0,
            api_key=api_key,
            base_url=api_url,
        )

        summaries_text = ""

        for index, item in enumerate(summaries, start=1):
            summaries_text += f"""
Article {index}

Title:
{item.get("title", "")}

Source:
{item.get("source", "")}

URL:
{item.get("url", "")}

Summary:
{item.get("summary", "")}

----------------------------------------
"""

        prompt = f"""
You are a professional news research assistant.

Create a final research report about the following topic:

Research topic:
{topic}

The report must be based ONLY on the article summaries provided below.

Article summaries:
{summaries_text}

Write a clear and coherent research report.

The report should include:

1. An introduction to the topic.
2. The most important findings from the articles.
3. A comparison or synthesis of the information when appropriate.
4. Important facts and developments.
5. A short conclusion.

Do not invent information.
Do not add facts that are not supported by the provided summaries.
Clearly distinguish information from different sources when necessary.

Return only the final research report.
"""

        response = llm.invoke(prompt)

        final_report = response.content.strip()

        if not final_report:
            return {
                "final_report": "",
                "current_node": "report_generation",
                "workflow_status": "report_generation_failed",
                "error": "LLM returned an empty report.",
            }

        return {
            "final_report": final_report,
            "current_node": "report_generation",
            "workflow_status": "report_generated",
            "error": "",
        }

    except Exception as exc:
        return {
            "final_report": "",
            "current_node": "report_generation",
            "workflow_status": "report_generation_failed",
            "error": f"Report generation failed: {str(exc)}",
        }