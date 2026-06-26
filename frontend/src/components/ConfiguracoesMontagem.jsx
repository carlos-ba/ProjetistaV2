import React from 'react';

const CAMPO = ({ label, value, onChange, suffix = 'm', min = 0.1, step = 0.1 }) => (
  <div className="flex items-center justify-between gap-2">
    <span className="text-xs text-gray-600 flex-1">{label}</span>
    <div className="flex items-center gap-1">
      <input
        type="number"
        min={min}
        step={step}
        value={value}
        onChange={e => onChange(parseFloat(e.target.value) || 0)}
        className="w-16 text-xs border border-gray-200 rounded px-1.5 py-0.5 text-center focus:outline-none focus:ring-1 focus:ring-slate-400"
      />
      <span className="text-xs text-gray-400">{suffix}</span>
    </div>
  </div>
);

export default function ConfiguracoesMontagem({ config, onChange }) {
  const set = (campo) => (valor) => onChange({ ...config, [campo]: valor });
  const setTipo = (campo) => (e) => onChange({ ...config, [campo]: e.target.value });

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-4">
      <div className="flex items-center gap-2 mb-1">
        <div className="w-2 h-2 rounded-full bg-slate-500" />
        <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
          Configurações de Montagem
        </span>
      </div>

      {/* Tipo de conexão */}
      <div>
        <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">Tipo de Conexão dos Componentes</p>
        <div className="grid grid-cols-2 gap-2">
          {[
            { campo: 'tipo_filtro',  label: 'Filtro Secador' },
            { campo: 'tipo_visor',   label: 'Visor de Líquido' },
          ].map(({ campo, label }) => (
            <div key={campo}>
              <p className="text-[10px] text-gray-500 mb-1">{label}</p>
              <select
                value={config[campo]}
                onChange={setTipo(campo)}
                className="w-full text-xs border border-gray-200 rounded px-2 py-1 bg-white focus:outline-none focus:ring-1 focus:ring-slate-400"
              >
                <option value="solda">Solda</option>
                <option value="rosca">Rosca (flange + porca)</option>
              </select>
            </div>
          ))}
        </div>
      </div>

      {/* Trechos internos */}
      <div>
        <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">Trechos de Montagem</p>
        <div className="space-y-2">
          <CAMPO label="VET → Evaporador"          value={config.trecho_vet_evap}   onChange={set('trecho_vet_evap')} />
          <CAMPO label="Evaporador → Sifão"         value={config.trecho_evap_sifao} onChange={set('trecho_evap_sifao')} />
          <CAMPO label="Sifão → Contra-sifão (subida)" value={config.trecho_subida}     onChange={set('trecho_subida')} />
          <CAMPO label="Contra-sifão → GBC sucção"  value={config.trecho_sifao_gbc}  onChange={set('trecho_sifao_gbc')} />
        </div>
        <p className="text-[10px] text-gray-400 mt-2">
          Luvas de passagem calculadas automaticamente (1 a cada 5 m de tubulação)
        </p>
      </div>
    </div>
  );
}
