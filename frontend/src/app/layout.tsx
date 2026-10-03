import type { Metadata, Viewport } from "next";
import { Geist, JetBrains_Mono } from "next/font/google";
import { SiteProvider } from "@/components/site-provider";
import "./globals.css";
import "./experience.css";
import "./console.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist", display: "swap" });
const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: { default: "SENTINEL | From incident to root cause", template: "%s | SENTINEL" },
  description:
    "Production breaks. We trace why. Sentinel connects runtime failures to deployments, code, and the evidence behind them. AI investigates. Humans decide.",
  applicationName: "Sentinel",
  openGraph: {
    title: "SENTINEL | Production breaks. We trace why.",
    description:
      "From the first 500 to the exact line of code. AI software incident response, with humans in control.",
    type: "website",
  },
  twitter: { card: "summary_large_image" },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = { themeColor: "#5c7285", colorScheme: "dark" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${geist.variable} ${mono.variable}`}>
      <body>
        <SiteProvider>{children}</SiteProvider>
      </body>
    </html>
  );
}
