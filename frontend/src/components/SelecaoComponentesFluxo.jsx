import React, { useState, useEffect } from 'react';
import api from '../api';

const SelecaoComponentesFluxo = ({ equipamentoSelecionado, aoFinalizar }) => {
  const [componentes, setComponentes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState('');
  const [finalizado, setFinalizado] = useState(false);

  useEffect(() => {
    if (equipamentoSelecionado) {
      buscarComponentes();
    }
  }, [equipamentoSelecionado]);

  const buscarComponentes = async () => {
    setLoading(true);
    setErro('');
    setFinalizado(false);

    try {
      const response = await api.post('/api/v1/selecionar-componentes-fluxo/', {
        capacidade_kcalh: equipamentoSelecionado.capacidade_real,
        fluido: equipamentoSelecionado.fluido,
        temp_evap: equipamentoSelecionado.temp_evap
      });
      setComponentes(response.data);
    } catch (error) {
      console.error(error);
      setErro('Erro ao buscar componentes de fluxo.');
    } finally {
      setLoading(false);
    }
  };

  const enviarParaOrcamento = () => {
    if (aoFinalizar) {
      const materiaisFormatados = componentes.map(c => ({
        item: `${c.categoria}: ${c.modelo} (${c.fabricante})`,
        quantidade: 1,
        unidade: 'un',
        detalhe: `Conexão: ${c.conexao_entrada} | Faixa: ${c.faixa_operacao}`,
        preco: c.custo // Se o orçamento suportar preço direto
      }));
      aoFinalizar(materiaisFormatados);
      setFinalizado(true);
    }
  };

  if (!equipamentoSelecionado) return null;

  return (
    <div style={{ background: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', marginBottom: '40px' }}>
      <h3 style={{ borderLeft: '5px solid #ffc107', paddingLeft: '10px', color: '#333', marginTop: 0 }}>
        3.5 Componentes de Fluxo (Linha de Líquido e Sucção)
      </h3>

      {loading && <p>Buscando melhores componentes...</p>}
      {erro && <p style={{ color: 'red' }}>{erro}</p>}

      {!loading && componentes.length > 0 && (
        <div>
          <p style={{ fontSize: '0.9rem', color: '#666' }}>
            Baseado na Unidade <strong>{equipamentoSelecionado.modelo}</strong>, selecionamos os seguintes componentes:
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
            {componentes.map((c, idx) => (
              <div key={idx} style={{ padding: '10px', border: '1px solid #eee', borderRadius: '5px', background: '#fcfcfc' }}>
                <div style={{ fontWeight: 'bold', fontSize: '0.85rem', color: '#007bff' }}>{c.categoria}</div>
                <div style={{ fontSize: '1rem', fontWeight: 'bold' }}>{c.modelo}</div>
                <div style={{ fontSize: '0.8rem', color: '#777' }}>{c.fabricante} | {c.conexao_entrada}</div>
              </div>
            ))}
          </div>

          {!finalizado ? (
            <button 
              onClick={enviarParaOrcamento}
              style={{ 
                marginTop: '20px', width: '100%', padding: '12px', 
                background: '#ffc107', color: '#000', border: 'none', 
                borderRadius: '5px', fontWeight: 'bold', cursor: 'pointer' 
              }}
            >
              ADICIONAR COMPONENTES AO ORÇAMENTO ✅
            </button>
          ) : (
            <div style={{ marginTop: '20px', padding: '10px', background: '#d4edda', color: '#155724', borderRadius: '5px', textAlign: 'center' }}>
              ✅ Componentes adicionados com sucesso!
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SelecaoComponentesFluxo;
