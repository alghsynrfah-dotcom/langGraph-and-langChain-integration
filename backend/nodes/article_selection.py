import json
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from backend.graph.state import ResearchState


load_dotenv()


def article_selection(state: ResearchState) -> dict:
    """
    Select the three most relevant articles using the LLM.

    The LLM compares the search results with the research topic
    and selects the three articles that are most relevant.
    """

    topic = state["topic"]
    search_results = state.get("search_results", [])

    if not search_results:
        return {
            "selected_articles": [],
            "current_node": "article_selection",
            "workflow_status": "article_selection_failed",
            "error": "No search results available for article selection.",
        }

    api_url = os.getenv("VLLM_API_URL")
    api_key = os.getenv("VLLM_API_KEY")
    model_name = os.getenv("MODEL_NAME")

    if not api_url or not api_key or not model_name:
        return {
            "selected_articles": [],
            "current_node": "article_selection",
            "workflow_status": "article_selection_failed",
            "error": "LLM configuration is missing.",
        }

    articles_for_llm = []

    for index, article in enumerate(search_results):
        articles_for_llm.append(
            {
                "index": index,
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", ""),
                "source": article.get("source", ""),
            }
        )

    prompt = f"""
You are selecting news articles for a research task.

Research topic:
{topic}

Below are the available news articles:

{json.dumps(articles_for_llm, ensure_ascii=False, indent=2)}

Select the 3 articles that are most relevant to the research topic.

Selection criteria:
- Relevance to the research topic
- Quality and usefulness for research
- How directly the article discusses the topic
- Prefer articles with useful content and clear information

Return ONLY a JSON array containing the indexes of the 3 selected articles.

Example:
[0, 4, 7]
"""

    try:
        llm = ChatOpenAI(
            model=model_name,
            temperature=0,
            api_key=api_key,
            base_url=api_url,
        )

        response = llm.invoke(prompt)

        selected_indexes = json.loads(response.content)

        if not isinstance(selected_indexes, list):
            raise ValueError("LLM response is not a list.")

        selected_articles = []

        for index in selected_indexes[:3]:
            if isinstance(index, int) and 0 <= index < len(search_results):
                selected_articles.append(search_results[index])

        if len(selected_articles) != 3:
            raise ValueError(
                "LLM did not select exactly 3 valid articles."
            )

        return {
            "selected_articles": selected_articles,
            "current_node": "article_selection",
            "workflow_status": "article_selection_completed",
            "error": "",
        }

    except Exception as exc:
        return {
            "selected_articles": [],
            "current_node": "article_selection",
            "workflow_status": "article_selection_failed",
            "error": f"Article selection failed: {str(exc)}",
        }