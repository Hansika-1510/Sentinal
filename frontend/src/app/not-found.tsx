import { ArrowRightIcon } from "@phosphor-icons/react/dist/ssr";
import { Brand } from "@/components/ui";

export default function NotFound() {
  return (
    <main className="error-page page-padding" id="main">
      <Brand />
      <div>
        <span className="mono accent">404 / TRACE ENDS HERE</span>
        <h1>
          This signal
          <br />
          leads nowhere.
        </h1>
        <p>The page you’re looking for isn’t part of this system.</p>
        <a href="/" className="button button-primary">
          Back to Sentinel
          <ArrowRightIcon size={18} />
        </a>
      </div>
    </main>
  );
}
