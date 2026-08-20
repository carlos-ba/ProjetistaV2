import type { Metadata } from "next";
import { PageFrame } from "../../components";
import { PlanSimulator } from "../../plan-simulator";

export const metadata: Metadata = {
  title: "Simular contratação — IceNexus",
  description: "Simulação sem cadastro ou cobrança da jornada de contratação do Projeto de Câmara Fria.",
  robots: { index: false, follow: false },
  openGraph: { title: "Simular contratação — IceNexus", description: "Simulação da jornada de contratação.", images: [] },
  twitter: { card: "summary", title: "Simular contratação — IceNexus", description: "Simulação da jornada de contratação.", images: [] },
};

export default async function ContractSimulation({ params }: { params: Promise<{ plan: string }> }) {
  const { plan } = await params;
  return <PageFrame><main className="section checkout-page"><PlanSimulator initialPlan={plan} /></main></PageFrame>;
}
