import { PageFrame } from "./components";

export default function Home() {
  return (
    <PageFrame>
      <main>
        <section className="hero hub-hero">
          <div className="hero-copy">
            <p className="eyebrow">TECNOLOGIA • ENGENHARIA • CONHECIMENTO</p>
            <h1>Um ecossistema para transformar a refrigeração.</h1>
            <p className="brand-signature">IceNexus. A inteligência por trás da refrigeração.</p>
            <p className="hero-lead">Ferramentas técnicas e capacitação conectadas para tornar decisões complexas mais simples, rápidas e acessíveis.</p>
            <div className="hero-actions">
              <a className="button primary" href="/projeto-camara-fria">Conhecer o primeiro produto</a>
              <a className="button ghost" href="/acessar">Já sou cliente</a>
            </div>
          </div>
          <div className="nexus-visual" aria-label="Áreas conectadas do ecossistema IceNexus">
            <div className="core"><img src="/logo-icenexus.png" alt="IceNexus" /></div>
            <div className="orbit orbit-one"><span>Ferramentas técnicas</span><small>Disponível</small></div>
            <div className="orbit orbit-two"><span>Academia IceNexus</span><small>Área ativa</small></div>
            <div className="orbit orbit-three future"><span>IceNexus Mastergroup</span><small>Em desenvolvimento</small></div>
            <div className="orbit orbit-four future"><span>Engenharia especializada</span><small>Em desenvolvimento</small></div>
            <div className="orbit orbit-five future"><span>Gestão de manutenção</span><small>Em desenvolvimento</small></div>
            <div className="orbit orbit-six future"><span>Conteúdo e inovação</span><small>Em desenvolvimento</small></div>
            <p className="nexus-caption">Áreas ativas e novas frentes conectadas em um ecossistema em evolução.</p>
          </div>
        </section>

        <section className="section solutions-section">
          <div className="section-heading split-heading">
            <div><p className="eyebrow">CONEXÕES ATIVAS</p><h2>Comece pelo que você precisa hoje.</h2></div>
            <p>A IceNexus cresce por áreas independentes, conectadas por uma mesma visão para o setor de refrigeração.</p>
          </div>
          <div className="solution-grid">
            <article className="solution-card featured-solution">
              <div className="card-top"><span className="live-badge">Disponível</span><span>Ferramenta técnica</span></div>
              <img className="solution-preview" src="/media/projeto-calculo.webp" alt="Resultado do cálculo de carga térmica dentro do Projeto de Câmara Fria" loading="lazy" />
              <h3>Projeto de Câmara Fria</h3>
              <p>Uma jornada guiada para calcular, selecionar componentes e gerar os documentos técnicos do projeto.</p>
              <a className="text-link" href="/projeto-camara-fria">Explorar a ferramenta <span>→</span></a>
            </article>
            <article className="solution-card">
              <div className="card-top"><span className="live-badge green">Área ativa</span><span>Capacitação</span></div>
              <div className="mini-product-ui" aria-hidden="true"><div className="mini-rail"><i /><i /><i /><i /></div><div className="mini-stage"><b>Formação conectada</b><span /><span /><span /></div></div>
              <h3>Academia IceNexus</h3>
              <p>Capacitação técnica para profissionais e empresas acompanharem a evolução da refrigeração.</p>
              <a className="text-link" href="/academia">Conhecer a Academia <span>→</span></a>
            </article>
          </div>
        </section>

        <section className="section vision-section">
          <div className="section-heading"><p className="eyebrow">VISÃO DO ECOSSISTEMA</p><h2>Uma base preparada para novas possibilidades.</h2><p>Estas frentes fazem parte da visão IceNexus e serão apresentadas publicamente conforme disponibilidade e condições de atendimento forem confirmadas.</p></div>
          <div className="vision-grid">
            {[
              ["Engenharia especializada", "Projetos, validação e acompanhamento de execução."],
              ["Gestão de manutenção", "Diagnóstico, planejamento, capacitação e apoio à operação de ativos de refrigeração."],
              ["IceNexus Mastergroup", "Programa anual avançado de desenvolvimento técnico e gerencial para profissionais da refrigeração."],
              ["Conteúdo e inovação", "Webinars, podcasts, biblioteca técnica e tendências para o aprimoramento do setor."],
            ].map(([title, text]) => <article key={title}><span>Em estruturação</span><h3>{title}</h3><p>{text}</p></article>)}
          </div>
        </section>

        <section className="section final-cta">
          <p className="eyebrow">PRIMEIRA FERRAMENTA</p>
          <h2>Seu próximo projeto de câmara fria pode começar aqui.</h2>
          <div><a className="button primary" href="/projeto-camara-fria">Ver como funciona</a><a className="button ghost" href="/acessar">Acessar ambiente</a></div>
        </section>
      </main>
    </PageFrame>
  );
}
