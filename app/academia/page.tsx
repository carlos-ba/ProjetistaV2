import type { Metadata } from "next";
import { PageFrame } from "../components";

const pageTitle = "Academia IceNexus";
const pageDescription = "Capacitação técnica com aulas e atividades práticas para profissionais e empresas do setor de refrigeração.";

export const metadata: Metadata = {
  title: pageTitle,
  description: pageDescription,
  openGraph: { title: pageTitle, description: pageDescription, images: ["/media/academia-demo-poster.webp"] },
  twitter: { card: "summary_large_image", title: pageTitle, description: pageDescription, images: ["/media/academia-demo-poster.webp"] },
};

export default function Academy() {
  return (
    <PageFrame>
      <main>
        <section className="hero training-hero">
          <div className="hero-copy">
            <p className="eyebrow">ACADEMIA ICENEXUS</p>
            <h1>Conhecimento técnico conectado à prática da refrigeração.</h1>
            <p className="hero-lead">A divisão de educação da IceNexus aproxima fundamentos técnicos, aplicação em laboratório e troca entre profissionais do setor.</p>
            <div className="hero-actions">
              <a className="button primary" href="mailto:financeiro@icenexus.com.br?subject=Informações%20sobre%20a%20Academia%20IceNexus">Solicitar informações</a>
              <a className="button ghost" href="#academia-em-acao">Ver a Academia em ação</a>
            </div>
          </div>
          <figure className="academy-hero-image">
            <img src="/media/academia-aula-teorica.webp" alt="Instrutor conduzindo uma aula técnica de refrigeração para uma turma" />
            <figcaption><strong>Teoria que prepara para a prática</strong><span>Registro real de uma atividade de capacitação.</span></figcaption>
          </figure>
        </section>

        <section className="section academy-showcase" id="academia-em-acao">
          <div className="academy-showcase-copy">
            <p className="eyebrow">ACADEMIA EM AÇÃO</p>
            <h2>Um ambiente preparado para aprender, testar e aplicar.</h2>
            <p>As imagens apresentam atividades já realizadas no centro técnico: aulas orientadas, exercícios em grupo e contato direto com componentes e sistemas de refrigeração.</p>
            <ul className="academy-proof-list">
              <li>Aulas técnicas com apoio visual e demonstrações</li>
              <li>Atividades práticas acompanhadas por instrutores</li>
              <li>Laboratório com equipamentos e componentes reais</li>
            </ul>
          </div>
          <figure className="academy-video">
            <video controls muted playsInline preload="metadata" poster="/media/academia-demo-poster.webp" aria-label="Clipe com registros de aulas e atividades práticas da Academia IceNexus">
              <source src="/media/academia-em-acao-21s.mp4" type="video/mp4" />
              Seu navegador não oferece suporte à reprodução deste vídeo.
            </video>
            <figcaption>21 segundos · sem áudio · registros de atividades reais</figcaption>
          </figure>
        </section>

        <section className="section academy-gallery-section">
          <div className="section-heading">
            <p className="eyebrow">APRENDIZAGEM APLICADA</p>
            <h2>Do entendimento técnico à execução acompanhada.</h2>
            <p>Diferentes momentos da formação mostram como conteúdo, experimentação e orientação profissional se complementam.</p>
          </div>
          <div className="academy-gallery">
            <figure className="academy-gallery-card academy-gallery-wide">
              <img src="/media/academia-pratica-eletrica.webp" alt="Instrutor orientando um grupo durante uma atividade prática com componentes elétricos" />
              <figcaption><strong>Orientação próxima</strong><span>Discussão técnica e resolução de dúvidas durante a atividade.</span></figcaption>
            </figure>
            <figure className="academy-gallery-card">
              <img src="/media/academia-pratica-refrigeracao.webp" alt="Turma acompanhando uma demonstração prática com componentes de refrigeração" />
              <figcaption><strong>Contato com componentes reais</strong><span>Aprendizado apoiado por demonstrações e exercícios práticos.</span></figcaption>
            </figure>
            <figure className="academy-gallery-card">
              <img src="/media/academia-montagem-painel.webp" alt="Profissionais acompanhando a montagem prática de um painel para câmara fria" />
              <figcaption><strong>Prática acompanhada</strong><span>Execução orientada dentro de um ambiente técnico preparado.</span></figcaption>
            </figure>
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
