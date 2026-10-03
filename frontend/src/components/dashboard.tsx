"use client";

import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import {
  ArrowClockwiseIcon,
  ArrowRightIcon,
  ArrowUpRightIcon,
  BellIcon,
  ChartLineUpIcon,
  CheckCircleIcon,
  CheckIcon,
  CircleNotchIcon,
  ClockIcon,
  CommandIcon,
  CubeIcon,
  FileTextIcon,
  FingerprintIcon,
  GitCommitIcon,
  MagnifyingGlassIcon,
  PulseIcon,
  ShieldCheckIcon,
  SquaresFourIcon,
  StackIcon,
  WarningCircleIcon,
} from "@phosphor-icons/react";
import { agents, evidence, memoryIncidents, recommendation, timeline } from "@/lib/data";
import { ApprovalCard, type ApprovalDecision } from "./approval";
import { Brand, BrandMark, CopyButton, DemoLabel } from "./ui";
import { TelemetryChart } from "./telemetry-chart";

type View = "overview" | "incidents" | "agents" | "audit";
type Tab = "evidence" | "rca" | "advisor" | "approval" | "audit";
type AuditEntry = {
  time: string;
  title: string;
  detail: string;
  kind: "info" | "approval" | "success";
};
const navigation = [
  { id: "overview", title: "Overview", icon: SquaresFourIcon },
  { id: "incidents", title: "Incidents", icon: WarningCircleIcon },
  { id: "agents", title: "Agents", icon: StackIcon },
  { id: "audit", title: "Audit trail", icon: FileTextIcon },
] as const;
const tabs: { id: Tab; title: string }[] = [
  { id: "evidence", title: "Evidence timeline" },
  { id: "rca", title: "Root cause" },
  { id: "advisor", title: "Fix Advisor" },
  { id: "approval", title: "Approval queue" },
  { id: "audit", title: "Audit trail" },
];
const initialAudit: AuditEntry[] = [
  {
    time: "10:43:10",
    title: "Incident created",
    detail: "Sentinel correlated 3 alerts for payment-service.",
    kind: "info",
  },
  {
    time: "10:43:18",
    title: "Investigation completed",
    detail: "Five evidence sources support a probable resource-lifecycle regression.",
    kind: "info",
  },
  {
    time: "10:43:22",
    title: "Guidance generated",
    detail: "Fix Advisor supplied developer guidance. Application source code was not modified.",
    kind: "info",
  },
  {
    time: "10:43:26",
    title: "Approval requested",
    detail: "Response proposed a scoped rollback. Human approval is required.",
    kind: "approval",
  },
];

function AuditList({ entries }: { entries: AuditEntry[] }) {
  return (
    <div className="dashboard-audit">
      {entries.map((entry, index) => (
        <div className="audit-entry" key={`${entry.title}-${index}`}>
          <span className={`audit-icon ${entry.kind}`}>
            {entry.kind === "success" ? (
              <CheckCircleIcon size={17} />
            ) : entry.kind === "approval" ? (
              <ShieldCheckIcon size={17} />
            ) : (
              <ClockIcon size={17} />
            )}
          </span>
          <time className="mono">{entry.time}</time>
          <div>
            <strong>{entry.title}</strong>
            <p>{entry.detail}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function Dashboard({ standalone = false }: { standalone?: boolean }) {
  const [view, setView] = useState<View>("overview");
  const [tab, setTab] = useState<Tab>("evidence");
  const [query, setQuery] = useState("");
  const [incidentId, setIncidentId] = useState("1042");
  const [status, setStatus] = useState<"Investigating" | "Validating" | "Recovered">(
    "Investigating",
  );
  const [audit, setAudit] = useState<AuditEntry[]>(initialAudit);
  const [approvalKey, setApprovalKey] = useState(0);
  const [approvalPending, setApprovalPending] = useState(true);
  const [approvalDecision, setApprovalDecision] = useState<ApprovalDecision | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState(0);
  const [showDiff, setShowDiff] = useState(false);
  const [replaying, setReplaying] = useState(false);
  const [replayStep, setReplayStep] = useState(0);
  const [verifying, setVerifying] = useState(false);
  const [toast, setToast] = useState("");
  const search = useRef<HTMLInputElement>(null);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const instance = useId().replace(/:/g, "");
  useEffect(() => () => timers.current.forEach(clearTimeout), []);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 4000);
    return () => clearTimeout(timer);
  }, [toast]);
  useEffect(() => {
    if (!standalone) return;
    const shortcut = (event: globalThis.KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        search.current?.focus();
      }
    };
    document.addEventListener("keydown", shortcut);
    return () => document.removeEventListener("keydown", shortcut);
  }, [standalone]);

  const replay = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setApprovalDecision(null);
    setStatus("Investigating");
    setIncidentId("1042");
    setView("overview");
    setTab("evidence");
    setQuery("");
    setAudit(initialAudit);
    setApprovalKey((value) => value + 1);
    setApprovalPending(true);
    setReplaying(true);
    setReplayStep(0);
    setVerifying(false);
    for (let i = 1; i <= 4; i++)
      timers.current.push(
        setTimeout(() => {
          setReplayStep(i);
          if (i === 4) {
            setReplaying(false);
            setToast("Incident traced. Five evidence sources connected.");
          }
        }, i * 800),
      );
  };
  const onDecision = (decision: ApprovalDecision) => {
    setApprovalDecision(decision);
    setApprovalPending(false);
    setAudit((entries) => [
      ...entries,
      {
        time: decision.time,
        title: `Rollback ${decision.decision} by you`,
        detail: decision.reason,
        kind: "approval",
      },
    ]);
    if (decision.decision === "approved") setStatus("Validating");
    setToast(
      decision.decision === "approved"
        ? "Approval recorded. Recovery checks are now available."
        : "Rejection recorded. No action was taken.",
    );
  };
  const verify = () => {
    if (status !== "Validating" || verifying) return;
    setVerifying(true);
    timers.current.push(
      setTimeout(() => {
        setStatus("Recovered");
        setVerifying(false);
        setAudit((entries) => [
          ...entries,
          {
            time: new Date().toLocaleTimeString("en-GB", { timeZone: "UTC" }),
            title: "Recovery verified",
            detail:
              "The approved rollback restored v1.8.2. Error rate returned to 0.2%, p95 latency to 120ms, and the pool to 6/30 active connections.",
            kind: "success",
          },
        ]);
        setToast("Recovery verified. The incident is preserved in memory.");
      }, 1300),
    );
  };
  const changeTab = (event: KeyboardEvent<HTMLButtonElement>) => {
    const index = tabs.findIndex((item) => item.id === tab);
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    else if (event.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = tabs.length - 1;
    else return;
    event.preventDefault();
    setTab(tabs[next].id);
    document.getElementById(`${instance}-tab-${tabs[next].id}`)?.focus();
  };
  const recovered = status === "Recovered";
  const allIncidents = [
    {
      id: "1042",
      title: "Payment API degradation",
      service: "payment-service",
      status,
      severity: "HIGH",
    },
    ...memoryIncidents.map((incident) => ({
      id: incident.id,
      title: incident.title,
      service: incident.service,
      status: "Recovered",
      severity: "MEDIUM",
    })),
  ];
  const results = allIncidents.filter((incident) =>
    `${incident.id} ${incident.title} ${incident.service} ${incident.status}`
      .toLowerCase()
      .includes(query.toLowerCase().trim()),
  );
  const historical = memoryIncidents.find((incident) => incident.id === incidentId);
  const showResults = query.trim().length > 0 || view === "incidents";
  const replayLabels = [
    "Ingesting runtime signals…",
    "Anomaly detected. Incident created.",
    "Deployment and commit correlated.",
    "Five evidence sources connected.",
    "Probable root cause identified.",
  ];
  const PageHeading = standalone ? "h1" : "h3";

  return (
    <div className={`dashboard-shell ${standalone ? "dashboard-standalone" : ""}`}>
      {standalone && (
        <div className="console-sitebar">
          <Brand />
          <a href="/">
            Back to the story
            <ArrowUpRightIcon size={16} />
          </a>
        </div>
      )}
      <div className="dashboard-app">
        <aside className="dashboard-sidebar">
          <div className="dashboard-workspace">
            <BrandMark />
            <div>
              <strong>Sentinel</strong>
              <span className="mono">WORKSPACE / DEMO</span>
            </div>
          </div>
          <nav aria-label="Console navigation">
            {navigation.map((item) => (
              <button
                type="button"
                key={item.id}
                className={view === item.id ? "active" : ""}
                aria-pressed={view === item.id}
                onClick={() => {
                  setView(item.id);
                  setQuery("");
                }}
              >
                <item.icon size={17} />
                <span>{item.title}</span>
                {item.id === "incidents" && <b>{recovered ? 0 : 1}</b>}
              </button>
            ))}
          </nav>
          <div className="sidebar-context">
            <span className="mono">CONNECTED</span>
            <div>
              <GitCommitIcon size={14} />
              GitHub
            </div>
            <div>
              <CubeIcon size={14} />
              CI/CD
            </div>
            <div>
              <PulseIcon size={14} />
              Runtime
            </div>
          </div>
          <div className="sidebar-bottom">
            <span className={`status-dot ${recovered ? "is-green" : ""}`} />
            <span className="mono">production</span>
            <ShieldCheckIcon size={14} />
          </div>
        </aside>
        <div className="dashboard-main">
          <header className="dashboard-topbar">
            <div>
              <span className="dashboard-current-view">
                {navigation.find((item) => item.id === view)?.title}
              </span>
              <span className="dashboard-slash">/</span>
              <span className="mono">production</span>
            </div>
            <label className="dashboard-search">
              <MagnifyingGlassIcon size={15} />
              <span className="sr-only">Search incidents</span>
              <input
                ref={search}
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search incidents…"
              />
              <kbd>
                <CommandIcon size={10} />K
              </kbd>
            </label>
            <span className="console-demo-badge">DEMO</span>
          </header>
          <div className="dashboard-content">
            <div className="dashboard-page-heading">
              <div>
                <PageHeading>
                  {view === "overview"
                    ? "Your production. In context."
                    : view === "incidents"
                      ? "Every incident, connected."
                      : view === "agents"
                        ? "Your response team."
                        : "Every decision has a record."}
                </PageHeading>
                <p>
                  {view === "overview"
                    ? "All systems tell a story. Here’s yours."
                    : view === "incidents"
                      ? "Search active incidents and verified incident memory."
                      : view === "agents"
                        ? "Six specialized agents. One human-governed workflow."
                        : "The complete, attributable history of this example incident."}
                </p>
              </div>
              <button
                type="button"
                className="dashboard-replay"
                onClick={replay}
                disabled={replaying}
              >
                <ArrowClockwiseIcon size={13} />
                <span>{replaying ? "Replaying…" : "Replay incident"}</span>
              </button>
            </div>
            {replaying && (
              <div className="dashboard-replay-status" role="status">
                <CircleNotchIcon className="is-checking" size={15} />
                {replayLabels[replayStep]}
              </div>
            )}
            {showResults ? (
              <div className="incident-search-results">
                <div className="results-heading mono">
                  {results.length} INCIDENT{results.length === 1 ? "" : "S"}
                  {query && ` MATCHING “${query}”`}
                </div>
                {results.length === 0 ? (
                  <div className="dashboard-empty">
                    <MagnifyingGlassIcon size={29} />
                    <h4>No matching incidents.</h4>
                    <p>Try a service name, incident number, or status.</p>
                    <button type="button" onClick={() => setQuery("")} className="text-link">
                      Clear search
                      <ArrowRightIcon size={16} />
                    </button>
                  </div>
                ) : (
                  results.map((incident) => (
                    <button
                      type="button"
                      key={incident.id}
                      className="incident-result"
                      onClick={() => {
                        setIncidentId(incident.id);
                        setQuery("");
                        setView("overview");
                      }}
                    >
                      <span className="mono">INC-{incident.id}</span>
                      <span>
                        <strong>{incident.title}</strong>
                        <span>{incident.service}</span>
                      </span>
                      <span
                        className={`incident-status ${incident.status === "Recovered" ? "recovered" : ""}`}
                      >
                        {incident.status}
                      </span>
                      <ArrowUpRightIcon size={17} />
                    </button>
                  ))
                )}
              </div>
            ) : view === "agents" ? (
              <div className="dashboard-agents-list">
                {agents.map((agent) => (
                  <article key={agent.id}>
                    <div className="agent-list-mark">
                      <FingerprintIcon size={24} weight="light" />
                    </div>
                    <div>
                      <h4>{agent.name}</h4>
                      <p>{agent.description}</p>
                      <span>{agent.boundary}</span>
                    </div>
                    <a href={`/docs#${agent.id}`} aria-label={`Documentation for ${agent.name}`}>
                      <ArrowUpRightIcon size={19} />
                    </a>
                  </article>
                ))}
              </div>
            ) : view === "audit" ? (
              <AuditList entries={audit} />
            ) : historical ? (
              <div className="dashboard-historical">
                <span className="mono text-recovered">
                  <CheckCircleIcon size={16} /> RECOVERED / INCIDENT MEMORY
                </span>
                <h4>INC-{historical.id}</h4>
                <h3>{historical.title}</h3>
                <p>{historical.cause}</p>
                <div className="historical-lesson">
                  <span className="mono">LESSON RETAINED</span>
                  <p>{historical.lesson}</p>
                </div>
                <button
                  type="button"
                  className="button button-outline"
                  onClick={() => setIncidentId("1042")}
                >
                  Return to INC-1042
                  <ArrowRightIcon size={16} />
                </button>
              </div>
            ) : (
              <>
                <div className="dashboard-metrics">
                  <div>
                    <span>Active incidents</span>
                    <strong>
                      {recovered ? "0" : "1"}
                      <small className={recovered ? "text-recovered" : "text-incident"}>
                        {recovered ? "All clear" : "1 high severity"}
                      </small>
                    </strong>
                  </div>
                  <div>
                    <span>Error rate</span>
                    <strong className={recovered ? "text-recovered" : "text-incident"}>
                      {recovered ? "0.2" : "7.4"}
                      <small>%</small>
                    </strong>
                  </div>
                  <div>
                    <span>Service health</span>
                    <strong>
                      {recovered ? "12" : "9"}
                      <small>/ 12 healthy</small>
                    </strong>
                  </div>
                  <div>
                    <span>AI investigations</span>
                    <strong>
                      1<small>Root cause found</small>
                    </strong>
                  </div>
                </div>
                <div className="dashboard-primary">
                  <div className="dashboard-service-chart">
                    <div className="dashboard-chart-title">
                      <span>
                        <PulseIcon size={14} />
                        Payment API
                      </span>
                      <span className="mono">ERROR RATE / 5 MIN</span>
                    </div>
                    <TelemetryChart
                      compact
                      level={4}
                      recovered={recovered}
                      deploymentLabel={recovered ? "v1.8.2 restored" : "v1.8.3 deployed"}
                    />
                    <div className="dashboard-chart-footer">
                      <span>
                        <CubeIcon size={13} />
                        {recovered ? "Approved rollback v1.8.2" : "Recent deployment v1.8.3"}
                      </span>
                      <span className="mono">{recovered ? "VERIFIED" : "10:42:18"}</span>
                    </div>
                  </div>
                  <div className="dashboard-incident-summary">
                    <div>
                      <span className="mono">INC-1042</span>
                      <span className={`incident-status ${recovered ? "recovered" : ""}`}>
                        {status}
                      </span>
                    </div>
                    <h4>
                      Payment API
                      <br />
                      degradation
                    </h4>
                    <div className="incident-summary-detail">
                      <span>Root cause confidence</span>
                      <strong>91%</strong>
                    </div>
                    <div className="incident-summary-detail">
                      <span>Affected services</span>
                      <strong>3</strong>
                    </div>
                    <div className="incident-summary-detail">
                      <span>Blast radius</span>
                      <strong>Payment + Checkout</strong>
                    </div>
                    {status === "Validating" && (
                      <button
                        type="button"
                        className="verify-recovery-button"
                        disabled={verifying}
                        onClick={verify}
                      >
                        {verifying ? (
                          <CircleNotchIcon className="is-checking" size={14} />
                        ) : (
                          <CheckCircleIcon size={14} />
                        )}
                        {verifying ? "Verifying runtime…" : "Verify recovery"}
                      </button>
                    )}
                    {recovered && (
                      <div className="dashboard-recovered-note">
                        <CheckCircleIcon size={14} />
                        Recovery verified
                      </div>
                    )}
                  </div>
                </div>
                <div className="dashboard-investigation">
                  <div
                    className="dashboard-tabs"
                    role="tablist"
                    aria-label="Incident investigation"
                  >
                    {tabs.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        id={`${instance}-tab-${item.id}`}
                        role="tab"
                        aria-selected={tab === item.id}
                        aria-controls={`${instance}-panel`}
                        tabIndex={tab === item.id ? 0 : -1}
                        onKeyDown={changeTab}
                        onClick={() => setTab(item.id)}
                      >
                        {item.title}
                        {item.id === "approval" && approvalPending && <span>1</span>}
                      </button>
                    ))}
                  </div>
                  <div
                    id={`${instance}-panel`}
                    className="dashboard-tab-panel"
                    role="tabpanel"
                    aria-labelledby={`${instance}-tab-${tab}`}
                    tabIndex={0}
                  >
                    {tab === "evidence" && (
                      <div className="dashboard-evidence-timeline">
                        {timeline.slice(0, 6).map((event, index) => (
                          <button
                            type="button"
                            key={event.time}
                            onClick={() => {
                              setSelectedEvidence(Math.min(index, evidence.length - 1));
                              setTab("rca");
                            }}
                          >
                            <span className={`small-event-dot ${index === 2 ? "incident" : ""}`} />
                            <time className="mono">{event.time}</time>
                            <strong>{event.title}</strong>
                            <span>{event.detail}</span>
                            <ArrowUpRightIcon size={13} />
                          </button>
                        ))}
                      </div>
                    )}
                    {tab === "rca" && (
                      <div className="dashboard-rca">
                        <div className="rca-summary">
                          <span className="mono">PROBABLE ROOT CAUSE / 91% CONFIDENCE</span>
                          <h4>Database resources are not reliably released.</h4>
                          <p>
                            PaymentService.java, lines 42-48. Repeated requests exhaust the
                            connection pool.
                          </p>
                        </div>
                        <div className="rca-source-tabs" role="group" aria-label="Evidence sources">
                          {evidence.map((source, index) => (
                            <button
                              type="button"
                              key={source.id}
                              aria-pressed={selectedEvidence === index}
                              onClick={() => setSelectedEvidence(index)}
                            >
                              <CheckIcon size={12} />
                              {source.title}
                            </button>
                          ))}
                        </div>
                        <div className="rca-source-detail">
                          <p>{evidence[selectedEvidence].detail}</p>
                          <code>{evidence[selectedEvidence].code}</code>
                        </div>
                      </div>
                    )}
                    {tab === "advisor" && (
                      <div className="dashboard-advisor">
                        <div>
                          <span className="mono">DEVELOPER GUIDANCE</span>
                          <h4>Make resource cleanup automatic.</h4>
                          <p>
                            Use try-with-resources for Connection, PreparedStatement, and ResultSet.
                            Test sustained traffic and exceptional exit paths.
                          </p>
                          <div className="advisor-boundary">
                            <ShieldCheckIcon size={17} />
                            The developer writes the fix. Sentinel never modifies application source
                            code.
                          </div>
                        </div>
                        <div className="advisor-tab-actions">
                          <CopyButton value={recommendation} />
                          <button
                            type="button"
                            className="text-link"
                            onClick={() => setShowDiff((value) => !value)}
                            aria-expanded={showDiff}
                          >
                            {showDiff ? "Hide" : "View"} developer’s example fix
                            <ArrowRightIcon size={14} />
                          </button>
                        </div>
                        {showDiff && (
                          <pre className="dashboard-code-example">
                            <code>
                              {
                                "// Developer-authored example\ntry (Connection connection = dataSource.getConnection();\n     PreparedStatement stmt = connection.prepareStatement(sql)) {\n  stmt.setString(1, payment.id());\n  try (ResultSet result = stmt.executeQuery()) {\n    return mapResult(result);\n  }\n}"
                              }
                            </code>
                          </pre>
                        )}
                      </div>
                    )}
                    {tab === "approval" && (
                      <div className="dashboard-approval">
                        <ApprovalCard
                          key={approvalKey}
                          compact
                          onDecision={onDecision}
                          initialDecision={approvalDecision}
                        />
                        <div className="dashboard-approval-context">
                          <ShieldCheckIcon size={28} weight="light" />
                          <h4>
                            Nothing happens
                            <br />
                            without your say.
                          </h4>
                          <p>
                            This operational rollback is an example alternative while a developer
                            prepares the source-code fix.
                          </p>
                          <p>
                            Approve it with a reason, then run recovery checks. Every decision
                            appears in the audit trail.
                          </p>
                          <span className="mono">SCOPED ACTION. RECORDED DECISION.</span>
                        </div>
                      </div>
                    )}
                    {tab === "audit" && <AuditList entries={audit} />}
                  </div>
                </div>
              </>
            )}
          </div>
          <div className="dashboard-bottom-bar">
            <span>
              <ShieldCheckIcon size={12} />
              Human-governed operations
            </span>
            <span className="mono">ILLUSTRATIVE DATA / INTERACTIVE DEMO</span>
          </div>
        </div>
      </div>
      {toast && (
        <div className="dashboard-toast" role="status">
          <CheckCircleIcon size={17} />
          <span>{toast}</span>
        </div>
      )}
    </div>
  );
}
