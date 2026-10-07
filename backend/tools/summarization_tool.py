import os

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_openai import ChatOpenAI


load_dotenv()

SUMMARY_MAX_LENGTH = 6000


@tool
def summarize_article(article_text: str) -> str:
    """
    Summarize the provided news article.

    Use this tool when the agent needs to summarize
    article content.

    Input:
        article_text: The text content of the article.

    Output:
        A concise summary of the article.
    """

    if not article_text or not article_text.strip():
        return "Error: Article content cannot be empty."

    article_text = article_text.strip()

    # Prevent excessively large input.
    article_text = article_text[:SUMMARY_MAX_LENGTH]

    api_url = os.getenv("VLLM_API_URL")
    api_key = os.getenv("VLLM_API_KEY")
    model_name = os.getenv("MODEL_NAME")

    if not api_url:
        return "Error: VLLM_API_URL is missing from .env"

    if not api_key:
        return "Error: VLLM_API_KEY is missing from .env"

    if not model_name:
        return "Error: MODEL_NAME is missing from .env"

    try:
        model = ChatOpenAI(
            model=model_name,
            temperature=0,
            api_key=api_key,
            base_url=api_url,
        )

        prompt = f"""
Summarize the following news article.

Requirements:
- Keep the summary concise.
- Include the main event or topic.
- Include the most important facts.
- Do not invent information.
- Only use information from the article.

Article:

{article_text}
"""

        response = model.invoke(prompt)

        if not response.content:
            return (
                "Error: The summarization model "
                "returned an empty response."
            )

        return str(response.content).strip()

    except Exception as error:
        return f"Error: Summarization failed: {str(error)}"