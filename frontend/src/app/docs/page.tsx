import type { Metadata } from "next";
import {
  ArrowRightIcon,
  ArrowUpRightIcon,
  CheckIcon,
  GitBranchIcon,
  ShieldCheckIcon,
} from "@phosphor-icons/react/dist/ssr";
import { Navigation } from "@/components/navigation";
import { Footer } from "@/components/footer";
import { CopyButton, TextLink } from "@/components/ui";
import { agents } from "@/lib/data";
import "../reference-pages.css";

export const metadata: Metadata = {
  title: "Documentation",
  description:
    "The Sentinel operating model: evidence, developer ownership, scoped operations, and verified recovery.",
};
const eventExample =
  '{\n  "service": "payment-service",\n  "environment": "production",\n  "deployment": "v1.8.3",\n  "commit": "8f03c2a",\n  "signal": "http_error_rate",\n  "observed_at": "2026-10-03T10:43:00Z"\n}';

export default function DocsPage() {
  return (
    <>
      <Navigation />
      <main id="main" className="docs-page page-padding">
        <header className="reference-hero">
          <span className="eyebrow mono">DOCUMENTATION</span>
          <h1>
            Understand
            <br />
            <span>the whole system.</span>
          </h1>
          <p>
            The operating model behind Sentinel.
            <br />
            Evidence, human authority, and a complete incident lifecycle.
          </p>
        </header>
        <div className="docs-layout">
          <aside className="docs-sidebar">
            <span className="mono">IN THIS GUIDE</span>
            <nav aria-label="Documentation sections">
              <a href="#overview">Overview</a>
              <a href="#workflow">The full workflow</a>
              <a href="#github">GitHub & deployments</a>
              <a href="#agents">The agent system</a>
              <a href="#review">Developer ownership</a>
              <a href="#approval">Operational approval</a>
              <a href="#security">Security model</a>
              <a href="#demo">Try the demo</a>
            </nav>
            <a href="/architecture" className="docs-architecture-link">
              View architecture
              <ArrowUpRightIcon size={16} />
            </a>
          </aside>
          <div className="docs-content">
            <section id="overview">
              <h2>One incident. All its context.</h2>
              <p>
                Sentinel connects a runtime failure to the deployment, commit, and code that may
                explain it. The Investigator assembles evidence into a probable root cause. Fix
                Advisor gives the developer precise guidance, and Sentinel verifies the outcome
                after a reviewed change or approved operational response.
              </p>
              <div className="docs-callout">
                <ShieldCheckIcon size={22} />
                <div>
                  <strong>Sentinel does not autonomously modify application source code.</strong>
                  <p>
                    Developers write, test, and commit fixes. CodeGuard and Robin Review validate
                    their changes.
                  </p>
                </div>
              </div>
            </section>
            <section id="workflow">
              <h2>From code to recovery.</h2>
              <ol className="docs-workflow">
                <li>
                  <strong>Build & ship</strong>
                  <span>Developer code → CodeGuard → Git / CI → deployment</span>
                </li>
                <li>
                  <strong>Detect & investigate</strong>
                  <span>Runtime signals → Sentinel → incident → Investigator</span>
                </li>
                <li>
                  <strong>Understand & fix</strong>
                  <span>Evidence → probable root cause → Fix Advisor → developer</span>
                </li>
                <li>
                  <strong>Verify & learn</strong>
                  <span>
                    CodeGuard + Robin Review → CI/CD → deployment → verified recovery → Memory
                  </span>
                </li>
              </ol>
              <TextLink href="/architecture">Explore every connection</TextLink>
            </section>
            <section id="github">
              <h2>Connect the release to the runtime.</h2>
              <p>
                Source context starts with a stable commit identifier. Deployment metadata carries
                that identifier into production, alongside a service name, environment, release
                version, and timestamp. Runtime signals use the same service identity.
              </p>
              <div className="docs-code">
                <div>
                  <span className="mono">ILLUSTRATIVE EVENT CONTEXT</span>
                  <CopyButton value={eventExample} label="Copy example" />
                </div>
                <pre>
                  <code>{eventExample}</code>
                </pre>
              </div>
              <h3>GitHub access</h3>
              <p>
                Scope a GitHub App installation to the repositories involved in your services. Grant
                the minimum permissions needed to read commits and diffs or publish review checks.
                Reading evidence does not require source-code write access.
              </p>
              <a
                href="https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app"
                target="_blank"
                rel="noopener noreferrer"
                className="text-link"
              >
                GitHub App permission guidance
                <ArrowUpRightIcon size={17} />
              </a>
              <h3>Deployment context</h3>
              <p>
                Keep deployment identifiers immutable. Include the previous release and the actor or
                pipeline that performed the deployment. This creates a reliable bridge between an
                error spike and a specific change.
              </p>
            </section>
            <section id="agents">
              <h2>Specialized agents. Shared evidence.</h2>
              <div className="docs-agent-list">
                {agents.map((agent) => (
                  <article id={agent.id} key={agent.id}>
                    <h3>{agent.name}</h3>
                    <p>{agent.description}</p>
                    <dl>
                      <div>
                        <dt>Reads</dt>
                        <dd>{agent.input}</dd>
                      </div>
                      <div>
                        <dt>Produces</dt>
                        <dd>{agent.output}</dd>
                      </div>
                      <div>
                        <dt>Boundary</dt>
                        <dd>{agent.boundary}</dd>
                      </div>
                    </dl>
                  </article>
                ))}
              </div>
            </section>
            <section id="review">
              <h2>The developer owns the fix.</h2>
              <p>
                Fix Advisor identifies the affected area, explains the failure mechanism, and
                recommends a change. The developer reviews that guidance, modifies the source, adds
                appropriate tests, and creates the commit.
              </p>
              <div className="docs-review-flow">
                <span>
                  <GitBranchIcon size={19} />
                  Developer commit
                </span>
                <ArrowRightIcon size={18} />
                <span>
                  <ShieldCheckIcon size={19} />
                  CodeGuard + Robin
                </span>
                <ArrowRightIcon size={18} />
                <span>
                  <CheckIcon size={19} />
                  Your CI/CD
                </span>
              </div>
              <p>
                CodeGuard applies deterministic security and quality checks. Robin Review evaluates
                the developer’s change in context. Neither a root-cause confidence score nor an AI
                recommendation substitutes for review and testing.
              </p>
            </section>
            <section id="approval">
              <h2>Sensitive actions need a human.</h2>
              <p>
                An operational recommendation must describe the exact target, expected impact, risk,
                and rollback path. The approver sees that context before deciding. Rejections and
                approvals are both retained with the actor, timestamp, and reason.
              </p>
              <p>
                A rollback may help restore service while a developer prepares a permanent
                source-code fix. After an approved action, Sentinel checks the runtime against the
                baseline instead of assuming that execution means recovery.
              </p>
              <TextLink href="/#human-control">Explore the approval example</TextLink>
            </section>
            <section id="security">
              <h2>Authority is explicit.</h2>
              <div className="docs-security-grid">
                <article>
                  <h3>Least privilege</h3>
                  <p>
                    Separate read access for investigation from the narrowly scoped authority to
                    perform an approved operational action.
                  </p>
                </article>
                <article>
                  <h3>Secret redaction</h3>
                  <p>
                    Remove secrets from collected telemetry and source context before they enter the
                    investigation or incident memory.
                  </p>
                </article>
                <article>
                  <h3>Evidence provenance</h3>
                  <p>
                    Preserve where a finding came from. Confidence, timestamps, and source
                    references stay available for inspection.
                  </p>
                </article>
                <article>
                  <h3>Auditable decisions</h3>
                  <p>
                    Record the recommendation, approver, reason, scope, execution result, and
                    subsequent recovery checks.
                  </p>
                </article>
              </div>
            </section>
            <section id="demo">
              <h2>Follow an incident yourself.</h2>
              <p>
                The interactive console uses illustrative telemetry. Search incident memory, inspect
                evidence, read developer guidance, approve or reject the sample rollback, and verify
                the recovery. The demo does not connect to production or modify source code.
              </p>
              <a href="/console" className="button button-primary">
                Open the interactive console
                <ArrowRightIcon size={17} />
              </a>
            </section>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
