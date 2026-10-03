import { Brand } from "./ui";

export function Footer() {
  return (
    <footer className="site-footer page-padding">
      <div className="footer-top">
        <div>
          <Brand />
          <p className="mono footer-descriptor">AI SOFTWARE INCIDENT RESPONSE</p>
        </div>
        <nav aria-label="Footer navigation">
          <a href="/#platform">Platform</a>
          <a href="/#agents">Agents</a>
          <a href="/architecture">Architecture</a>
          <a href="/#security">Security</a>
          <a href="/docs">Documentation</a>
          <a href="/docs#github">GitHub</a>
        </nav>
      </div>
      <div className="footer-bottom">
        <span className="mono">DETECT · INVESTIGATE · RESOLVE · LEARN</span>
        <span>© {new Date().getFullYear()} Sentinel</span>
        <a href="#main" className="back-top">
          Back to top ↑
        </a>
      </div>
    </footer>
  );
}
