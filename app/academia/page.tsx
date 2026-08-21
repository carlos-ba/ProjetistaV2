import type { Metadata } from "next";
import { PageFrame } from "../components";

const pageTitle = "Academia IceNexus";
const pageDescription = "Capacitação técnica para profissionais e empresas do setor de refrigeração.";

export const metadata: Metadata = {
  title: pageTitle,
  description: pageDescription,
  openGraph: { title: pageTitle, description: pageDescription, images: [] },
  twitter: { card: "summary", title: pageTitle, description: pageDescription, images: [] },
};

export default function Academy() {
  return (
    <PageFrame>
      <main>
        <section className="hero training-hero">
          <div className="hero-copy">
            <p className="eyebrow">ACADEMIA ICENEXUS</p>
            <h1>Conhecimento técnico conectado à prática da refrigeração.</h1>
            <p className="hero-lead">A divisão de educação da IceNexus para capacitação e atualização de profissionais e empresas do setor.</p>
            <div className="hero-actions"><a className="button primary" href="mailto:financeiro@icenexus.com.br?subject=Informações%20sobre%20a%20Academia%20IceNexus">Solicitar informações</a><a className="button ghost" href="/">Conhecer o ecossistema</a></div>
          </div>
          <div className="product-window" aria-label="Áreas de capacitação da Academia IceNexus">
            <div className="window-bar"><i /><i /><i /><span>Academia IceNexus</span></div>
            <div className="window-body"><aside><span className="done">1</span><span className="done">2</span><span>3</span></aside><div className="window-content"><small>CAPACITAÇÃO CONTÍNUA</small><h3>Técnica, aplicação e desenvolvimento</h3><div className="choice-row"><b>Formação profissional</b><span>IceNexus</span></div><div className="choice-row"><b>Treinamentos para empresas</b><span>Sob consulta</span></div><div className="insight">A programação será publicada conforme cada oferta for confirmada.</div></div></div>
          </div>
        </section>

        <section className="section training-value">
          <div className="section-heading"><p className="eyebrow">DIVISÃO ATIVA</p><h2>Da atualização técnica ao desenvolvimento de equipes.</h2><p>A Academia foi criada para aproximar conhecimento, aplicação profissional e evolução do setor de refrigeração.</p></div>
          <div className="training-points"><article><span>01</span><h3>Capacitação técnica</h3><p>Conteúdos orientados aos desafios encontrados por profissionais da refrigeração.</p></article><article><span>02</span><h3>Desenvolvimento de equipes</h3><p>Treinamentos que podem atender necessidades específicas de empresas.</p></article><article><span>03</span><h3>Formatos conectados</h3><p>Possibilidades presenciais, online, ao vivo e EAD conforme a oferta publicada.</p></article></div>
        </section>

        <section className="section enterprise-cta"><div><p className="eyebrow">PROGRAMAÇÃO EM PREPARAÇÃO</p><h2>Novos treinamentos serão apresentados aqui.</h2><p>Enquanto a programação pública é organizada, profissionais e empresas podem solicitar informações diretamente à IceNexus.</p></div><a className="button primary" href="mailto:financeiro@icenexus.com.br?subject=Interesse%20em%20treinamentos%20IceNexus">Falar com a Academia</a></section>
      </main>
    </PageFrame>
  );
}
