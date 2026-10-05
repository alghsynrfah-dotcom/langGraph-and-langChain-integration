import { useEffect, useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

interface Article {
  title?: string;
  description?: string;
  url?: string;
  source?: string;
  published_at?: string;
}

interface ResearchResponse {
  thread_id: string;
  topic: string;
  answer?: string;
  final_report?: string;
  sources?: Article[];
  selected_articles?: Article[];
  approved_articles?: Article[];
  current_node?: string;
  workflow_status?: string;
  completed_steps?: string[];
  validation_errors?: string[];
  quality_feedback?: string;
  error?: string;
  execution_time?: number;
  human_review_required?: boolean;
  human_review?: string;
  tools_used?: string[];
}

function App() {
  const [topic, setTopic] = useState("");
  const [threadId, setThreadId] = useState<string | null>(null);

  const [result, setResult] = useState<ResearchResponse | null>(null);

  const [loading, setLoading] = useState(false);
  const [reviewLoading, setReviewLoading] = useState(false);

  const [error, setError] = useState("");

  const [apiStatus, setApiStatus] = useState("Checking API...");

  // Check backend when frontend starts
  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Backend is not healthy");
        }

        setApiStatus("Backend connected");
      })
      .catch(() => {
        setApiStatus("Backend unavailable");
      });
  }, []);

  const startResearch = async () => {
    if (!topic.trim()) {
      setError("Please enter a research topic.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setThreadId(null);

    const startTime = performance.now();

    try {
      const response = await fetch(`${API_BASE_URL}/research`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: topic.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || data.error || "Failed to start research."
        );
      }

      const executionTime =
        data.execution_time ??
        Number(((performance.now() - startTime) / 1000).toFixed(2));

      const finalData: ResearchResponse = {
        ...data,
        execution_time: executionTime,
      };

      setResult(finalData);
      setThreadId(data.thread_id ?? null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An unexpected error occurred."
      );
    } finally {
      setLoading(false);
    }
  };

  const sendReview = async (decision: "approve" | "reject") => {
    if (!threadId) {
      setError("No active research session.");
      return;
    }

    setReviewLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/research/review`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          thread_id: threadId,
          decision,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || data.error || "Failed to submit review."
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to submit review."
      );
    } finally {
      setReviewLoading(false);
    }
  };

  const refreshResearch = async () => {
    if (!threadId) {
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/research/${threadId}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || data.error || "Failed to get workflow state."
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to refresh workflow."
      );
    }
  };

  const displayReport = result?.final_report || result?.answer || "";

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>AI News Research Assistant</h1>
          <p>
            LangGraph Research & News Analysis Workflow
          </p>
        </div>

        <div
          className={`api-status ${
            apiStatus === "Backend connected" ? "connected" : "offline"
          }`}
        >
          <span className="status-dot" />
          {apiStatus}
        </div>
      </header>

      <main className="container">
        {/* Research Input */}
        <section className="card input-card">
          <h2>Research Topic</h2>

          <p className="section-description">
            Enter a topic to start the research workflow.
          </p>

          <div className="input-row">
            <input
              type="text"
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !loading) {
                  startResearch();
                }
              }}
              placeholder="Example: Artificial Intelligence"
              disabled={loading}
            />

            <button
              className="primary-button"
              onClick={startResearch}
              disabled={loading}
            >
              {loading ? "Researching..." : "Start Research"}
            </button>
          </div>

          {error && (
            <div className="error-box">
              <strong>Error</strong>
              <span>{error}</span>
            </div>
          )}
        </section>

        {/* Workflow Status */}
        {result && (
          <>
            <section className="status-grid">
              <div className="card status-card">
                <span className="label">Current Node</span>
                <strong>
                  {result.current_node || "Unknown"}
                </strong>
              </div>

              <div className="card status-card">
                <span className="label">Workflow Status</span>
                <strong>
                  {result.workflow_status || "Unknown"}
                </strong>
              </div>

              <div className="card status-card">
                <span className="label">Execution Time</span>
                <strong>
                  {result.execution_time !== undefined
                    ? `${result.execution_time}s`
                    : "—"}
                </strong>
              </div>

              <div className="card status-card">
                <span className="label">Thread ID</span>
                <strong className="thread-id">
                  {result.thread_id || "—"}
                </strong>
              </div>
            </section>

            {/* Completed Steps */}
            <section className="card">
              <div className="section-header">
                <div>
                  <h2>Completed Steps</h2>
                  <p className="section-description">
                    Workflow nodes completed so far.
                  </p>
                </div>

                <button
                  className="secondary-button"
                  onClick={refreshResearch}
                >
                  Refresh
                </button>
              </div>

              <div className="steps">
                {result.completed_steps &&
                result.completed_steps.length > 0 ? (
                  result.completed_steps.map((step, index) => (
                    <div className="step" key={`${step}-${index}`}>
                      <span className="step-number">
                        {index + 1}
                      </span>

                      <span>{step}</span>
                    </div>
                  ))
                ) : (
                  <div className="empty-state">
                    No completed steps reported yet.
                  </div>
                )}
              </div>
            </section>

            {/* Validation */}
            <section className="card">
              <h2>Validation</h2>

              {result.validation_errors &&
              result.validation_errors.length > 0 ? (
                <div className="validation-errors">
                  {result.validation_errors.map((validationError, index) => (
                    <div key={index}>
                      ⚠ {validationError}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="success-box">
                  ✓ No validation errors.
                </div>
              )}
            </section>

            {/* Human Review */}
            {result.human_review_required && (
              <section className="card review-card">
                <h2>Human Review Required</h2>

                <p>
                  The workflow is waiting for your decision before
                  continuing.
                </p>

                <div className="review-actions">
                  <button
                    className="approve-button"
                    onClick={() => sendReview("approve")}
                    disabled={reviewLoading}
                  >
                    {reviewLoading ? "Processing..." : "Approve Articles"}
                  </button>

                  <button
                    className="reject-button"
                    onClick={() => sendReview("reject")}
                    disabled={reviewLoading}
                  >
                    Reject & Re-select
                  </button>
                </div>
              </section>
            )}

            {/* Final Report */}
            {displayReport && (
              <section className="card">
                <h2>Final Research Report</h2>

                <div className="report">
                  {displayReport}
                </div>
              </section>
            )}

            {/* Sources */}
            {result.sources && result.sources.length > 0 && (
              <section className="card">
                <h2>Sources</h2>

                <div className="sources">
                  {result.sources.map((article, index) => (
                    <article
                      className="source-card"
                      key={`${article.url}-${index}`}
                    >
                      <div className="source-number">
                        {index + 1}
                      </div>

                      <div className="source-content">
                        <h3>
                          {article.title || "Untitled article"}
                        </h3>

                        {article.description && (
                          <p>{article.description}</p>
                        )}

                        <div className="source-meta">
                          {article.source && (
                            <span>{article.source}</span>
                          )}

                          {article.published_at && (
                            <span>{article.published_at}</span>
                          )}
                        </div>

                        {article.url && (
                          <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            Open Article →
                          </a>
                        )}
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            )}

            {/* Selected Articles */}
            {result.selected_articles &&
              result.selected_articles.length > 0 && (
                <section className="card">
                  <h2>Selected Articles</h2>

                  <div className="sources">
                    {result.selected_articles.map((article, index) => (
                      <article
                        className="source-card"
                        key={`${article.url}-selected-${index}`}
                      >
                        <div className="source-number">
                          {index + 1}
                        </div>

                        <div className="source-content">
                          <h3>
                            {article.title || "Untitled article"}
                          </h3>

                          {article.description && (
                            <p>{article.description}</p>
                          )}

                          {article.url && (
                            <a
                              href={article.url}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              Open Article →
                            </a>
                          )}
                        </div>
                      </article>
                    ))}
                  </div>
                </section>
              )}

            {/* Quality Feedback */}
            {result.quality_feedback && (
              <section className="card">
                <h2>Quality Check</h2>

                <div className="quality-box">
                  {result.quality_feedback}
                </div>
              </section>
            )}

            {/* Errors */}
            {result.error && (
              <section className="card error-card">
                <h2>Workflow Error</h2>

                <div className="error-box">
                  {result.error}
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;