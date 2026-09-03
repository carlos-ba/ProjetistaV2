import type { ReactNode } from "react";
import Link from "next/link";

export function Brand() {
  return (
    <Link className="brand" href="/" aria-label="IceNexus — página inicial">
      <img className="brand-logo" src="/logo-icenexus.png" alt="IceNexus" />
    </Link>
  );
}

export function Header() {
  return (
    <header className="topbar">
      <Brand />
      <nav className="desktop-nav" aria-label="Navegação principal">
        <Link href="/">Ecossistema</Link>
        <a href="/projeto-camara-fria">Projeto de Câmara Fria</a>
        <a href="/academia">Academia IceNexus</a>
        <a className="access-link" href="/acessar">Acessar</a>
      </nav>
      <details className="mobile-menu">
        <summary aria-label="Abrir navegação">Menu</summary>
        <nav aria-label="Navegação para celular">
          <Link href="/">Ecossistema</Link>
          <a href="/projeto-camara-fria">Projeto de Câmara Fria</a>
          <a href="/academia">Academia IceNexus</a>
          <a href="/acessar">Acessar</a>
        </nav>
      </details>
    </header>
  );
}

export function PageFrame({ children }: { children: ReactNode }) {
  return (
    <div className="site-shell">
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
        <a href="/academia">Academia IceNexus</a>
        <a href="/acessar">Acessar</a>
      </div>
      <div className="footer-pending">
        <strong>Contato</strong>
        <a href="mailto:contato@icenexus.com.br">contato@icenexus.com.br</a>
        <a href="https://wa.me/5511957214799" target="_blank" rel="noopener noreferrer">WhatsApp: (11) 95721-4799</a>
      </div>
    </footer>
  );
}

export function Placeholder({ label, className = "" }: { label: string; className?: string }) {
  return <div className={`placeholder ${className}`} role="img" aria-label={label}><span>Imagem a fornecer</span><small>{label}</small></div>;
}
