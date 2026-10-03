import type { Metadata } from "next";
import {
  ArrowRightIcon,
  EyeIcon,
  GitCommitIcon,
  HandPalmIcon,
  ShieldCheckIcon,
} from "@phosphor-icons/react/dist/ssr";
import { Navigation } from "@/components/navigation";
import { SystemJourney } from "@/components/system-journey";
import { Footer } from "@/components/footer";
import "../reference-pages.css";

export const metadata: Metadata = {
  title: "Architecture",
  description:
    "Explore Sentinel's human-governed incident response architecture, from source code to verified recovery.",
};

export default function ArchitecturePage() {
  return (
    <>
      <Navigation />
      <main id="main" className="architecture-page">
        <header className="reference-hero page-padding">
          <span className="eyebrow mono">REFERENCE ARCHITECTURE</span>
          <h1>
            Every connection.
            <br />
            <span>Nothing hidden.</span>
          </h1>
          <p>
            Trace the full lifecycle. Select any node to inspect its context, responsibility, and
            owner.
          </p>
        </header>
        <SystemJourney standalone />
        <section className="architecture-boundaries section page-padding">
          <h2>
            Intelligence and authority
            <br />
            <span>have clear boundaries.</span>
          </h2>
          <div className="boundary-grid">
            <article>
              <EyeIcon size={30} weight="light" />
              <h3>Read the evidence.</h3>
              <p>
                Sentinel and Investigator observe runtime signals, correlate deployments, and
                inspect code context using scoped access.
              </p>
              <span className="mono">SENTINEL + INVESTIGATOR</span>
            </article>
            <article>
              <GitCommitIcon size={30} weight="light" />
              <h3>Keep the developer in control.</h3>
              <p>
                Fix Advisor recommends. The developer changes the code, tests it, and commits it.
                CodeGuard and Robin Review verify the change.
              </p>
              <span className="mono">DEVELOPER + CODEGUARD + ROBIN</span>
            </article>
            <article>
              <HandPalmIcon size={30} weight="light" />
              <h3>Ask before acting.</h3>
              <p>
                Response presents sensitive actions with their scope, risk, expected impact, and
                rollback path. A human makes the decision.
              </p>
              <span className="mono">RESPONSE + HUMAN APPROVER</span>
            </article>
            <article>
              <ShieldCheckIcon size={30} weight="light" />
              <h3>Verify the recovery.</h3>
              <p>
                After a reviewed deployment or approved operational action, Sentinel validates
                runtime health and preserves the outcome in Memory.
              </p>
              <span className="mono">SENTINEL + MEMORY</span>
            </article>
          </div>
          <a href="/console" className="button button-primary">
            See the system in action
            <ArrowRightIcon size={18} />
          </a>
        </section>
      </main>
      <Footer />
    </>
  );
}
