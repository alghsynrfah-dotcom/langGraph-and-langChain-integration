from backend.graph.state import ResearchState


def article_processing(state: ResearchState) -> dict:
    """
    Process the articles approved by the human reviewer
    and prepare them for the summarization stage.

    The processing includes:
    - Validating that approved articles exist.
    - Cleaning text fields.
    - Preparing a consistent article structure.
    - Storing the processed articles in the workflow State.
    """

    approved_articles = state.get("approved_articles", [])

    if not approved_articles:
        return {
            "processed_articles": [],
            "current_node": "article_processing",
            "workflow_status": "article_processing_failed",
            "error": "No approved articles available for processing.",
        }

    processed_articles = []

    for article in approved_articles:
        title = str(article.get("title", "")).strip()
        description = str(article.get("description", "")).strip()
        content = str(article.get("content", "")).strip()
        url = str(article.get("url", "")).strip()
        source = str(article.get("source", "")).strip()
        published_at = str(article.get("published_at", "")).strip()

        if not title or not url:
            return {
                "processed_articles": [],
                "current_node": "article_processing",
                "workflow_status": "article_processing_failed",
                "error": "An approved article is missing required information.",
            }

        processed_article = {
            "title": title,
            "description": description,
            "content": content,
            "url": url,
            "source": source,
            "published_at": published_at,
        }

        processed_articles.append(processed_article)

    return {
        "processed_articles": processed_articles,
        "current_node": "article_processing",
        "workflow_status": "article_processing_completed",
        "error": "",
    }