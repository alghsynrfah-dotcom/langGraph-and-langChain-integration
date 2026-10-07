import json
import os

import requests
from dotenv import load_dotenv
from langchain.tools import tool


load_dotenv()

NEWS_TIMEOUT = 10
GNEWS_URL = "https://gnews.io/api/v4/search"


@tool
def get_news(topic: str) -> str:
    """
    Get recent news articles about a specific topic using GNews.

    Use this tool when the user asks for current, recent, latest,
    breaking, or newest news.

    Input:
        topic: The news topic to search for.

    Output:
        JSON string containing news articles with title, URL,
        description, and publication date.
    """

    if not topic or not topic.strip():
        return json.dumps(
            {
                "error": "Topic cannot be empty.",
                "articles": [],
            }
        )

    topic = topic.strip()

    if len(topic) > 100:
        return json.dumps(
            {
                "error": "Topic is too long.",
                "articles": [],
            }
        )

    api_key = os.getenv("GNEWS_API_KEY")

    if not api_key:
        return json.dumps(
            {
                "error": "GNEWS_API_KEY is missing from .env",
                "articles": [],
            }
        )

    params = {
        "q": topic,
        "lang": "en",
        "max": 10,
        "apikey": api_key,
    }

    try:
        response = requests.get(
            GNEWS_URL,
            params=params,
            timeout=NEWS_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        articles = data.get("articles", [])

        if not articles:
            return json.dumps(
                {
                    "error": f"No recent news found for: {topic}",
                    "articles": [],
                },
                ensure_ascii=False,
            )

        results = []

        for article in articles[:10]:
            results.append(
                {
                    "title": article.get(
                        "title",
                        "No title",
                    ),
                    "url": article.get(
                        "url",
                        "",
                    ),
                    "description": article.get(
                        "description",
                        "",
                    ),
                    "publishedAt": article.get(
                        "publishedAt",
                        "",
                    ),
                    "source": article.get(
                        "source",
                        {},
                    ),
                }
            )

        return json.dumps(
            {
                "topic": topic,
                "articles": results,
            },
            ensure_ascii=False,
        )

    except requests.Timeout:
        return json.dumps(
            {
                "error": (
                    "GNews request timed out. "
                    "Please try again later."
                ),
                "articles": [],
            }
        )

    except requests.RequestException as error:
        return json.dumps(
            {
                "error": (
                    f"GNews request failed: {str(error)}"
                ),
                "articles": [],
            }
        )

    except Exception as error:
        return json.dumps(
            {
                "error": (
                    f"Unexpected news tool failure: {str(error)}"
                ),
                "articles": [],
            }
        )