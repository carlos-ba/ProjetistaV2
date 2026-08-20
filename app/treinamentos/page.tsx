import type { Metadata } from "next";
import { PageFrame, Placeholder } from "../components";

const pageTitle = "Treinamentos — IceNexus";
const pageDescription = "Capacitação técnica para profissionais e empresas do setor de refrigeração.";
export const metadata: Metadata = {
  title: pageTitle,
  description: pageDescription,
  openGraph: { title: pageTitle, description: pageDescription, images: [] },
  twitter: { card: "summary", title: pageTitle, description: pageDescription, images: [] },
};

export default function Trainings() {
  return (
    <PageFrame>
      <main>
        <section className="hero training-hero">
          <div className="hero-copy"><p className="eyebrow">TREINAMENTOS ICENEXUS</p><h1>Conhecimento técnico que acompanha a prática.</h1><p className="hero-lead">Uma área ativa de capacitação para profissionais e empresas do setor de refrigeração. Os cursos, datas e modalidades serão incluídos assim que as informações forem fornecidas.</p><div className="hero-actions"><a className="button primary" href="#programacao">Ver programação</a><button className="button ghost" type="button">[Canal de inscrição]</button></div></div>
          <Placeholder label="Foto principal de treinamento IceNexus" className="hero-placeholder" />
        </section>

        <section className="section training-value"><div className="section-heading"><p className="eyebrow">DIVISÃO ATIVA</p><h2>Da atualização técnica ao desenvolvimento de equipes.</h2><p>A página poderá reunir modalidades presenciais, online, ao vivo e EAD, mas exibirá somente ofertas realmente disponíveis.</p></div><div className="training-points"><article><span>01</span><h3>Aplicação prática</h3><p>[Resultados e metodologia a confirmar]</p></article><article><span>02</span><h3>Experiência profissional</h3><p>[Qualificações públicas dos instrutores a confirmar]</p></article><article><span>03</span><h3>Formatos flexíveis</h3><p>[Modalidades atualmente disponíveis a confirmar]</p></article></div></section>

        <section className="section schedule-section" id="programacao"><div className="section-heading split-heading"><div><p className="eyebrow">PROGRAMAÇÃO</p><h2>Próximos treinamentos.</h2></div><p>Os cartões abaixo são espaços estruturais do protótipo e não representam cursos anunciados.</p></div><div className="training-grid">{[1,2,3].map(item => <article className="training-card" key={item}><Placeholder label={`Imagem do treinamento ${item}`} /><div className="training-card-body"><span>Modalidade a definir</span><h3>[Nome do treinamento]</h3><p>[Público, objetivo e breve descrição]</p><dl><div><dt>Data</dt><dd>A fornecer</dd></div><div><dt>Carga horária</dt><dd>A fornecer</dd></div></dl><button className="text-link" type="button">[Inscrição a configurar] →</button></div></article>)}</div></section>

        <section className="section enterprise-cta"><div><p className="eyebrow">TREINAMENTO PARA EMPRESAS</p><h2>Sua equipe precisa de uma capacitação específica?</h2><p>Este espaço poderá receber a oferta corporativa quando temas, formatos e condições forem confirmados.</p></div><button className="button primary" type="button">[Solicitar atendimento]</button></section>
      </main>
    </PageFrame>
  );
}
