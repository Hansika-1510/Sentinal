"use client";

export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="error-page page-padding" id="main">
      <div>
        <span className="mono accent">SIGNAL INTERRUPTED</span>
        <h1>Let’s reconnect.</h1>
        <p>This view couldn’t load. You can try it again.</p>
        <button type="button" onClick={reset} className="button button-primary">
          Retry this view →
        </button>
        <a href="/" className="text-link">
          Return to Sentinel
        </a>
      </div>
    </main>
  );
}
