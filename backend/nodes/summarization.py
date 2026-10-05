import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from backend.graph.state import ResearchState


load_dotenv()


def summarization(state: ResearchState) -> dict:
    """
    Summarize the processed articles using the LLM.

    Each processed article is sent to the LLM to generate:
    - A concise summary.
    - The main points.
    - Important facts or findings.

    The generated summaries are stored in the workflow State.
    """

    processed_articles = state.get("processed_articles", [])

    if not processed_articles:
        return {
            "summaries": [],
            "current_node": "summarization",
            "workflow_status": "summarization_failed",
            "error": "No processed articles available for summarization.",
        }

    api_url = os.getenv("VLLM_API_URL")
    api_key = os.getenv("VLLM_API_KEY")
    model_name = os.getenv("MODEL_NAME")

    if not api_url or not api_key or not model_name:
        return {
            "summaries": [],
            "current_node": "summarization",
            "workflow_status": "summarization_failed",
            "error": "LLM configuration is missing.",
        }

    try:
        llm = ChatOpenAI(
            model=model_name,
            temperature=0,
            api_key=api_key,
            base_url=api_url,
        )

        summaries = []

        for article in processed_articles:

            title = article.get("title", "")
            description = article.get("description", "")
            content = article.get("content", "")

            prompt = f"""
You are a news research assistant.

Summarize the following article for a research report.

Article title:
{title}

Description:
{description}

Article content:
{content}

Provide:
1. A concise summary of the article.
2. The main points.
3. Important facts or findings.

Do not invent information that is not present in the article.

Return the answer in a clear and structured format.
"""

            response = llm.invoke(prompt)

            summaries.append(
                {
                    "title": title,
                    "url": article.get("url", ""),
                    "source": article.get("source", ""),
                    "summary": response.content,
                }
            )

        return {
            "summaries": summaries,
            "current_node": "summarization",
            "workflow_status": "summarization_completed",
            "error": "",
        }

    except Exception as exc:
        return {
            "summaries": [],
            "current_node": "summarization",
            "workflow_status": "summarization_failed",
            "error": f"Summarization failed: {str(exc)}",
        }