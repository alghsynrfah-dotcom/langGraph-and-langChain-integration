from langgraph.types import Command

from backend.graph.graph import graph


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

config = {
    "configurable": {
        "thread_id": "human-review-test-2"
    }
}


print("=== START WORKFLOW ===")

result = graph.invoke(
    initial_state,
    config=config,
)

print("\n=== INTERRUPTED ===")

if "__interrupt__" in result:
    print("Human Review interrupt detected.")
else:
    print("ERROR: No interrupt detected.")
    print(result)
    raise SystemExit(1)


print("\n=== RESUMING WITH APPROVE ===")

result = graph.invoke(
    Command(resume="approve"),
    config=config,
)

print("\n=== RESUME RESULT ===")
print(result)

print("\n=== HUMAN REVIEW ===")
print("Decision:", result.get("human_review"))

print("\n=== APPROVED ARTICLES ===")
print("Number approved:", len(result.get("approved_articles", [])))

print("\n=== STATUS ===")
print(result.get("workflow_status"))

print("\n=== CURRENT NODE ===")
print(result.get("current_node"))
