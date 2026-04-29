import React, { useRef, useEffect, useState } from 'react';

const VisualizadorProjeto = ({ dimensoes, larguraPainel, espessura, onImagemGerada }) => {
  const canvasRef = useRef(null);
  
  // Estados para Zoom e Pan
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [lastMousePos, setLastMousePos] = useState({ x: 0, y: 0 });
  const [vista, setVista] = useState('planta'); // 'planta', 'frontal', 'lateral', 'todas'
  const [zoomAtivo, setZoomAtivo] = useState(false);

  // Sanitização de entradas
  const comp = parseFloat(dimensoes.comp) || 0;
  const larg = parseFloat(dimensoes.larg) || 0;
  const alt = parseFloat(dimensoes.alt) || 0;
  const mod = (parseFloat(larguraPainel) || 1150) / 1000;
  const esp = (parseFloat(espessura) || 100) / 1000;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const handleWheelManual = (e) => {
      // Impede a rolagem da página apenas se o zoom estiver explicitamente ativo (após clique)
      if (zoomAtivo) {
        e.preventDefault();
        
        const zoomSpeed = 0.0015;
        const delta = -e.deltaY * zoomSpeed;
        
        setScale(prevScale => {
          const newScale = prevScale * (1 + delta);
          // Limites de zoom: 0.1x a 20x
          return Math.min(Math.max(0.1, newScale), 20);
        });
      }
    };

    const handleBlur = () => {
      setZoomAtivo(false);
    };

    const handleClick = () => {
      setZoomAtivo(true);
      canvas.focus(); 
    };

    // Adiciona o listener com passive: false para permitir preventDefault()
    canvas.addEventListener('wheel', handleWheelManual, { passive: false });
    canvas.addEventListener('blur', handleBlur);
    canvas.addEventListener('click', handleClick);

    return () => {
      canvas.removeEventListener('wheel', handleWheelManual);
      canvas.removeEventListener('blur', handleBlur);
      canvas.removeEventListener('click', handleClick);
    };
  }, [zoomAtivo]); // Re-adiciona o listener quando o estado de zoomAtivo muda

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    // Limpa canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (comp <= 0 || larg <= 0 || alt <= 0) {
      ctx.fillStyle = '#64748b';
      ctx.font = '14px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Aguardando dimensões válidas...', canvas.width / 2, canvas.height / 2);
      return;
    }

    // Configurações de Escala Base (Auto-fit)
    const padding = 50;
    const gap = 80;
    
    let totalWidth, totalHeight;
    let originPlanta = { x: 0, y: 0 };
    let originFrontal = { x: 0, y: 0 };
    let originLateral = { x: 0, y: 0 };

    if (vista === 'planta') {
      totalWidth = comp;
      totalHeight = larg;
      originPlanta = { x: 0, y: 0 };
    } else if (vista === 'frontal') {
      totalWidth = comp;
      totalHeight = alt;
      originFrontal = { x: 0, y: 0 };
    } else if (vista === 'lateral') {
      totalWidth = larg;
      totalHeight = alt;
      originLateral = { x: 0, y: 0 };
    } else {
      // 'todas'
      totalWidth = comp + gap + larg;
      totalHeight = larg + gap + alt;
      originPlanta = { x: 0, y: totalHeight - larg };
      originFrontal = { x: 0, y: originPlanta.y - gap - alt };
      originLateral = { x: comp + gap, y: originFrontal.y };
    }
    
    const baseScaleX = (canvas.width - 2 * padding) / totalWidth;
    const baseScaleY = (canvas.height - 2 * padding) / totalHeight;
    const baseScale = Math.min(baseScaleX, baseScaleY);

    // Escala final combinada com o zoom do usuário
    const finalScale = baseScale * scale;

    // Funções auxiliares de desenho (usando finalScale e offset)
    const drawRect = (x, y, w, h, color) => {
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      // Aplicar offset e escala
      ctx.strokeRect(
        (x * finalScale) + offset.x + padding, 
        (y * finalScale) + offset.y + padding, 
        w * finalScale, 
        h * finalScale
      );
    };

    const drawText = (text, x, y, color, font = 'bold 12px sans-serif', align = 'left') => {
      ctx.fillStyle = color;
      ctx.font = font;
      ctx.textAlign = align;
      ctx.fillText(
        text, 
        (x * finalScale) + offset.x + padding, 
        (y * finalScale) + offset.y + padding
      );
    };

    ctx.save();
    
    // 1. PLANTA BAIXA
    if (vista === 'planta' || vista === 'todas') {
      let qtd_base = Math.floor(comp / mod);
      let resto_base = comp % mod;
      
      // Parede Inferior
      for (let i = 0; i < qtd_base; i++) {
          drawRect(originPlanta.x + i * mod, originPlanta.y + larg - esp, mod, esp, '#3b82f6');
      }
      if (resto_base > 0.001) {
          drawRect(originPlanta.x + qtd_base * mod, originPlanta.y + larg - esp, resto_base, esp, '#3b82f6');
      }

      // Parede Superior
      for (let i = 0; i < qtd_base; i++) {
          drawRect(originPlanta.x + i * mod, originPlanta.y, mod, esp, '#3b82f6');
      }
      if (resto_base > 0.001) {
          drawRect(originPlanta.x + qtd_base * mod, originPlanta.y, resto_base, esp, '#3b82f6');
      }

      // Paredes Laterais
      const h_util = larg - 2 * esp;
      if (h_util > 0) {
          let qtd_parede = Math.floor(h_util / mod);
          let resto_parede = h_util % mod;
          
          for (let i = 0; i < qtd_parede; i++) {
              drawRect(originPlanta.x, originPlanta.y + esp + i * mod, esp, mod, '#10b981');
              drawRect(originPlanta.x + comp - esp, originPlanta.y + esp + i * mod, esp, mod, '#10b981');
          }
          if (resto_parede > 0.001) {
              drawRect(originPlanta.x, originPlanta.y + esp + qtd_parede * mod, esp, resto_parede, '#10b981');
              drawRect(originPlanta.x + comp - esp, originPlanta.y + esp + qtd_parede * mod, esp, resto_parede, '#10b981');
          }
      }
      drawText("PLANTA BAIXA", originPlanta.x, originPlanta.y + larg + (vista === 'todas' ? 0.5 : 0.2), '#1e293b');
    }

    // 2. VISTA FRONTAL
    if (vista === 'frontal' || vista === 'todas') {
      let qtd_base = Math.floor(comp / mod);
      let resto_base = comp % mod;
      for (let i = 0; i < qtd_base; i++) {
          drawRect(originFrontal.x + i * mod, originFrontal.y, mod, alt, '#3b82f6');
      }
      if (resto_base > 0.001) {
          drawRect(originFrontal.x + qtd_base * mod, originFrontal.y, resto_base, alt, '#3b82f6');
      }
      drawText("VISTA FRONTAL", originFrontal.x, originFrontal.y + alt + (vista === 'todas' ? 0.5 : 0.2), '#1e293b');
    }

    // 3. VISTA LATERAL
    if (vista === 'lateral' || vista === 'todas') {
      let qtd_lat = Math.floor(larg / mod);
      let resto_lat = larg % mod;
      for (let i = 0; i < qtd_lat; i++) {
          drawRect(originLateral.x + i * mod, originLateral.y, mod, alt, '#a855f7');
      }
      if (resto_lat > 0.001) {
          drawRect(originLateral.x + qtd_lat * mod, originLateral.y, resto_lat, alt, '#a855f7');
      }
      drawText("VISTA LATERAL", originLateral.x, originLateral.y + alt + (vista === 'todas' ? 0.5 : 0.2), '#1e293b');
    }

    ctx.restore();

    // Notifica o pai sobre a nova imagem gerada (se necessário para o orçamento)
    // Debounce maior para evitar loops de renderização no pai
    if (onImagemGerada && comp > 0 && larg > 0 && alt > 0) {
      const timer = setTimeout(() => {
        const dataUrl = canvas.toDataURL('image/png');
        // Só dispara se for diferente da última (reduz processamento no pai)
        if (canvas.lastImage !== dataUrl) {
          canvas.lastImage = dataUrl;
          onImagemGerada(dataUrl);
        }
      }, 1500); // Aumentado para 1.5s
      return () => clearTimeout(timer);
    }

  }, [comp, larg, alt, mod, esp, scale, offset, vista, onImagemGerada]);

  // Handlers de Eventos
  const handleMouseDown = (e) => {
    setIsDragging(true);
    setLastMousePos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    const dx = e.clientX - lastMousePos.x;
    const dy = e.clientY - lastMousePos.y;
    setOffset(prev => ({ x: prev.x + dx, y: prev.y + dy }));
    setLastMousePos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => setIsDragging(false);

  const resetView = () => {
    setScale(1);
    setOffset({ x: 0, y: 0 });
  };

  const alternarVista = (novaVista) => {
    setVista(novaVista);
    setScale(1);
    setOffset({ x: 0, y: 0 });
  };

  return (
    <div className="bg-slate-50 rounded-xl border border-slate-200 p-4">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
          <span className="text-indigo-500">📐</span> Visualização Técnica
        </h3>
        
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex bg-white border border-slate-200 rounded-lg p-1 shadow-sm">
            {[
              { id: 'planta', label: 'Planta' },
              { id: 'frontal', label: 'Frontal' },
              { id: 'lateral', label: 'Lateral' },
              { id: 'todas', label: 'Todas' }
            ].map((v) => (
              <button
                key={v.id}
                onClick={() => alternarVista(v.id)}
                className={`px-3 py-1 text-[10px] font-bold rounded-md transition-all ${
                  vista === v.id 
                    ? 'bg-indigo-600 text-white shadow-sm' 
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {v.label}
              </button>
            ))}
          </div>
          
          <button 
            onClick={resetView}
            className="text-[10px] bg-white border border-slate-300 px-2 py-1.5 rounded-lg hover:bg-slate-100 transition-colors font-bold text-slate-600 shadow-sm"
          >
            RESETAR
          </button>
        </div>
      </div>
      
      <div className="flex gap-4 text-[10px] font-bold uppercase mb-3 overflow-x-auto pb-1">
        <span className="flex items-center gap-1 whitespace-nowrap"><i className="w-2 h-2 bg-blue-500 rounded-full"></i> Horizontais</span>
        <span className="flex items-center gap-1 whitespace-nowrap"><i className="w-2 h-2 bg-emerald-500 rounded-full"></i> Verticais</span>
        <span className="flex items-center gap-1 whitespace-nowrap"><i className="w-2 h-2 bg-purple-500 rounded-full"></i> Lateral</span>
      </div>
      
      <div className={`relative group overflow-hidden rounded-lg shadow-inner border transition-all duration-300 bg-white ${
        zoomAtivo ? 'ring-2 ring-indigo-500 border-transparent' : 'border-slate-100'
      }`}>
        <canvas 
          ref={canvasRef} 
          width={800} 
          height={500} 
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className={`w-full h-auto cursor-${isDragging ? 'grabbing' : 'grab'} outline-none`}
          tabIndex="0"
        />
        
        {/* Dicas de Controle */}
        <div className="absolute top-2 right-2 flex gap-2 pointer-events-none">
          {zoomAtivo ? (
            <span className="bg-indigo-600 text-white text-[9px] px-2 py-1 rounded font-bold animate-pulse">
              MODO CAD ATIVO (Zoom Habilitado)
            </span>
          ) : (
            <span className="bg-slate-800/50 text-white text-[9px] px-2 py-1 rounded">
              Clique para ativar o Zoom
            </span>
          )}
        </div>

        <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/50 text-white text-[9px] px-2 py-1 rounded pointer-events-none">
          Scroll: Zoom | Arraste: Mover
        </div>
      </div>

      <p className="mt-2 text-[10px] text-slate-500 italic">
        * Use o mouse para navegar no desenho. Painéis de {larguraPainel}mm.
      </p>
    </div>
  );
};

export default VisualizadorProjeto;
