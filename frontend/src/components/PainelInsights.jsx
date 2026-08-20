import React from 'react';

// Vírgula decimal (padrão BR) em vez do "." padrão de JS/toFixed.
const fmtQtd = (v, casas = 2) => Number(v ?? 0).toLocaleString('pt-BR', { maximumFractionDigits: casas });

const PainelInsights = ({ dimensoes, temps, isolamento, cargaCalculada, produto, compacto = false }) => {
  const gerarInsights = () => {
    const insights = [];
    
    // Converter para números para garantir a comparação
    const tInt = parseFloat(temps.interna);
    const esp = parseFloat(isolamento.esp);
    const tEvap = parseFloat(temps.evap);
    const mov = produto ? parseFloat(produto.movimentacao) : null;

    console.log("Analisando Insights:", { tInt, esp, tEvap, mov }); // Verifique isso no F12

    // --- INSIGHT DE MOVIMENTAÇÃO DE PRODUTO ---
    if (mov !== null && mov === 0) {
      insights.push({
        tipo: 'aviso',
        titulo: 'Movimentação Zerada',
        texto: 'Atenção: Não foi inserida a movimentação diária do produto. O cálculo considerará apenas a manutenção da temperatura.',
        cor: '#f39c12'
      });
    }

    // --- INSIGHT DE ISOLAMENTO ---
    // Se a temperatura for de congelados (<= -15) e a espessura for menor que 150
    if (tInt <= -15 && esp < 150) {
      insights.push({
        tipo: 'alerta',
        titulo: 'Espessura de Painel Baixa',
        texto: `CUIDADO: Para ${fmtQtd(tInt)}°C, usar painel de ${esp}mm causará alto consumo. Recomendamos 150mm.`,
        cor: '#e74c3c'
      });
    } else if (tInt > 0 && esp > 100) {
      insights.push({
        tipo: 'dica',
        titulo: 'Otimização de Custo',
        texto: 'Para resfriados, painéis de 100mm costumam ser o ponto de equilíbrio ideal entre custo e eficiência.',
        cor: '#2ecc71'
      });
    }

    // --- INSIGHT DE DELTA T (EVAPORAÇÃO) ---
    const deltaT = tInt - tEvap;
    if (isNaN(deltaT) || isNaN(tEvap)) {
      insights.push({
        tipo: 'info',
        titulo: 'Delta T não informado',
        texto: 'Forneça o valor da diferença de temperatura do ambiente e a temperatura de evaporação (campo Delta T) para receber análise de umidade relativa e adequação de produtos.',
        cor: '#6c5ce7'
      });
    } else if (deltaT >= 4 && deltaT <= 5) {
      insights.push({
        tipo: 'info',
        titulo: `Delta T ${fmtQtd(deltaT, 1)}°C — Umidade 85 a 90%`,
        texto: 'Adequado para: vegetais, produtos agrícolas, flores, gelo sem embalagem e câmaras de resfriamento.',
        cor: '#2ecc71'
      });
    } else if (deltaT > 5 && deltaT <= 7) {
      insights.push({
        tipo: 'info',
        titulo: `Delta T ${fmtQtd(deltaT, 1)}°C — Umidade 80 a 85%`,
        texto: 'Adequado para: armazenamento frigorificado geral, refrigeração, alimentos e vegetais embalados, frutas e produtos similares e produtos que requerem menores níveis de umidade relativa.',
        cor: '#3498db'
      });
    } else if (deltaT > 7 && deltaT <= 9) {
      insights.push({
        tipo: 'aviso',
        titulo: `Delta T ${fmtQtd(deltaT, 1)}°C — Umidade 65 a 80%`,
        texto: 'Adequado para: cerveja, vinho, produtos farmacêuticos, batatas, cebolas, frutas de casca dura (melão) e produtos embalados com umidade relativa moderada.',
        cor: '#f39c12'
      });
    } else if (deltaT > 9 && deltaT <= 12) {
      insights.push({
        tipo: 'aviso',
        titulo: `Delta T ${fmtQtd(deltaT, 1)}°C — Umidade 50 a 65%`,
        texto: 'Adequado para: sala de preparo e processos, corte, armazém de cerveja, doces e armazenagem de filmes.',
        cor: '#e67e22'
      });
    } else if (deltaT > 12) {
      insights.push({
        tipo: 'alerta',
        titulo: `Delta T ${fmtQtd(deltaT, 1)}°C — Umidade muito baixa`,
        texto: 'CUIDADO: Delta T elevado causa umidade relativa muito baixa, inadequada para a maioria dos produtos. Reduza a diferença entre temperatura interna e evaporação.',
        cor: '#e74c3c'
      });
    }

    // --- INSIGHT DE VOLUME/CARGA ---
    if (cargaCalculada) {
      const valorCarga = typeof cargaCalculada === 'object' 
        ? cargaCalculada.capacidade_requerida_equipamento_kcalh 
        : cargaCalculada;

      const volume = (parseFloat(dimensoes.comp) || 0) * (parseFloat(dimensoes.larg) || 0) * (parseFloat(dimensoes.alt) || 0);
      
      if (volume > 0 && valorCarga) {
        const densidadeCarga = valorCarga / volume;
        
        if (densidadeCarga > 250) {
          insights.push({
            tipo: 'info',
            titulo: 'Alta Densidade Térmica',
            texto: 'A carga por m³ está elevada. Certifique-se que o evaporador tenha flecha de ar suficiente para circular em todo o volume.',
            cor: '#3498db'
          });
        }
      }
    }

    return insights;
  };

  const insights = gerarInsights();

  if (insights.length === 0) return null;

  if (compacto) {
    return (
      <div className="space-y-3">
        <h3 className="text-xs font-black text-[#7B2D8B] uppercase tracking-widest flex items-center gap-2">
          <span>💡</span> Insights de Engenharia
        </h3>
        <div className="space-y-2">
          {insights.map((ins, idx) => (
            <div key={idx} className="p-3 rounded-lg border-l-4 bg-white shadow-sm" style={{ borderLeftColor: ins.cor }}>
              <strong className="block text-[11px] uppercase tracking-tight" style={{ color: ins.cor }}>{ins.titulo}</strong>
              <p className="text-xs text-slate-600 leading-tight mt-1">{ins.texto}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={{ marginTop: '30px' }}>
      <h3 style={{ color: '#2c3e50', borderBottom: '2px solid #6c5ce7', paddingBottom: '5px', display: 'inline-block' }}>
        💡 Insights de Engenharia
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px', marginTop: '15px' }}>
        {insights.map((ins, idx) => (
          <div key={idx} style={{ 
            padding: '15px', 
            borderRadius: '8px', 
            borderLeft: `5px solid ${ins.cor}`, 
            backgroundColor: '#fff', 
            boxShadow: '0 2px 5px rgba(0,0,0,0.1)' 
          }}>
            <strong style={{ color: ins.cor, fontSize: '0.9em', textTransform: 'uppercase' }}>{ins.titulo}</strong>
            <p style={{ margin: '8px 0 0 0', fontSize: '0.9em', color: '#555', lineHeight: '1.4' }}>{ins.texto}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PainelInsights;