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
        "thread_id": "human-review-reject-test-1"
    }
}


print("=== START WORKFLOW ===")

result = graph.invoke(
    initial_state,
    config=config,
)

print("\n=== FIRST HUMAN REVIEW ===")

if "__interrupt__" not in result:
    print("ERROR: No interrupt detected.")
    print(result)
    raise SystemExit(1)

print("Human Review interrupt detected.")


print("\n=== RESUMING WITH REJECT ===")

result = graph.invoke(
    Command(resume="reject"),
    config=config,
)

print("\n=== REJECT RESULT ===")
print(result)

print("\n=== HUMAN REVIEW ===")
print("Decision:", result.get("human_review"))

print("\n=== APPROVED ARTICLES ===")
print("Number approved:", len(result.get("approved_articles", [])))

print("\n=== STATUS ===")
print(result.get("workflow_status"))

print("\n=== CURRENT NODE ===")
print(result.get("current_node"))

print("\n=== SECOND HUMAN REVIEW ===")

if "__interrupt__" in result:
    print("Workflow returned to Article Selection and reached Human Review again.")
else:
    print("ERROR: Workflow did not reach Human Review again.")