from typing import TypedDict


class ResearchState(TypedDict):

    topic: str

    research_plan: str

    search_results: list

    selected_articles: list

    human_review: str

    approved_articles: list

    processed_articles: list

    summaries: list

    final_report: str

    validation_errors: list

    quality_feedback: str

    current_node: str

    workflow_status: str

    retry_count: int

    max_retries: int

    error: str