import CatalogoPrecosEmpresa from './CatalogoPrecosEmpresa';

/**
 * Autoadministração da lista de preços da própria empresa (Fase B). Mesmo componente
 * de conteúdo usado na implantação (AdminEmpresas.jsx), aqui escopado pela própria
 * empresa do usuário logado — o backend resolve isso via get_empresa_atual, não um
 * empresa_id na URL.
 */
export default function CatalogoPrecosPage({ onFechar }) {
  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="absolute inset-0 bg-black/40" onClick={onFechar} />
      <div className="relative ml-auto w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 bg-slate-800">
          <div>
            <p className="text-sm font-black text-white">📦 Catálogo de Preços</p>
            <p className="text-[10px] text-slate-400">
              Preços da sua empresa — usados direto no orçamento, sem precisar cotar
            </p>
          </div>
          <button onClick={onFechar} className="text-slate-400 hover:text-white text-xl leading-none">✕</button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          <CatalogoPrecosEmpresa apiBase="/api/v1/produto-empresa" />
        </div>
      </div>
    </div>
  );
}
