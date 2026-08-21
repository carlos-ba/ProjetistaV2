import type { Metadata } from "next";
import { PageFrame } from "../components";

const pageTitle = "Projeto de Câmara Fria — IceNexus";
const pageDescription = "Jornada guiada para calcular, selecionar componentes e preparar os documentos técnicos de uma câmara fria.";
export const metadata: Metadata = {
  title: pageTitle,
  description: pageDescription,
  openGraph: { title: pageTitle, description: pageDescription, images: [] },
  twitter: { card: "summary", title: pageTitle, description: pageDescription, images: [] },
};

const deliverables = [
  ["01", "Memorial de cálculo", "Premissas e resultados técnicos organizados."],
  ["02", "Seleção de componentes", "Equipamentos e materiais conduzidos pela jornada."],
  ["03", "Layout e exportação", "Desenho do projeto com possibilidade de uso em CAD."],
  ["04", "Lista para cotação", "Peças e materiais organizados para solicitar preços."],
  ["05", "Formação do orçamento", "Combinação de preços, materiais e custo de montagem."],
];

export default function ColdRoomProject() {
  return (
    <PageFrame>
      <main>
        <section className="hero product-hero">
          <div className="hero-copy">
            <p className="eyebrow">PROJETO DE CÂMARA FRIA</p>
            <h1>Do primeiro dado ao projeto técnico, passo a passo.</h1>
            <p className="hero-lead">Uma jornada guiada por cards que ajuda técnicos e empresas a calcular, selecionar componentes e preparar os documentos de uma câmara fria.</p>
            <div className="hero-actions"><a className="button primary" href="#planos">Ver planos</a><a className="button ghost" href="/acessar">Já sou assinante</a></div>
            <p className="micro-proof">Jornada simples demonstrada em condições controladas. O tempo varia conforme dados, projeto e perfil de uso.</p>
          </div>
          <div className="product-window" aria-label="Representação da jornada guiada do programa">
            <div className="window-bar"><i /><i /><i /><span>Projeto de Câmara Fria</span></div>
            <div className="window-body"><aside>{[1,2,3,4,5,6].map(n => <span className={n < 4 ? "done" : ""} key={n}>{n}</span>)}</aside><div className="window-content"><small>ETAPA 03 DE 06</small><h3>Seleção de equipamentos</h3><div className="choice-row"><b>Opção recomendada</b><span>Selecionada ✓</span></div><div className="choice-row"><b>Alternativa técnica</b><span>Comparar</span></div><div className="insight">Informações técnicas acompanham cada decisão.</div></div></div>
          </div>
        </section>

        <section className="proof-band"><div><strong>Jornada guiada</strong><span>Etapas validadas em sequência</span></div><div><strong>Projeto completo</strong><span>Do cálculo à lista de materiais</span></div><div><strong>Para diferentes operações</strong><span>Técnicos, montadoras e revendas</span></div></section>

        <section className="section journey-section">
          <div className="section-heading"><p className="eyebrow">COMO FUNCIONA</p><h2>Complexidade técnica organizada em decisões simples.</h2><p>Você avança por uma sequência visual. Cada etapa reúne as informações necessárias antes de liberar a próxima decisão.</p></div>
          <ol className="journey-steps">
            <li><span>1</span><div><h3>Informe a necessidade</h3><p>Dimensões, temperatura, produto, movimentação e características da instalação.</p></div></li>
            <li><span>2</span><div><h3>Acompanhe o cálculo</h3><p>A carga térmica e os dados técnicos são organizados ao longo da jornada.</p></div></li>
            <li><span>3</span><div><h3>Compare e selecione</h3><p>Escolha equipamentos, tubulações, isolamento e componentes necessários.</p></div></li>
            <li><span>4</span><div><h3>Gere os documentos</h3><p>Receba os materiais técnicos que apoiam cotação e preparação do orçamento.</p></div></li>
          </ol>
        </section>

        <section className="section deliverables-section">
          <div className="section-heading"><p className="eyebrow">ENTREGÁVEIS</p><h2>O projeto não termina em uma tela.</h2></div>
          <div className="deliverables-list">{deliverables.map(([num,title,text]) => <article key={num}><span>{num}</span><div><h3>{title}</h3><p>{text}</p></div></article>)}</div>
        </section>

        <section className="section audience-section">
          <div className="section-heading"><p className="eyebrow">PARA QUEM É</p><h2>Uma base técnica, jornadas comerciais diferentes.</h2></div>
          <div className="audience-grid">
            <article><span>Compra online</span><h3>Técnico instalador</h3><p>Ganhe autonomia para desenvolver o projeto e organizar os materiais mesmo sem dominar softwares tradicionais de engenharia.</p><a className="text-link" href="#planos">Comparar planos →</a></article>
            <article><span>Atendimento especializado</span><h3>Empresa montadora</h3><p>Padronize a preparação de projetos e propostas entre equipes e reduza dependências externas.</p><a className="text-link" href="#empresas">Falar com especialista →</a></article>
            <article><span>Atendimento especializado</span><h3>Empresa revendedora</h3><p>Ajude vendedores e técnicos de balcão a responder ao cliente usando produtos e preços da própria operação.</p><a className="text-link" href="#empresas">Falar com especialista →</a></article>
          </div>
        </section>

        <section className="section pricing-section" id="planos">
          <div className="section-heading"><p className="eyebrow">PLANOS INDIVIDUAIS</p><h2>Comece com um projeto. Evolua com software, suporte e capacitação.</h2><p>Escolha entre o acesso de teste, os planos profissionais e a experiência Premium da IceNexus.</p></div>
          <div className="pricing-grid">
            <article className="price-card"><p className="plan-name">Free</p><div className="price"><strong>R$ 0</strong><span>por 15 dias</span></div><ul><li>1 projeto de câmara fria</li><li>Acesso de teste à plataforma</li><li>Suporte básico</li></ul><a className="button ghost full" href="/contratar/free">Simular plano Free</a></article>
            <article className="price-card"><p className="plan-name">Profissional Mensal</p><div className="price"><strong>R$ 159</strong><span>por mês</span></div><ul><li>Plataforma completa</li><li>Projetos ilimitados*</li><li>Lives técnicas</li><li>1 validação técnica por mês</li><li>Suporte via WhatsApp</li></ul><a className="button ghost full" href="/contratar/mensal">Simular plano mensal</a></article>
            <article className="price-card"><p className="plan-name">Profissional Semestral</p><div className="price"><strong>6 × R$ 99</strong><span>total de R$ 594</span></div><ul><li>Plataforma completa por 6 meses</li><li>Projetos ilimitados*</li><li>Lives técnicas</li><li>1 validação técnica por mês</li><li>Suporte via WhatsApp</li><li>1 mês adicional para cada indicado com assinatura confirmada e válida no Profissional Semestral</li></ul><a className="button ghost full" href="/contratar/semestral">Simular plano semestral</a></article>
            <article className="price-card preferred"><span className="recommended">Plano mais completo</span><p className="plan-name">Premium</p><div className="price"><strong>6 × R$ 497</strong><span>total de R$ 2.982</span></div><ul><li>Plataforma completa por 6 meses</li><li>Projetos ilimitados*</li><li>Lives técnicas</li><li>3 validações técnicas por mês</li><li>Cursos EAD IceNexus inclusos</li><li>70% de desconto nos cursos presenciais IceNexus</li><li>Suporte prioritário</li></ul><a className="button primary full" href="/contratar/premium">Simular plano Premium</a></article>
          </div>
          <p className="pricing-note">*Projetos ilimitados conforme as regras e limites operacionais definidos pela plataforma. Validações técnicas estão sujeitas aos critérios e ao escopo técnico estabelecidos pela IceNexus.</p>
        </section>

        <section className="section enterprise-cta" id="empresas"><div><p className="eyebrow">SOLUÇÃO PARA EMPRESAS</p><h2>Sua operação tem equipes, tabelas próprias ou uma jornada de venda específica?</h2><p>Montadoras e revendas recebem atendimento especializado para entender usuários, produtos, preços e implantação.</p></div><button className="button primary" type="button">[Canal comercial a fornecer]</button></section>
      </main>
    </PageFrame>
  );
}
