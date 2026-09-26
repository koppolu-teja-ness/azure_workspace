import { useEffect, useMemo, useState } from "react";
import { API_BASE, getRunDetails, getRuns, submitDecision } from "./api";

const VIEWS = {
  PLAN: "plan",
  APPROVAL: "approval",
};

const RUN_SORT = {
  HIGH_RISK: "high_risk",
  STATUS: "status",
  RUN_ID: "run_id",
};

function Badge({ value }) {
  return <span className={`badge badge-${value.replace(/_/g, "-")}`}>{value}</span>;
}

function StatusPill({ value }) {
  return <span className={`status-pill status-${value}`}>{value}</span>;
}

function MetricCard({ label, value }) {
  return (
    <article className="metric-card reveal">
      <p>{label}</p>
      <h3>{value}</h3>
    </article>
  );
}

function App() {
  const [view, setView] = useState(VIEWS.PLAN);
  const [runs, setRuns] = useState([]);
  const [runId, setRunId] = useState("");
  const [runData, setRunData] = useState(null);
  const [runSort, setRunSort] = useState(RUN_SORT.HIGH_RISK);
  const [showAwaitingOnly, setShowAwaitingOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [reviewer, setReviewer] = useState("");
  const [decision, setDecision] = useState("approved");
  const [comments, setComments] = useState("");

  const runPriorityByStatus = {
    awaiting_approval: 0,
    planned: 1,
    approved: 2,
    modified: 3,
    rejected: 4,
    deployed: 5,
    verified: 6,
    failed: 7,
  };

  async function refreshRuns(keepCurrent = true) {
    const runsPayload = await getRuns();
    const items = runsPayload.runs || [];
    setRuns(items);
    if (items.length === 0) {
      setRunId("");
      return;
    }
    if (!keepCurrent || !items.some((item) => item.run_id === runId)) {
      setRunId(items[0].run_id);
    }
  }

  useEffect(() => {
    async function bootstrap() {
      setLoading(true);
      setError("");
      try {
        await refreshRuns(false);
      } catch (err) {
        setError(err.message || "Could not load runs");
      } finally {
        setLoading(false);
      }
    }
    bootstrap();
  }, []);

  useEffect(() => {
    if (!runId) {
      setRunData(null);
      return;
    }

    async function loadRun() {
      setLoading(true);
      setError("");
      try {
        const data = await getRunDetails(runId);
        setRunData(data);
      } catch (err) {
        setError(err.message || "Could not load run details");
      } finally {
        setLoading(false);
      }
    }

    loadRun();
  }, [runId]);

  const plan = runData?.config?.migration_plan || {};
  const riskSummary = plan?.risk_summary || {};
  const riskRows = runData?.risk_assessments || [];
  const pendingApprovalsCount = useMemo(
    () => runs.filter((item) => item.status === "awaiting_approval").length,
    [runs]
  );
  const sortedRuns = useMemo(() => {
    const list = [...runs];
    if (runSort === RUN_SORT.HIGH_RISK) {
      return list.sort((a, b) => {
        const delta = (b.counts?.high_risk || 0) - (a.counts?.high_risk || 0);
        if (delta !== 0) {
          return delta;
        }
        return String(a.run_id).localeCompare(String(b.run_id));
      });
    }
    if (runSort === RUN_SORT.STATUS) {
      return list.sort((a, b) => {
        const aScore = runPriorityByStatus[a.status] ?? 999;
        const bScore = runPriorityByStatus[b.status] ?? 999;
        if (aScore !== bScore) {
          return aScore - bScore;
        }
        return String(a.run_id).localeCompare(String(b.run_id));
      });
    }
    return list.sort((a, b) => String(a.run_id).localeCompare(String(b.run_id)));
  }, [runs, runSort]);
  const displayedRuns = useMemo(() => {
    if (!showAwaitingOnly) {
      return sortedRuns;
    }
    return sortedRuns.filter((run) => run.status === "awaiting_approval");
  }, [showAwaitingOnly, sortedRuns]);
  const highRiskCount = useMemo(
    () => riskRows.filter((item) => item.risk_level === "high_risk").length,
    [riskRows]
  );

  async function onSubmitDecision(event) {
    event.preventDefault();
    setMessage("");
    setError("");

    if (!reviewer.trim()) {
      setError("Reviewer is required.");
      return;
    }

    setSubmitting(true);
    try {
      await submitDecision(runId, {
        decision,
        reviewer: reviewer.trim(),
        comments: comments.trim() || null,
      });
      await refreshRuns(true);
      const refreshed = await getRunDetails(runId);
      setRunData(refreshed);
      setMessage("Decision submitted.");
    } catch (err) {
      setError(err.message || "Could not submit decision");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar reveal">
        <div>
          <p className="eyebrow">Phase 2 / Person A</p>
          <h1>
            Migration Control Deck
            <span className="pending-badge">Pending approvals: {pendingApprovalsCount}</span>
          </h1>
          <p className="subtitle">Planning and human approval gate for Azure to AWS migration runs</p>
        </div>
        <div className="api-hint">API: {API_BASE}</div>
      </header>

      <section className="toolbar reveal">
        <div className="tabs" role="tablist" aria-label="views">
          <button
            className={view === VIEWS.PLAN ? "tab active" : "tab"}
            onClick={() => setView(VIEWS.PLAN)}
            type="button"
          >
            Migration Plan
          </button>
          <button
            className={view === VIEWS.APPROVAL ? "tab active" : "tab"}
            onClick={() => setView(VIEWS.APPROVAL)}
            type="button"
          >
            Approval Gate
          </button>
        </div>

        <label className="run-selector">
          <span>Run</span>
          <select value={runId} onChange={(event) => setRunId(event.target.value)}>
            {runs.map((run) => (
              <option key={run.run_id} value={run.run_id}>
                {run.run_id}
              </option>
            ))}
          </select>
        </label>
      </section>

      <section className="panel reveal runs-overview">
        <div className="runs-header">
          <h2>Runs Overview</h2>
          <div className="runs-controls">
            <label className="toggle-control">
              <input
                type="checkbox"
                checked={showAwaitingOnly}
                onChange={(event) => setShowAwaitingOnly(event.target.checked)}
              />
              <span>Awaiting approval only</span>
            </label>
            <label className="sort-control">
              <span>Sort</span>
              <select value={runSort} onChange={(event) => setRunSort(event.target.value)}>
                <option value={RUN_SORT.HIGH_RISK}>High risk first</option>
                <option value={RUN_SORT.STATUS}>Status priority</option>
                <option value={RUN_SORT.RUN_ID}>Run id</option>
              </select>
            </label>
          </div>
        </div>
        <div className="runs-grid">
          {displayedRuns.map((run) => {
            const selected = run.run_id === runId;
            return (
              <button
                key={run.run_id}
                type="button"
                className={selected ? "run-card selected" : "run-card"}
                onClick={() => setRunId(run.run_id)}
              >
                <div className="run-top">
                  <h3>{run.run_id}</h3>
                  <StatusPill value={run.status} />
                </div>
                <p>
                  High risk: <strong>{run.counts?.high_risk || 0}</strong>
                </p>
                <p>
                  Mappings: <strong>{run.counts?.mappings || 0}</strong>
                </p>
              </button>
            );
          })}
          {displayedRuns.length === 0 ? (
            <article className="empty-state">No runs match the current filter.</article>
          ) : null}
        </div>
      </section>

      {error ? <section className="notice error">{error}</section> : null}
      {message ? <section className="notice success">{message}</section> : null}
      {loading ? <section className="notice">Loading...</section> : null}

      {!loading && runData && view === VIEWS.PLAN ? (
        <main className="panel-grid">
          <MetricCard label="Resources" value={plan.resource_count || 0} />
          <MetricCard label="Auto" value={riskSummary.auto_migratable || 0} />
          <MetricCard label="Needs Review" value={riskSummary.needs_review || 0} />
          <MetricCard label="High Risk" value={riskSummary.high_risk || 0} />

          <section className="panel reveal span-2">
            <h2>Execution Sequence</h2>
            <table>
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Resource Id</th>
                </tr>
              </thead>
              <tbody>
                {(plan.sequence || []).map((item) => (
                  <tr key={`${item.sequence}-${item.resource_id}`}>
                    <td>{item.sequence}</td>
                    <td>{item.name}</td>
                    <td>{item.resource_type}</td>
                    <td className="mono">{item.resource_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="panel reveal span-2">
            <h2>Risk Assessments</h2>
            <table>
              <thead>
                <tr>
                  <th>Resource</th>
                  <th>Risk Level</th>
                  <th>Reasons</th>
                </tr>
              </thead>
              <tbody>
                {riskRows.map((row) => (
                  <tr key={row.resource_id}>
                    <td className="mono">{row.resource_id}</td>
                    <td>
                      <Badge value={row.risk_level} />
                    </td>
                    <td>{(row.reasons || []).join("; ") || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </main>
      ) : null}

      {!loading && runData && view === VIEWS.APPROVAL ? (
        <main className="approval-layout">
          <section className="panel reveal">
            <h2>Current Decision</h2>
            <p className="mono">Status: {runData.status}</p>
            <p>
              Risk items: {riskRows.length} | High risk: {highRiskCount}
            </p>
            <pre>{JSON.stringify(runData.approval || {}, null, 2)}</pre>
          </section>

          <section className="panel reveal">
            <h2>Submit Decision</h2>
            <form onSubmit={onSubmitDecision} className="decision-form">
              <label>
                Reviewer
                <input
                  value={reviewer}
                  onChange={(event) => setReviewer(event.target.value)}
                  placeholder="name or alias"
                  maxLength={100}
                />
              </label>

              <label>
                Decision
                <select value={decision} onChange={(event) => setDecision(event.target.value)}>
                  <option value="approved">approved</option>
                  <option value="rejected">rejected</option>
                  <option value="modified">modified</option>
                </select>
              </label>

              <label>
                Comments
                <textarea
                  value={comments}
                  onChange={(event) => setComments(event.target.value)}
                  rows={6}
                  placeholder="Add rationale, conditions, or requested modifications"
                  maxLength={2000}
                />
              </label>

              <button type="submit" disabled={submitting}>
                {submitting ? "Submitting..." : "Submit"}
              </button>
            </form>
          </section>
        </main>
      ) : null}
    </div>
  );
}

export default App;
