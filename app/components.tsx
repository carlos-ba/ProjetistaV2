import type { ReactNode } from "react";

export function Brand() {
  return (
    <a className="brand" href="/" aria-label="IceNexus — página inicial">
      <img className="brand-logo" src="/logo-icenexus.png" alt="IceNexus" />
    </a>
  );
}

export function Header() {
  return (
    <header className="topbar">
      <Brand />
      <nav className="desktop-nav" aria-label="Navegação principal">
        <a href="/">Ecossistema</a>
        <a href="/projeto-camara-fria">Projeto de Câmara Fria</a>
        <a href="/treinamentos">Academia IceNexus</a>
        <a className="access-link" href="/acessar">Acessar</a>
      </nav>
      <details className="mobile-menu">
        <summary aria-label="Abrir navegação">Menu</summary>
        <nav aria-label="Navegação para celular">
          <a href="/">Ecossistema</a>
          <a href="/projeto-camara-fria">Projeto de Câmara Fria</a>
          <a href="/treinamentos">Academia IceNexus</a>
          <a href="/acessar">Acessar</a>
        </nav>
      </details>
    </header>
  );
}

export function PrototypeNote() {
  return (
    <div className="prototype-note" role="note">
      <span>Protótipo V1</span>
      <p>Navegação para validação. Nenhum cadastro, pagamento ou login é realizado.</p>
    </div>
  );
}

export function PageFrame({ children }: { children: ReactNode }) {
  return (
    <div className="site-shell">
      <PrototypeNote />
      <Header />
      {children}
      <Footer />
    </div>
  );
}

export function Footer() {
  return (
    <footer className="footer">
      <div><Brand /><p>Tecnologia, engenharia e conhecimento para refrigeração.</p></div>
      <div className="footer-links">
        <a href="/projeto-camara-fria">Projeto de Câmara Fria</a>
        <a href="/treinamentos">Academia IceNexus</a>
        <a href="/acessar">Acessar</a>
      </div>
      <div className="footer-pending">
        <strong>Contato</strong>
        <span>[WhatsApp a fornecer]</span>
        <span>[E-mail a fornecer]</span>
      </div>
    </footer>
  );
}

export function Placeholder({ label, className = "" }: { label: string; className?: string }) {
  return <div className={`placeholder ${className}`} role="img" aria-label={label}><span>Imagem a fornecer</span><small>{label}</small></div>;
}
