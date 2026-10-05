from langgraph.types import Command

from backend.graph.graph import graph


config = {
    "configurable": {
        "thread_id": "human-review-test-1"
    }
}


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
