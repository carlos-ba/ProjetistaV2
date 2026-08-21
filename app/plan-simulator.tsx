"use client";

import { FormEvent, useState } from "react";

const plans = {
  free: { name: "Free", price: "R$ 0", detail: "1 projeto • 15 dias • suporte básico", action: "Ativar teste" },
  mensal: { name: "Profissional Mensal", price: "R$ 159/mês", detail: "Projetos ilimitados* • lives técnicas • 1 validação/mês • WhatsApp", action: "Continuar para pagamento" },
  semestral: { name: "Profissional Semestral", price: "6 × R$ 99", detail: "6 meses • projetos ilimitados* • lives técnicas • 1 validação/mês", action: "Continuar para pagamento" },
  premium: { name: "Premium", price: "6 × R$ 497", detail: "3 validações/mês • cursos EAD IceNexus • 70% OFF em cursos presenciais", action: "Continuar para pagamento" },
} as const;

type PlanKey = keyof typeof plans;

export function PlanSimulator({ initialPlan }: { initialPlan: string }) {
  const safePlan: PlanKey = initialPlan in plans ? initialPlan as PlanKey : "free";
  const [plan, setPlan] = useState<PlanKey>(safePlan);
  const [step, setStep] = useState(1);
  const selected = plans[plan];

  function next(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setStep(current => Math.min(3, current + 1)); }

  return (
    <div className="checkout-shell">
      <div className="checkout-steps" aria-label={`Etapa ${step} de 3`}><span className={step >= 1 ? "active" : ""}>1. Plano</span><i /><span className={step >= 2 ? "active" : ""}>2. Cadastro</span><i /><span className={step >= 3 ? "active" : ""}>3. Revisão</span></div>
      {step === 1 && <section className="checkout-card"><p className="eyebrow">SIMULAÇÃO DA CONTRATAÇÃO</p><h1>Escolha como quer começar.</h1><p>Nenhuma cobrança ou cadastro será realizado neste protótipo.</p><div className="plan-choice">{(Object.keys(plans) as PlanKey[]).map(key => <button className={plan === key ? "selected" : ""} type="button" key={key} onClick={() => setPlan(key)}><span>{plans[key].name}</span><strong>{plans[key].price}</strong><small>{plans[key].detail}</small></button>)}</div><button className="button primary full" onClick={() => setStep(2)}>Continuar com {selected.name}</button></section>}
      {step === 2 && <form className="checkout-card" onSubmit={next}><button className="back-button" type="button" onClick={() => setStep(1)}>← Voltar</button><p className="eyebrow">DADOS DE ACESSO</p><h2>Crie sua conta de demonstração.</h2><div className="form-grid"><label>Nome completo<input required placeholder="Seu nome" /></label><label>E-mail profissional<input type="email" required placeholder="voce@empresa.com.br" /></label><label>WhatsApp<input required placeholder="(00) 00000-0000" /></label><label>Perfil<select defaultValue=""><option value="" disabled>Selecione</option><option>Técnico instalador</option><option>Empresa montadora</option><option>Empresa revendedora</option></select></label></div><label className="check-row"><input type="checkbox" required /><span>Concordo em simular a jornada. Nenhum dado será enviado.</span></label><button className="button primary full" type="submit">Revisar escolha</button></form>}
      {step === 3 && <section className="checkout-card review-card"><button className="back-button" type="button" onClick={() => setStep(2)}>← Voltar</button><span className="success-mark">✓</span><p className="eyebrow">JORNADA VALIDADA</p><h2>{selected.name} — {selected.price}</h2><p>{selected.detail}</p><div className="review-box"><strong>Próxima etapa real</strong><p>{plan === "free" ? "Criar a conta e liberar o projeto de teste por 15 dias." : "Abrir o checkout seguro e confirmar as condições da assinatura."}</p></div><button className="button primary full" type="button">{selected.action} — simulação</button><a className="text-link centered" href="/projeto-camara-fria">Voltar aos planos</a></section>}
    </div>
  );
}
