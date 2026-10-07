import json
import os
import re

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from backend.tools.news_tool import get_news
from backend.tools.article_tool import fetch_article
from backend.tools.summarization_tool import summarize_article
from backend.tools.calculator_tool import calculate
from backend.tools.email_tool import send_email


load_dotenv()


MAX_AGENT_STEPS = 5

# Keep tool observations small enough for models
# with a 4096-token context window.
MAX_NEWS_OBSERVATION_CHARS = 4500
MAX_ARTICLE_OBSERVATION_CHARS = 3500
MAX_GENERAL_OBSERVATION_CHARS = 2500


def _compact_news_observation(observation) -> str:
    """
    Reduce the GNews result before sending it back to the LLM.

    The full article data is still stored in `sources`.
    Only a compact version is sent to the model so that
    the conversation does not exceed the model context limit.
    """

    try:

        if isinstance(observation, str):
            data = json.loads(observation)
        else:
            data = observation

    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):

        text = str(observation)

        return text[:MAX_NEWS_OBSERVATION_CHARS]

    if not isinstance(data, dict):
        return str(data)[:MAX_NEWS_OBSERVATION_CHARS]

    articles = data.get(
        "articles",
        [],
    )

    if not isinstance(articles, list):
        return json.dumps(
            data,
            ensure_ascii=False,
        )[:MAX_NEWS_OBSERVATION_CHARS]

    compact_articles = []

    # Only send the most relevant first few articles
    # to the LLM. All sources remain stored separately.
    for article in articles[:5]:

        if not isinstance(article, dict):
            continue

        compact_articles.append(
            {
                "title": article.get(
                    "title",
                    "",
                ),
                "url": article.get(
                    "url",
                    "",
                ),
                "description": (
                    article.get(
                        "description",
                        "",
                    ) or ""
                )[:500],
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

    compact_data = {
        "topic": data.get(
            "topic",
            "",
        ),
        "articles": compact_articles,
    }

    return json.dumps(
        compact_data,
        ensure_ascii=False,
    )[:MAX_NEWS_OBSERVATION_CHARS]


def _compact_article_observation(observation) -> str:
    """
    Limit fetched article content before putting it
    into the LLM conversation.
    """

    text = str(observation)

    if len(text) <= MAX_ARTICLE_OBSERVATION_CHARS:
        return text

    return (
        text[:MAX_ARTICLE_OBSERVATION_CHARS]
        + "\n\n[Article content truncated for context size.]"
    )


def _compact_general_observation(observation) -> str:
    """
    Limit generic tool observations.
    """

    text = str(observation)

    if len(text) <= MAX_GENERAL_OBSERVATION_CHARS:
        return text

    return (
        text[:MAX_GENERAL_OBSERVATION_CHARS]
        + "\n\n[Tool output truncated.]"
    )


def create_news_agent():

    api_url = os.getenv("VLLM_API_URL")
    api_key = os.getenv("VLLM_API_KEY")
    model_name = os.getenv("MODEL_NAME")

    if not api_url:
        raise ValueError(
            "VLLM_API_URL is missing from .env"
        )

    if not api_key:
        raise ValueError(
            "VLLM_API_KEY is missing from .env"
        )

    if not model_name:
        raise ValueError(
            "MODEL_NAME is missing from .env"
        )

    model = ChatOpenAI(
        model=model_name,
        temperature=0,
        api_key=api_key,
        base_url=api_url,
    )

    tools = {
        "get_news": get_news,
        "fetch_article": fetch_article,
        "summarize_article": summarize_article,
        "calculate": calculate,
        "send_email": send_email,
    }

    system_prompt = """
You are a news research agent operating inside a LangGraph workflow.

Your job is to reason about the user's research task and choose
the appropriate tools.

AVAILABLE TOOLS:

get_news
- Use for current, recent, latest, today's, breaking, or newest news.
- For current or recent news, ALWAYS use get_news first.
- Do not invent current news from your own knowledge.

fetch_article
- Use to read and inspect a specific article URL.

summarize_article
- Use to summarize article content.

calculate
- Use for mathematical calculations.
- Never calculate mathematical expressions yourself.

send_email
- Use ONLY when the user explicitly asks to send an email.
- Sending an email is an external side effect.

RULES:

1. Do not invent news or sources.
2. Use tools when the task requires external information.
3. After receiving a tool result, decide whether another tool is needed.
4. Only provide a final answer when enough information has been collected.
5. Keep the final answer concise.
6. Answer in the same language as the user's request.
7. If a tool returns an error, do not pretend that the operation succeeded.
8. When using get_news, provide only the actual news topic as the
   Action Input.
9. Never invent tool names.
10. Stop when you have enough information.
11. Do not repeat a tool call unnecessarily.
12. The Observation from a tool may be shortened to fit the model
    context window. Use the available information and continue.

When using a tool, use exactly this format:

Thought: I need to ...
Action: tool_name
Action Input: tool input

After the tool executes, you will receive:

Observation: tool result

Then continue reasoning.

When the task is complete, use:

Final Answer: your answer
"""

    def invoke(question: str) -> dict:

        if not question or not str(question).strip():
            return {
                "answer": "",
                "agent_steps": 0,
                "tools_used": [],
                "sources": [],
                "error": "Agent question cannot be empty.",
            }

        question = str(question).strip()

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ]

        tools_used = []
        sources = []

        for step in range(
            1,
            MAX_AGENT_STEPS + 1,
        ):

            try:

                response = model.invoke(
                    messages
                )

            except Exception as error:

                return {
                    "answer": "",
                    "agent_steps": step,
                    "tools_used": tools_used,
                    "sources": sources,
                    "error": (
                        f"Agent model invocation failed: "
                        f"{str(error)}"
                    ),
                }

            content = response.content

            if not isinstance(
                content,
                str,
            ):
                content = str(content)

            content = content.strip()

            # ------------------------------------------------
            # Final Answer
            # ------------------------------------------------

            if "Final Answer:" in content:

                final_answer = content.split(
                    "Final Answer:",
                    1,
                )[1].strip()

                if not final_answer:

                    return {
                        "answer": "",
                        "agent_steps": step,
                        "tools_used": tools_used,
                        "sources": sources,
                        "error": (
                            "Agent returned an empty "
                            "final answer."
                        ),
                    }

                return {
                    "answer": final_answer,
                    "agent_steps": step,
                    "tools_used": tools_used,
                    "sources": sources,
                    "error": "",
                }

            # ------------------------------------------------
            # Extract Action
            # ------------------------------------------------

            action_match = re.search(
                r"Action:\s*([a-zA-Z_]+)",
                content,
                re.IGNORECASE,
            )

            input_match = re.search(
                r"Action Input:\s*(.*)",
                content,
                re.IGNORECASE | re.DOTALL,
            )

            if (
                not action_match
                or not input_match
            ):

                messages.append(
                    {
                        "role": "assistant",
                        "content": content,
                    }
                )

                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Observation: Invalid agent format. "
                            "You must use exactly:\n"
                            "Thought: ...\n"
                            "Action: tool_name\n"
                            "Action Input: tool input\n\n"
                            "Or, when finished:\n"
                            "Final Answer: ..."
                        ),
                    }
                )

                continue

            tool_name = action_match.group(
                1
            ).strip()

            tool_input = input_match.group(
                1
            ).strip()

            # ------------------------------------------------
            # Clean Tool Input
            # ------------------------------------------------

            if (
                len(tool_input) >= 2
                and (
                    (
                        tool_input.startswith('"')
                        and tool_input.endswith('"')
                    )
                    or (
                        tool_input.startswith("'")
                        and tool_input.endswith("'")
                    )
                )
            ):

                tool_input = tool_input[
                    1:-1
                ].strip()

            # ------------------------------------------------
            # Validate Tool
            # ------------------------------------------------

            if tool_name not in tools:

                messages.append(
                    {
                        "role": "assistant",
                        "content": content,
                    }
                )

                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Observation: Unauthorized "
                            f"or unknown tool "
                            f"'{tool_name}'. "
                            f"Available tools: "
                            f"{', '.join(tools.keys())}"
                        ),
                    }
                )

                continue

            tool = tools[tool_name]

            # ------------------------------------------------
            # Execute Tool
            # ------------------------------------------------

            try:

                if tool_name == "get_news":

                    observation = tool.invoke(
                        {
                            "topic": tool_input,
                        }
                    )

                elif tool_name == "fetch_article":

                    observation = tool.invoke(
                        {
                            "url": tool_input,
                        }
                    )

                elif tool_name == "summarize_article":

                    observation = tool.invoke(
                        {
                            "article_text": tool_input,
                        }
                    )

                elif tool_name == "calculate":

                    observation = tool.invoke(
                        {
                            "expression": tool_input,
                        }
                    )

                else:

                    observation = tool.invoke(
                        tool_input
                    )

            except Exception as error:

                observation = (
                    f"Tool error: {str(error)}"
                )

            # ------------------------------------------------
            # Track Tool
            # ------------------------------------------------

            if tool_name not in tools_used:
                tools_used.append(
                    tool_name
                )

            # ------------------------------------------------
            # Extract Full Sources
            # ------------------------------------------------

            if tool_name == "get_news":

                try:

                    if isinstance(
                        observation,
                        str,
                    ):
                        news_data = json.loads(
                            observation
                        )

                    else:
                        news_data = observation

                    articles = news_data.get(
                        "articles",
                        [],
                    )

                    if isinstance(
                        articles,
                        list,
                    ):

                        for article in articles:

                            if not isinstance(
                                article,
                                dict,
                            ):
                                continue

                            url = article.get(
                                "url",
                                "",
                            )

                            if url:
                                sources.append(
                                    article
                                )

                except (
                    json.JSONDecodeError,
                    TypeError,
                    AttributeError,
                ):
                    pass

            # ------------------------------------------------
            # Compact Observation For LLM
            # ------------------------------------------------

            if tool_name == "get_news":

                llm_observation = (
                    _compact_news_observation(
                        observation
                    )
                )

            elif tool_name == "fetch_article":

                llm_observation = (
                    _compact_article_observation(
                        observation
                    )
                )

            else:

                llm_observation = (
                    _compact_general_observation(
                        observation
                    )
                )

            # ------------------------------------------------
            # Add Tool Interaction
            # ------------------------------------------------

            messages.append(
                {
                    "role": "assistant",
                    "content": content,
                }
            )

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Observation:\n"
                        f"{llm_observation}"
                    ),
                }
            )

        # ----------------------------------------------------
        # Maximum Agent Steps
        # ----------------------------------------------------

        return {
            "answer": "",
            "agent_steps": MAX_AGENT_STEPS,
            "tools_used": tools_used,
            "sources": sources,
            "error": (
                "The agent reached the maximum "
                "number of reasoning steps."
            ),
        }

    return invoke


agent = create_news_agent()