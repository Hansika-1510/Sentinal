import type { Metadata } from "next";
import Dashboard from "@/components/dashboard";

export const metadata: Metadata = {
  title: "Interactive Console",
  description:
    "Explore an example incident from runtime failure to root cause, human approval, and verified recovery.",
};

export default function ConsolePage() {
  return (
    <main id="main" className="console-page">
      <Dashboard standalone />
    </main>
  );
}
