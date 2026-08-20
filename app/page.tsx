import Link from "next/link";
import { PageFrame, Placeholder } from "./components";

export default function Home() {
  return (
    <PageFrame>
      <main>
        <section className="hero hub-hero">
          <div className="hero-copy">
            <p className="eyebrow">TECNOLOGIA • ENGENHARIA • CONHECIMENTO</p>
            <h1>Um ecossistema para transformar a refrigeração.</h1>
            <p className="hero-lead">Ferramentas técnicas e capacitação conectadas para tornar decisões complexas mais simples, rápidas e acessíveis.</p>
            <div className="hero-actions">
              <Link className="button primary" href="/projeto-camara-fria">Conhecer o primeiro produto</Link>
              <Link className="button ghost" href="/acessar">Já sou cliente</Link>
            </div>
          </div>
          <div className="nexus-visual" aria-label="Áreas conectadas do ecossistema IceNexus">
            <div className="core"><span>ICE</span><strong>NEXUS</strong></div>
            <div className="orbit orbit-one">Projetos</div>
            <div className="orbit orbit-two">Treinamentos</div>
            <div className="orbit orbit-three">Engenharia</div>
            <div className="orbit orbit-four">Conhecimento</div>
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
              <div className="mini-product-ui" aria-hidden="true"><div className="mini-rail"><i /><i /><i /><i /></div><div className="mini-stage"><b>Projeto guiado</b><span /><span /><span /></div></div>
              <h3>Projeto de Câmara Fria</h3>
              <p>Uma jornada guiada para calcular, selecionar componentes e gerar os documentos técnicos do projeto.</p>
              <Link className="text-link" href="/projeto-camara-fria">Explorar a ferramenta <span>→</span></Link>
            </article>
            <article className="solution-card">
              <div className="card-top"><span className="live-badge green">Área ativa</span><span>Capacitação</span></div>
              <Placeholder label="Treinamentos IceNexus" className="card-placeholder" />
              <h3>Treinamentos</h3>
              <p>Capacitação técnica para profissionais e empresas acompanharem a evolução da refrigeração.</p>
              <Link className="text-link" href="/treinamentos">Conhecer treinamentos <span>→</span></Link>
            </article>
          </div>
        </section>

        <section className="section vision-section">
          <div className="section-heading"><p className="eyebrow">VISÃO DO ECOSSISTEMA</p><h2>Uma base preparada para novas possibilidades.</h2><p>Estas frentes fazem parte da visão IceNexus e serão apresentadas publicamente conforme disponibilidade e condições de atendimento forem confirmadas.</p></div>
          <div className="vision-grid">
            {[
              ["Engenharia especializada", "Projetos, validação e acompanhamento de execução."],
              ["Manutenção e ativos", "Diagnóstico, estruturação e modalidades de apoio à operação."],
              ["Biblioteca técnica", "Conteúdos organizados e atualizados para o setor."],
              ["Inovação", "Tendências e aprendizados de mercados e eventos."],
            ].map(([title, text]) => <article key={title}><span>Em estruturação</span><h3>{title}</h3><p>{text}</p></article>)}
          </div>
        </section>

        <section className="section final-cta">
          <p className="eyebrow">PRIMEIRA FERRAMENTA</p>
          <h2>Seu próximo projeto de câmara fria pode começar aqui.</h2>
          <div><Link className="button primary" href="/projeto-camara-fria">Ver como funciona</Link><Link className="button ghost" href="/acessar">Acessar ambiente</Link></div>
        </section>
      </main>
    </PageFrame>
  );
}
