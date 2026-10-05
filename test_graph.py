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
        "thread_id": "human-review-test-1"
    }
}

result = graph.invoke(initial_state, config=config)

print("\n=== WORKFLOW RESULT ===")
print(result)

print("\n=== INTERRUPT ===")

if "__interrupt__" in result:
    print(result["__interrupt__"])
else:
    print("No interrupt found.")
