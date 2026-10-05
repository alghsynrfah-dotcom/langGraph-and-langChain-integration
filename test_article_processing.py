from langgraph.types import Command

from backend.graph.graph import graph


# Thread ID is required for checkpointing and Human Review interrupt.
thread_id = "full-workflow-test"

config = {
    "configurable": {
        "thread_id": thread_id,
    }
}


initial_state = {
    "topic": "artificial intelligence",
    "research_plan": "",
    "search_results": [],
    "selected_articles": [],
    "human_review": "",
    "approved_articles": [],
    "processed_articles": [],
    "summaries": [],
    "final_report": "",
    "validation_errors": [],
    "quality_feedback": "",
    "current_node": "",
    "workflow_status": "",
    "retry_count": 0,
    "max_retries": 3,
    "error": "",
}


print("=" * 60)
print("STARTING FULL WORKFLOW")
print("=" * 60)

result = graph.invoke(
    initial_state,
    config=config,
)


# ---------------------------------------------------------
# HUMAN REVIEW INTERRUPT
# ---------------------------------------------------------

if "__interrupt__" in result:

    print("\n" + "=" * 60)
    print("HUMAN REVIEW")
    print("=" * 60)

    interrupts = result["__interrupt__"]

    print("Human Review interrupt detected.")

    if interrupts:
        review_data = interrupts[0].value

        print("\nSelected articles:")
        print("-" * 60)

        for index, article in enumerate(
            review_data.get("articles", []),
            start=1,
        ):
            print(f"\nArticle {index}:")
            print(f"Title: {article.get('title', '')}")
            print(f"Source: {article.get('source', '')}")
            print(f"URL: {article.get('url', '')}")

    # -----------------------------------------------------
    # APPROVE THE SELECTED ARTICLES
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("APPROVING ARTICLES")
    print("=" * 60)

    result = graph.invoke(
        Command(resume="approve"),
        config=config,
    )


# ---------------------------------------------------------
# FINAL WORKFLOW RESULT
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("FINAL WORKFLOW RESULT")
print("=" * 60)

print(f"Current node: {result.get('current_node')}")
print(f"Workflow status: {result.get('workflow_status')}")
print(f"Human decision: {result.get('human_review')}")
print(f"Search results: {len(result.get('search_results', []))}")
print(f"Selected articles: {len(result.get('selected_articles', []))}")
print(f"Approved articles: {len(result.get('approved_articles', []))}")
print(f"Processed articles: {len(result.get('processed_articles', []))}")
print(f"Summaries: {len(result.get('summaries', []))}")

print("\n" + "=" * 60)
print("FINAL REPORT")
print("=" * 60)

final_report = result.get("final_report", "")

if final_report:
    print(final_report)
else:
    print("No final report was generated.")


print("\n" + "=" * 60)
print("QUALITY CHECK")
print("=" * 60)

print(f"Quality feedback: {result.get('quality_feedback', '')}")

print("\n" + "=" * 60)
print("ERROR")
print("=" * 60)

print(result.get("error", ""))


# ---------------------------------------------------------
# FINAL CHECK
# ---------------------------------------------------------

if result.get("workflow_status") == "quality_check_passed":
    print("\n" + "=" * 60)
    print("FULL WORKFLOW TEST PASSED")
    print("=" * 60)
else:
    print("\n" + "=" * 60)
    print("FULL WORKFLOW TEST DID NOT COMPLETE SUCCESSFULLY")
    print("=" * 60)