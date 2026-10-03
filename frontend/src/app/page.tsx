import { Navigation } from "@/components/navigation";
import { Hero } from "@/components/hero";
import { ProblemStory } from "@/components/problem";
import { SystemJourney } from "@/components/system-journey";
import { RuntimeDemo } from "@/components/runtime-demo";
import { Observer } from "@/components/observer";
import { Footer } from "@/components/footer";
import { Investigation, EvidenceChain } from "@/components/investigation";
import { FixAdvisor, CodeReview } from "@/components/fix-and-review";
import { Recovery, IncidentMemory } from "@/components/recovery-memory";
import { HumanControl } from "@/components/approval";
import { AgentSystem } from "@/components/agents";
import { FullLoop, Security, FinalCTA } from "@/components/closing";
import { ProductPreview } from "@/components/product-preview";

export default function Home() {
  return (
    <>
      <Navigation />
      <main id="main">
        <Hero />
        <ProblemStory />
        <SystemJourney />
        <RuntimeDemo />
        <Observer />
        <Investigation />
        <EvidenceChain />
        <FixAdvisor />
        <CodeReview />
        <Recovery />
        <IncidentMemory />
        <HumanControl />
        <AgentSystem />
        <FullLoop />
        <ProductPreview />
        <Security />
        <FinalCTA />
      </main>
      <Footer />
    </>
  );
}
