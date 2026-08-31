# Carga térmica dos ventiladores do evaporador — pesquisa (sem implementação)

**Data:** 2026-08-31
**Status:** pesquisa concluída, **nada implementado** — decisão consciente de
não mexer em `calculos_carga_termica.py` por ora (área sensível, já validada
número a número numa auditoria real). Documentado aqui pra retomar quando o
usuário decidir seguir.

## Contexto

Durante a auditoria do projeto "tatiminas cam gr" (verificação número a
número do `calculos_carga_termica.py` contra dados reais de produção),
apareceu uma carga de motor de 3.800 W lançada manualmente no campo
genérico "outros motores" (`potencia_outros_motores_w`). Isso levantou a
pergunta: no **primeiro**
cálculo de carga térmica (Card 2), o evaporador ainda não foi escolhido
(isso só acontece no Card 3) — então não existe potência real de motor de
ventilador disponível ainda. Perguntei ao usuário se ASHRAE ou norma
brasileira equivalente definem uma premissa pra essa estimativa preliminar.

## Achado — não existe norma numerada específica

Nem ASHRAE nem NBR têm uma cláusula numerada específica só pra isso. A
referência de prática consolidada no Brasil é o livro-texto **Stoecker &
Jabardo, "Refrigeração Industrial"**, não uma norma ABNT. É convenção de
engenharia, não obrigação regulatória.

## Duas premissas encontradas (fontes de engenharia, ver links)

**1. Estimativa preliminar (antes de escolher o evaporador) — a que serve
pra este caso:**
- Regra simples: **5% da carga térmica total (24h)**.
- Alternativa ligada ao volume da câmara (não circular, ao contrário da
  regra dos 5% que depende do próprio total que ainda não existe):
  **Potência ventiladores (W) = 135 + 3,45 × Volume da câmara (m³)**,
  ponderada pelas horas de funcionamento do evaporador/dia (fonte documenta
  21h/dia pra câmara de refrigerados; **não achei o valor equivalente pra
  câmara de congelados** — não presumir, pesquisar de novo se for adotar
  essa via).
- A própria fonte documenta a faixa "Carga evaporador: 1–15% da carga
  total" (ventiladores + resistências de degelo somados), consistente com
  os 5% isolados pra só ventiladores.

**2. Fórmula rigorosa (depois de escolher o evaporador de verdade, quando
já se sabe a potência do motor):**
- Q = N(CV) × 632,41 (kcal/h por CV) × (horas de uso/24h) — fonte técnica
  brasileira. Mesmo princípio que a ASHRAE usa pra motor elétrico
  encerrado dentro do espaço refrigerado: praticamente 100% da potência
  nominal do motor vira calor no ambiente.
- Só se aplica a evaporador de convecção forçada (com ventilador) — não se
  aplica a evaporador estático (natural).

## Recomendação (não implementada)

Adotar **5% da carga térmica total (24h)** como estimativa preliminar no
Card 2 — mais simples, bate com a faixa documentada, e segue o mesmo padrão
que `fator_seguranca_perc` já existente no motor de cálculo (outro
percentual fixo aplicado sobre o total). Quando o Card 3 escolher o
evaporador real, essa estimativa preliminar seria substituída pela carga
real do motor do fabricante (fórmula rigorosa acima).

## Por que não implementar agora

Pedido explícito do usuário: "não vamos mexer no código nesta área muito
sensível" — `calculos_carga_termica.py` acabou de passar por uma auditoria
completa (todos os números conferidos manualmente contra um projeto real em
produção) e qualquer mudança ali merece o mesmo nível de cuidado, não uma
adição apressada.

## Pendências se isso for retomado

1. Confirmar as horas de funcionamento do evaporador pra câmara de
   **congelados** (só achei o valor pra refrigerados, 21h/dia) — pesquisar
   antes de usar a fórmula volumétrica.
2. Decidir entre a regra dos 5% (mais simples) e a fórmula volumétrica
   (mais precisa, mas precisa da hora de funcionamento certa).
3. Decidir se essa estimativa preliminar fica visível/editável pro usuário
   na tela (como as outras premissas fixas documentadas na auditoria —
   T.externa, horas de iluminação/pessoas, margem de segurança) ou some
   quando o Card 3 escolhe o evaporador real.

## Fontes

- [DISEÑO DE UNA CÁMARA FRIGORÍFICA PASO A PASO — Cálculo de la carga térmica (Coolproyect)](https://coolproyect.es/website/wp-content/uploads/2022/03/1-calculo-de-la-carga-termica-camara-de-refrigerados.pdf) — fórmula `135 + 3,45×Volume` e a regra dos 5%.
- [CÂMARA FRIGORÍFICA — Cálculo de carga térmica (BR Prom)](http://brprom-file.s3.amazonaws.com/257_camara_fria_carga.pdf) — fórmula rigorosa `N(CV) × 632,41 × horas`.
- [Cargas térmicas de refrigeración — Blog Averroes/Junta de Andalucía](https://blogsaverroes.juntadeandalucia.es/amrandado/cargas-termicas-refrigeracion/)
- [Refrigeração Industrial (Stoecker & Jabardo) — texto completo](https://archive.org/stream/RefrigeracaoIndustrialLIVROCOMPLETOJabardoEStoecker/Refrigera%C3%A7%C3%A3o+Industrial+(LIVRO+COMPLETO)+-Jabardo_e_Stoecker_djvu.txt)
- [ASHRAE Handbook — Refrigeration, Table of Contents](https://www.ashrae.org/technical-resources/ashrae-handbook/table-of-contents-2022-ashrae-handbook-refrigeration)
