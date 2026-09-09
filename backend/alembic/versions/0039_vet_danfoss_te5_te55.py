"""Catálogo VET Danfoss TE5-TE55 — cobre capacidades maiores que o T2 (corpo T2-6 parava em ~17.7 mil kcal/h)

Pedido do usuário: UCs Bitzer maiores (evolução do catálogo em 2026-09-08)
passaram a exigir válvula de expansão além do que o corpo T2 cobre. Danfoss
não tem "TE 30" — a linha TE5-55 tem só 4 corpos (TE5, TE12, TE20, TE55),
confirmado contra 2 datasheets oficiais Danfoss (nenhuma fonte, incluindo
catálogos 2020+, menciona TE30). 14 combinações corpo+orifício ao todo:
TE5 (0.5/01/02/03/04), TE12 (05/06/07), TE20 (08/09), TE55 (10/11/12/13) —
o orifício 9B do TE55 existe mas só tem tabela publicada pra faixa B
(-60 a -25°C), fora do escopo desta leva (ver nota de pendência abaixo).

Fontes (extraídas e conferidas, T.Cond = 45°C):
  - DKRCC.PD.AB0.A3.02 (2011) — R22, R404A/R507, R134a, R407C: tabela
    completa faixa N (-40 a +10°C, passo 5°C) e faixa B (não usada aqui).
  - DKRCC.PD.AB0.A6.02 (2017) — R448A/R449A: só faixa N, passo 10°C
    (-40/-30/-20/-10/0/10), mesmos 4 pontos de T.Cond do doc de 2011.
  - R290, R402B, R452A, R513A: sem tabela de capacidade publicada
    encontrada pra essa linha (nem em fontes 2020+) — não inventamos
    valor; ficam de fora até a Danfoss publicar ou o CoolSelector2
    confirmar.

R404A/R507 e R448A/R449A: a Danfoss publica uma tabela só pros dois
fluidos de cada par (valores idênticos) — replicada aqui como fluido
separado (fluido é comparado por igualdade exata na seleção,
`componentes_fluxo.py`), fechando um gap que a T2 antiga já tinha (T2 só
tem 'R22'/'R404A', nunca teve 'R507').

Capacidade mínima = 25% da nominal — mesmo padrão já usado no T2 (migration
0018, "padrão Danfoss").

Conexões: cada corpo Danfoss vem em mais de uma combinação de entrada/saída
(pedido explícito do usuário pra registrar TODAS, não só uma). Registramos
1 conexão "operacional" por orifício em `conexao_entrada`/`conexao_saida`
(cresce com a capacidade do orifício dentro do que o corpo oferece — não é
uma regra formal da Danfoss, é uma escolha de engenharia nossa já que o
corpo/conexão e o orifício são peças compradas separadamente) e a lista
completa das conexões reais do corpo (com código de venda) em
`dados_especificos.conexoes_disponiveis`, pra não perder nenhuma opção.

T.Cond fixo em 45°C (decisão do usuário, 2026-09-09, pra simplificar) — os
dados-fonte têm 4 pontos reais (25/35/45/55°C). PENDÊNCIA FUTURA: dá pra
fazer a VET interpolar por T.Cond igual ao Card 3 já faz pra UC/Evaporadora
(`selecao_equipamentos.py`) usando os outros 3 pontos, que não foram
descartados — só não estão cadastrados ainda. Ver também nota de pendência
sobre orifício 9B (faixa B) e os 4 fluidos sem tabela publicada.

Revision ID: 0039
Revises: 0038
Create Date: 2026-09-09
"""
from alembic import op
import sqlalchemy as sa
import json

revision = "0039"
down_revision = "0038"
branch_labels = None
depends_on = None

FABRICANTE = "Danfoss"
CATEGORIA = "Válvula de Expansão Termostática"
FONTE = "Danfoss DKRCC.PD.AB0.A3.02 (2011) / DKRCC.PD.AB0.A6.02 (2017), T.Cond 45°C"

# corpo, orifício, código de venda do conjunto de orifício, conexão operacional, todas as conexões reais do corpo
MODELOS = [
    ("TE5 - 0.5", "TE5", "0.5", "067B2788", '1/2"', '5/8"'),
    ("TE5 - 01",  "TE5", "01",  "067B2789", '1/2"', '7/8"'),
    ("TE5 - 02",  "TE5", "02",  "067B2790", '5/8"', '7/8"'),
    ("TE5 - 03",  "TE5", "03",  "067B2791", '5/8"', '7/8"'),
    ("TE5 - 04",  "TE5", "04",  "067B2792", '7/8"', '1.1/8"'),
    ("TE12 - 05", "TE12", "05", "067B2708", '5/8"', '7/8"'),
    ("TE12 - 06", "TE12", "06", "067B2709", '7/8"', '1"'),
    ("TE12 - 07", "TE12", "07", "067B2710", '7/8"', '1.1/8"'),
    ("TE20 - 08", "TE20", "08", "067B2771", '7/8"', '1.1/8"'),
    ("TE20 - 09", "TE20", "09", "067B2773", '7/8"', '1.1/8"'),
    ("TE55 - 10", "TE55", "10", "067G2701", '1.1/8"', '1.3/8"'),
    ("TE55 - 11", "TE55", "11", "067G2704", '1.1/8"', '1.3/8"'),
    ("TE55 - 12", "TE55", "12", "067G2707", '1.1/8"', '1.3/8"'),
    ("TE55 - 13", "TE55", "13", "067G2710", '1.1/8"', '1.3/8"'),
]

CONEXOES_POR_CORPO = {
    "TE5":  ['1/2"x5/8"', '1/2"x7/8"', '5/8"x7/8"', '7/8"x1.1/8"'],
    "TE12": ['5/8"x7/8"', '7/8"x1"', '7/8"x1.1/8"'],
    "TE20": ['7/8"x1.1/8"'],
    "TE55": ['1.1/8"x1.3/8"'],
}

TEMPS_5C = [-40, -35, -30, -25, -20, -15, -10, -5, 0, 5, 10]
TEMPS_10C = [-40, -30, -20, -10, 0, 10]

# kcal/h a T.Cond=45°C, já convertido de kW (×860) — ver PR/scratch de geração
R22 = {
    "TE5 - 0.5": [4050.6, 4575.2, 5142.8, 5762.0, 6407.0, 7095.0, 7791.6, 8488.2, 9141.8, 9718.0, 10173.8],
    "TE5 - 01":  [7413.2, 8393.6, 9451.4, 10595.2, 11799.2, 13063.4, 14344.8, 15609.0, 16795.8, 17819.2, 18610.4],
    "TE5 - 02":  [10371.6, 11773.4, 13278.4, 14886.6, 16589.4, 18343.8, 20106.8, 21809.6, 23374.8, 24682.0, 25610.8],
    "TE5 - 03":  [13029.0, 14731.8, 16580.8, 18593.2, 20734.6, 22979.2, 25275.4, 27520.0, 29670.0, 31476.0, 32766.0],
    "TE5 - 04":  [17157.0, 19530.6, 22136.4, 24974.4, 28036.0, 31218.0, 34486.0, 37582.0, 40506.0, 42914.0, 44548.0],
    "TE12 - 05": [20794.8, 23288.8, 26058.0, 29154.0, 32508.0, 36206.0, 40076.0, 44032.0, 47988.0, 51686.0, 54782.0],
    "TE12 - 06": [26058.0, 29412.0, 33196.0, 37410.0, 42054.0, 47128.0, 52546.0, 58222.0, 63640.0, 68800.0, 73100.0],
    "TE12 - 07": [33368.0, 37238.0, 41538.0, 46440.0, 51944.0, 57964.0, 64500.0, 71380.0, 79120.0, 86000.0, 92020.0],
    "TE20 - 08": [45236.0, 51428.0, 58308.0, 65360.0, 73960.0, 82560.0, 92020.0, 100620.0, 109220.0, 116960.0, 122120.0],
    "TE20 - 09": [47300.0, 54008.0, 61060.0, 69660.0, 79120.0, 89440.0, 100620.0, 111800.0, 123840.0, 134160.0, 141900.0],
    "TE55 - 10": [49880.0, 58050.0, 67080.0, 77400.0, 88580.0, 100620.0, 113520.0, 126420.0, 140180.0, 152220.0, 162540.0],
    "TE55 - 11": [54352.0, 63640.0, 73100.0, 84280.0, 96320.0, 109220.0, 122980.0, 137600.0, 151360.0, 165120.0, 176300.0],
    "TE55 - 12": [57620.0, 67080.0, 77400.0, 89440.0, 102340.0, 116960.0, 132440.0, 148780.0, 164260.0, 179740.0, 193500.0],
    "TE55 - 13": [67940.0, 79980.0, 92880.0, 106640.0, 122980.0, 140180.0, 159100.0, 178880.0, 198660.0, 216720.0, 232200.0],
}
R404A = {
    "TE5 - 0.5": [2648.8, 3070.2, 3534.6, 4042.0, 4575.2, 5151.4, 5736.2, 6329.6, 6897.2, 7396.0, 7783.0],
    "TE5 - 01":  [4859.0, 5650.2, 6510.2, 7439.0, 8436.6, 9485.8, 10569.4, 11644.4, 12667.8, 13553.6, 14215.8],
    "TE5 - 02":  [6828.4, 7955.0, 9167.6, 10474.8, 11859.4, 13304.2, 14783.4, 16236.8, 17569.8, 18696.4, 19479.0],
    "TE5 - 03":  [8471.0, 9855.6, 11369.2, 13003.2, 14766.2, 16623.8, 18550.2, 20468.0, 22265.4, 23804.8, 24914.2],
    "TE5 - 04":  [11214.4, 13140.8, 15239.2, 17526.8, 19995.0, 22600.8, 25292.6, 27950.0, 30444.0, 32422.0, 33798.0],
    "TE12 - 05": [13837.4, 16202.4, 18825.4, 21749.4, 25000.2, 28552.0, 32508.0, 36636.0, 40764.0, 44548.0, 47558.0],
    "TE12 - 06": [16383.0, 19358.6, 22686.8, 26402.0, 30616.0, 35260.0, 40334.0, 45752.0, 51256.0, 56330.0, 60200.0],
    "TE12 - 07": [19874.6, 23194.2, 26918.0, 31218.0, 36120.0, 41624.0, 47902.0, 54696.0, 61920.0, 68800.0, 74820.0],
    "TE20 - 08": [24088.6, 28294.0, 33024.0, 38270.0, 44118.0, 50482.0, 57276.0, 64500.0, 71380.0, 77400.0, 81700.0],
    "TE20 - 09": [25361.4, 29928.0, 35002.0, 40764.0, 47300.0, 54696.0, 62780.0, 71380.0, 79980.0, 88580.0, 94600.0],
    "TE55 - 10": [28724.0, 34830.0, 41710.0, 49364.0, 57964.0, 67940.0, 78260.0, 89440.0, 100620.0, 110940.0, 120400.0],
    "TE55 - 11": [31132.0, 37754.0, 45150.0, 53406.0, 62780.0, 73100.0, 84280.0, 96320.0, 108360.0, 119540.0, 129860.0],
    "TE55 - 12": [32852.0, 39904.0, 47730.0, 56674.0, 67080.0, 78260.0, 90300.0, 103200.0, 116960.0, 129860.0, 141900.0],
    "TE55 - 13": [38356.0, 46698.0, 56158.0, 67080.0, 79120.0, 92020.0, 107500.0, 122980.0, 139320.0, 155660.0, 168560.0],
}
R134A = {
    "TE5 - 0.5": [2270.4, 2588.6, 2941.2, 3328.2, 3758.2, 4231.2, 4721.4, 5246.0, 5762.0, 6260.8, 6708.0],
    "TE5 - 01":  [4153.8, 4747.2, 5400.8, 6123.2, 6914.4, 7774.4, 8686.0, 9632.0, 10578.0, 11489.6, 12280.8],
    "TE5 - 02":  [5805.0, 6639.2, 7568.0, 8591.4, 9700.8, 10896.2, 12160.4, 13467.6, 14766.2, 15978.8, 17010.8],
    "TE5 - 03":  [7413.2, 8453.8, 9606.2, 10887.6, 12289.4, 13811.6, 15428.4, 17122.6, 18816.8, 20425.0, 21809.6],
    "TE5 - 04":  [9812.6, 11240.2, 12831.2, 14594.2, 16537.8, 18653.4, 20915.2, 23271.6, 25619.4, 27864.0, 29670.0],
    "TE12 - 05": [12934.4, 14534.0, 16331.4, 18343.8, 20597.0, 23073.8, 25765.6, 28638.0, 31562.0, 34486.0, 37152.0],
    "TE12 - 06": [16374.4, 18498.6, 20889.4, 23589.8, 26574.0, 30014.0, 33626.0, 37582.0, 41710.0, 45752.0, 49450.0],
    "TE12 - 07": [21689.2, 24286.4, 27262.0, 30530.0, 34314.0, 38528.0, 43086.0, 48160.0, 53406.0, 58652.0, 63640.0],
    "TE20 - 08": [25387.2, 28810.0, 32680.0, 37066.0, 41882.0, 47214.0, 52976.0, 59168.0, 65360.0, 71380.0, 76540.0],
    "TE20 - 09": [28036.0, 31906.0, 36206.0, 41194.0, 46784.0, 53062.0, 59942.0, 67940.0, 75680.0, 83420.0, 90300.0],
    "TE55 - 10": [30186.0, 35174.0, 40764.0, 47128.0, 54266.0, 61920.0, 71380.0, 80840.0, 90300.0, 100620.0, 109220.0],
    "TE55 - 11": [33196.0, 38700.0, 44892.0, 51858.0, 59684.0, 67940.0, 78260.0, 88580.0, 98900.0, 110080.0, 119540.0],
    "TE55 - 12": [35604.0, 41452.0, 48160.0, 55642.0, 64500.0, 73960.0, 84280.0, 95460.0, 108360.0, 120400.0, 131580.0],
    "TE55 - 13": [42828.0, 50052.0, 58308.0, 67940.0, 78260.0, 90300.0, 103200.0, 117820.0, 132440.0, 147060.0, 161680.0],
}
R407C = {
    "TE5 - 0.5": [3732.4, 4214.0, 4747.2, 5340.6, 5985.6, 6690.8, 7439.0, 8204.4, 8969.8, 9700.8, 10337.2],
    "TE5 - 01":  [6845.6, 7731.4, 8729.0, 9829.8, 11025.2, 12323.8, 13699.8, 15118.8, 16520.6, 17836.4, 18971.6],
    "TE5 - 02":  [9580.4, 10861.8, 12272.2, 13828.8, 15523.0, 17337.6, 19246.8, 21190.4, 23082.4, 24819.6, 26230.0],
    "TE5 - 03":  [11936.8, 13502.0, 15239.2, 17165.6, 19298.4, 21603.2, 24054.2, 26574.0, 29154.0, 31476.0, 33454.0],
    "TE5 - 04":  [15669.2, 17836.4, 20261.6, 22970.6, 25972.0, 29240.0, 32680.0, 36292.0, 39818.0, 43086.0, 45666.0],
    "TE12 - 05": [16348.6, 18601.8, 21173.2, 24105.8, 27434.0, 31132.0, 35174.0, 39560.0, 44118.0, 48590.0, 52804.0],
    "TE12 - 06": [20278.8, 23245.8, 26660.0, 30530.0, 35002.0, 39990.0, 45580.0, 51600.0, 57964.0, 64500.0, 70520.0],
    "TE12 - 07": [25516.2, 28896.0, 32852.0, 37410.0, 42656.0, 48676.0, 55470.0, 62780.0, 71380.0, 79120.0, 87720.0],
    "TE20 - 08": [37496.0, 42312.0, 47730.0, 53922.0, 61060.0, 68800.0, 77400.0, 86000.0, 95460.0, 104060.0, 111800.0],
    "TE20 - 09": [39388.0, 44548.0, 50482.0, 57190.0, 65360.0, 73960.0, 83420.0, 94600.0, 105780.0, 117820.0, 128140.0],
    "TE55 - 10": [44290.0, 50912.0, 58394.0, 67080.0, 76540.0, 87720.0, 99760.0, 112660.0, 126420.0, 141040.0, 153940.0],
    "TE55 - 11": [48160.0, 55384.0, 63640.0, 73100.0, 83420.0, 95460.0, 108360.0, 122120.0, 137600.0, 152220.0, 166840.0],
    "TE55 - 12": [50998.0, 58652.0, 67080.0, 77400.0, 88580.0, 101480.0, 116100.0, 131580.0, 147920.0, 165120.0, 181460.0],
    "TE55 - 13": [60028.0, 68800.0, 79980.0, 92020.0, 105780.0, 121260.0, 138460.0, 157380.0, 178020.0, 198660.0, 217580.0],
}
R448A_449A = {
    "TE5 - 0.5": [3500.2, 4592.4, 5839.4, 7241.2, 8772.0, 10148.0],
    "TE5 - 01":  [6407.0, 8428.0, 10750.0, 13330.0, 16082.0, 18662.0],
    "TE5 - 02":  [8944.0, 11868.0, 15136.0, 18834.0, 22532.0, 25800.0],
    "TE5 - 03":  [11180.0, 14706.0, 18834.0, 23392.0, 28380.0, 32938.0],
    "TE5 - 04":  [14534.0, 19522.0, 25284.0, 31906.0, 38958.0, 45236.0],
    "TE12 - 05": [17458.0, 22360.0, 28294.0, 35518.0, 43946.0, 52546.0],
    "TE12 - 06": [21672.0, 28208.0, 36292.0, 46182.0, 58050.0, 70434.0],
    "TE12 - 07": [27520.0, 34916.0, 44290.0, 56072.0, 70520.0, 86000.0],
    "TE20 - 08": [37496.0, 49536.0, 64070.0, 81442.0, 100620.0, 119540.0],
    "TE20 - 09": [38614.0, 51084.0, 66908.0, 86860.0, 110940.0, 135880.0],
    "TE55 - 10": [38786.0, 54008.0, 73100.0, 96320.0, 122120.0, 149640.0],
    "TE55 - 11": [42054.0, 58652.0, 79292.0, 104060.0, 132440.0, 160820.0],
    "TE55 - 12": [44376.0, 62006.0, 84194.0, 110940.0, 142760.0, 175440.0],
    "TE55 - 13": [51858.0, 73014.0, 99760.0, 132440.0, 171140.0, 210700.0],
}

# fluido -> (tabela, lista de T.Evap correspondente)
FLUIDOS = [
    ("R22", R22, TEMPS_5C),
    ("R404A", R404A, TEMPS_5C),
    ("R507", R404A, TEMPS_5C),       # Danfoss publica R404A/R507 na mesma tabela
    ("R134a", R134A, TEMPS_5C),
    ("R407C", R407C, TEMPS_5C),
    ("R448A", R448A_449A, TEMPS_10C),
    ("R449A", R448A_449A, TEMPS_10C),  # Danfoss publica R448A/R449A na mesma tabela
]


def _get_id(conn, table, nome_col, nome_val, extra_where=""):
    return conn.execute(
        sa.text(f"SELECT id FROM {table} WHERE {nome_col} = :v {extra_where}"),
        {"v": nome_val},
    ).scalar_one()


def upgrade() -> None:
    conn = op.get_bind()

    fabricante_id = _get_id(conn, "fabricante", "nome", FABRICANTE)
    categoria_id = _get_id(conn, "categoria", "nome", CATEGORIA)

    t_componente = sa.table(
        "componente_tecnico",
        sa.column("categoria_id", sa.Integer),
        sa.column("modelo", sa.String),
        sa.column("codigo_fabricante", sa.String),
        sa.column("fabricante_id", sa.Integer),
        sa.column("conexao_entrada", sa.String),
        sa.column("conexao_saida", sa.String),
        sa.column("capacidade_nominal", sa.Float),
        sa.column("dados_especificos", sa.JSON),
        sa.column("custo", sa.Numeric),
    )

    op.bulk_insert(t_componente, [
        {
            "categoria_id": categoria_id,
            "modelo": modelo,
            "codigo_fabricante": codigo,
            "fabricante_id": fabricante_id,
            "conexao_entrada": conexao_in,
            "conexao_saida": conexao_out,
            "capacidade_nominal": 0,
            "dados_especificos": json.dumps({
                "corpo": corpo,
                "orificio_no": orificio,
                "faixa": "N (-40°C a +10°C)",
                "conexoes_disponiveis_do_corpo": CONEXOES_POR_CORPO[corpo],
                "fonte": FONTE,
            }),
            "custo": 0,
        }
        for modelo, corpo, orificio, codigo, conexao_in, conexao_out in MODELOS
    ])

    ids_por_modelo = dict(conn.execute(
        sa.text(
            "SELECT modelo, id FROM componente_tecnico "
            "WHERE categoria_id = :cat AND fabricante_id = :fab AND modelo = ANY(:modelos)"
        ),
        {"cat": categoria_id, "fab": fabricante_id, "modelos": [m[0] for m in MODELOS]},
    ).all())

    t_performance = sa.table(
        "performance_componente",
        sa.column("componente_id", sa.Integer),
        sa.column("fluido", sa.String),
        sa.column("temp_evaporacao", sa.Integer),
        sa.column("temp_condensacao", sa.Integer),
        sa.column("capacidade_kcalh", sa.Float),
        sa.column("capacidade_min_kcalh", sa.Float),
    )

    linhas = []
    for modelo, _corpo, _orificio, _codigo, _in, _out in MODELOS:
        componente_id = ids_por_modelo[modelo]
        for fluido, tabela, temps in FLUIDOS:
            for temp, cap in zip(temps, tabela[modelo]):
                linhas.append({
                    "componente_id": componente_id,
                    "fluido": fluido,
                    "temp_evaporacao": temp,
                    "temp_condensacao": 45,
                    "capacidade_kcalh": cap,
                    "capacidade_min_kcalh": round(cap * 0.25, 2),
                })
    op.bulk_insert(t_performance, linhas)


def downgrade() -> None:
    conn = op.get_bind()
    categoria_id = _get_id(conn, "categoria", "nome", CATEGORIA)
    fabricante_id = _get_id(conn, "fabricante", "nome", FABRICANTE)
    conn.execute(
        sa.text(
            "DELETE FROM componente_tecnico "
            "WHERE categoria_id = :cat AND fabricante_id = :fab AND modelo = ANY(:modelos)"
        ),
        {"cat": categoria_id, "fab": fabricante_id, "modelos": [m[0] for m in MODELOS]},
    )
    # performance_componente cai junto via ON DELETE CASCADE
