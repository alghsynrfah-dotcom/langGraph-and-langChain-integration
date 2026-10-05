import os

import requests
from dotenv import load_dotenv

from backend.graph.state import ResearchState


load_dotenv()

GNEWS_API_URL = "https://gnews.io/api/v4/search"


def search_news(state: ResearchState) -> dict:
    topic = state["topic"]

    api_key = os.getenv("GNEWS_API_KEY")

    if not api_key:
        return {
            "search_results": [],
            "current_node": "search",
            "workflow_status": "search_failed",
            "error": "GNEWS_API_KEY is not configured.",
        }

    params = {
        "q": topic,
        "lang": "en",
        "max": 10,
        "apikey": api_key,
    }

    try:
        response = requests.get(
            GNEWS_API_URL,
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        articles = data.get("articles", [])

        search_results = []

        for article in articles:
            search_results.append(
                {
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "content": article.get("content", ""),
                    "url": article.get("url", ""),
                    "image": article.get("image", ""),
                    "published_at": article.get("publishedAt", ""),
                    "source": article.get("source", {}).get("name", ""),
                }
            )

        return {
            "search_results": search_results,
            "current_node": "search",
            "workflow_status": "search_completed",
            "error": "",
        }

    except requests.RequestException as exc:
        return {
            "search_results": [],
            "current_node": "search",
            "workflow_status": "search_failed",
            "error": f"News search failed: {str(exc)}",
        }