import type { Metadata } from "next";
import { PageFrame } from "../components";

export const metadata: Metadata = {
  title: "Acessar — IceNexus",
  description: "Acesso aos ambientes disponíveis do ecossistema IceNexus.",
  robots: { index: false, follow: false },
  openGraph: { title: "Acessar — IceNexus", description: "Acesso aos ambientes disponíveis do ecossistema IceNexus.", images: [] },
  twitter: { card: "summary", title: "Acessar — IceNexus", description: "Acesso aos ambientes disponíveis do ecossistema IceNexus.", images: [] },
};

export default function AccessPage() {
  return (
    <PageFrame>
      <main className="section access-page">
        <section className="checkout-card">
          <p className="eyebrow">ÁREA DO CLIENTE</p>
          <h1>Acesse seus produtos IceNexus.</h1>
          <p>O Projeto de Câmara Fria já está disponível em seu ambiente próprio. Novos produtos serão adicionados aqui conforme forem lançados.</p>
          <div className="review-box">
            <strong>Projeto de Câmara Fria</strong>
            <p>Entre para criar, continuar e consultar seus projetos.</p>
          </div>
          <a className="button primary full" href="https://camara-fria.icenexus.com.br">Acessar o Projeto de Câmara Fria</a>
          <a className="text-link centered" href="/projeto-camara-fria">Conhecer planos e recursos</a>
        </section>
      </main>
    </PageFrame>
  );
}
