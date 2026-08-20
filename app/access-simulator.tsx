"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";

export function AccessSimulator() {
  const [opened, setOpened] = useState(false);
  function simulate(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setOpened(true); }

  if (opened) return (
    <section className="account-demo" aria-live="polite">
      <div className="account-heading"><div><span className="success-mark">✓</span><div><p>Simulação de acesso</p><h2>Olá, usuário de teste.</h2></div></div><button className="text-link" onClick={() => setOpened(false)}>Sair da simulação</button></div>
      <p className="demo-warning">Nenhum login real foi realizado. Esta tela demonstra como os produtos contratados poderão ser apresentados.</p>
      <div className="access-product"><div className="app-icon">CF</div><div><span>Ambiente liberado</span><h3>Projeto de Câmara Fria</h3><p>Crie, consulte e exporte seus projetos.</p></div><button className="button primary" type="button">Abrir ambiente</button></div>
      <div className="locked-product"><div className="app-icon muted">+</div><div><span>Novos ambientes</span><h3>O ecossistema continuará crescendo</h3><p>Outros produtos aparecerão aqui conforme sua assinatura e disponibilidade.</p></div></div>
    </section>
  );

  return (
    <div className="access-layout">
      <section><p className="eyebrow">ÁREA DO CLIENTE</p><h1>Um acesso. Seus ambientes IceNexus.</h1><p className="hero-lead">Hoje, você seguirá diretamente para o Projeto de Câmara Fria. No futuro, esta entrada reunirá os produtos liberados para sua conta.</p><ul className="access-benefits"><li>Acesso direto, sem repetir a jornada comercial</li><li>Produtos exibidos conforme sua assinatura</li><li>Base preparada para novas ferramentas</li></ul></section>
      <form className="login-card" onSubmit={simulate}><span className="simulation-label">Simulação — não use uma senha real</span><h2>Entrar na IceNexus</h2><label>E-mail<input type="email" placeholder="usuario@exemplo.com" required /></label><label>Senha<input type="password" placeholder="••••••••" required minLength={4} /></label><button className="button primary full" type="submit">Simular entrada</button><button className="text-link centered" type="button">Esqueci minha senha</button><div className="form-divider"><span>ou</span></div><Link className="button ghost full" href="/projeto-camara-fria">Conhecer o Projeto de Câmara Fria</Link></form>
    </div>
  );
}
