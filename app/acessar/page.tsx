import type { Metadata } from "next";
import { PageFrame } from "../components";
import { AccessSimulator } from "../access-simulator";

export const metadata: Metadata = {
  title: "Acessar — IceNexus",
  description: "Entrada simulada para os ambientes IceNexus.",
  robots: { index: false, follow: false },
  openGraph: { title: "Acessar — IceNexus", description: "Entrada simulada para os ambientes IceNexus.", images: [] },
  twitter: { card: "summary", title: "Acessar — IceNexus", description: "Entrada simulada para os ambientes IceNexus.", images: [] },
};

export default function AccessPage() {
  return <PageFrame><main className="section access-page"><AccessSimulator /></main></PageFrame>;
}
