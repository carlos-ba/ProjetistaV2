"""Semeia dados reais do kit de montagem: 91 perfis MBP Isoblock + selante/rebite/parafuso+bucha genéricos

Terceira parte da frente do kit de montagem (0027 criou perfil_metalico,
0028 criou selante_montagem/rebite/parafuso_bucha + os 2 campos de
configuracao_montagem). Essa segurava dado real de propósito até a
lógica de seleção/cálculo estar pronta e testada (ver
DESIGN_KIT_MONTAGEM_2026-09-01.md) — agora está.

Perfis: mesmos 91 registros já validados localmente pelo importador
(backend/scripts/importar_perfis_metalicos.py) contra a planilha real da
MBP Isoblock — embutidos aqui como dado literal (não plugamos
DATABASE_URL de produção neste ambiente por segurança, então a migration
carrega o dado em vez do importador rodar direto contra produção).

Selante/rebite/parafuso+bucha: cadastro simples, fabricante genérico (sem
fornecedor específico definido ainda) — confirmado com o usuário
2026-09-01. Mesmo padrão de semear dado real direto na migration já usado
pra embalagem_fluido (0024).

Revision ID: 0029
Revises: 0028
Create Date: 2026-09-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None

FABRICANTE_PERFIS = "MBP Isoblock"
FABRICANTE_GENERICO = "Genérico"

PERFIS_MBP_ISOBLOCK = [
    # codigo_fabricante, tipo, medida_1_mm, medida_2_mm, medida_3_mm, comprimento_mm, descricao_original
    ("PI122D0D000H31", "Ângulo Interno", 40, 40, None, 3000, "P ANG INT       APP 0,50 DIM         ,40x40x3000 V10"),
    ("PI02285D0A0001", "Ângulo Externo", 40, 25, None, 3000, "P ANG EXT       APP 0,50 DIM         ,40x25x3000 V10"),
    ("PI022A1A100H30", "Ângulo Externo", 30, 30, None, 3000, "P ANG EXT       APP 0,50 DIM         ,30x30x3000 S/V"),
    ("PI122A1A100H30", "Ângulo Interno", 30, 30, None, 3000, "P ANG INT      APP 0,50 DIM         ,30x30x3000 S/V"),
    ("PI022D0D000H31", "Ângulo Externo", 40, 40, None, 3000, "P ANG EXT       APP 0,50 DIM         ,40x40x3000 V10"),
    ("PI02200D0G1H31", "Ângulo Externo", 40, 50, None, 3000, "P ANG EXT       APP 0,50 DIM       ,40x50x3000 V10"),
    ("PI12200D0I3H31", "Ângulo Interno", 40, 60, None, 3000, "P ANG INT       APP 0,50 DIM       ,40x60x3000 V10"),
    ("PI12200D0K2H31", "Ângulo Interno", 40, 70, None, 3000, "P ANG INT       APP 0,50 DIM       ,40x70x3000 V10"),
    ("PI02200D0K2H31", "Ângulo Externo", 40, 70, None, 3000, "P ANG EXT       APP 0,50 DIM       ,40x70x3000 V10"),
    ("PI12200D0M8H31", "Ângulo Interno", 40, 90, None, 3000, "P ANG INT       APP 0,50 DIM       ,40x90x3000 V10"),
    ("PI022D0M800H31", "Ângulo Externo", 40, 90, None, 3000, "P ANG EXT       APP 0,50 DIM       ,40x90x3000 V10"),
    ("PI12200D006H31", "Ângulo Interno", 40, 100, None, 3000, "P ANG INT       APP 0,50 DIM      ,40x100x3000 V10"),
    ("PI022D00600H30", "Ângulo Externo", 40, 100, None, 3000, "P ANG EXT       APP 0,50 DIM      ,40x100x3000 V10"),
    ("PI122D01700H31", "Ângulo Interno", 40, 110, None, 3000, "P ANG INT       APP 0,50 DIM      ,40x110x3000 V10"),
    ("PI022D01700H31", "Ângulo Externo", 40, 110, None, 3000, "P ANG EXT       APP 0,50 DIM      ,40x110x3000 V10"),
    ("PI122D02600H31", "Ângulo Interno", 40, 120, None, 3000, "P ANG INT       APP 0,50 DIM      ,40x120x3000 V10"),
    ("PI022D02600H31", "Ângulo Externo", 40, 120, None, 3000, "P ANG EXT      APP 0,50 DIM      ,40x120x3000 V10"),
    ("PI12200D035H31", "Ângulo Interno", 40, 140, None, 3000, "P ANG INT       APP 0,50 DIM       ,40x140x3000 V10"),
    ("PI022D03500H31", "Ângulo Externo", 40, 140, None, 3000, "P ANG EXT       APP 0,50 DIM      ,40x140x3000 V10"),
    ("PI02200D038H31", "Ângulo Externo", 40, 150, None, 3000, "P ANG EXT       APP 0,50 DIM      ,40x150x3000 V10"),
    ("PI02200D042H31", "Ângulo Externo", 40, 160, None, 3000, "P ANG EXT       APP 0,50 DIM      ,40x160x3000 V10"),
    ("PI122D05100H31", "Ângulo Interno", 40, 180, None, 3000, "P ANG INT      APP 0,50 DIM       ,40x180x3000 V10"),
    ("PI022D05100H31", "Ângulo Externo", 40, 180, None, 3000, "P ANG EXT      APP 0,50 DIM       ,40x180x3000 V10"),
    ("PI122D05600H31", "Ângulo Interno", 40, 190, None, 3000, "P ANG INT      APP 0,50 DIM       ,40x190x3000 V10"),
    ("PI022D05600H31", "Ângulo Externo", 40, 190, None, 3000, "P ANG EXT       APP 0,50 DIM       ,40x190x3000 V10"),
    ("PI022D05900H31", "Ângulo Externo", 40, 200, None, 3000, "P ANG EXT       APP 0,50 DIM       ,40x200x3000 V10"),
    ("PI022D07000H31", "Ângulo Externo", 40, 220, None, 3000, "P ANG EXT       APP 0,50 DIM       ,40x220x3000 V10"),
    ("PI022D07700H31", "Ângulo Externo", 40, 240, None, 3000, "P ANG EXT       APP 0,50 DIM       ,40x240x3000 V10"),
    ("PI122K2K200H31", "Ângulo Interno", 70, 70, None, 3000, "P ANG INT       APP 0,50 DIM       ,70x70x3000 V10"),
    ("PI022K2K200H31", "Ângulo Externo", 70, 70, None, 3000, "P ANG EXT       APP 0,50 DIM       ,70x70x3000 V10"),
    ("PI022K23500H31", "Ângulo Externo", 70, 140, None, 3000, "P ANG EXT       APP 0,50 DIM       ,70x140x3000 V10"),
    ("PI022K24200H31", "Ângulo Externo", 70, 160, None, 3000, "P ANG EXT       APP 0,50 DIM       ,70x160x3000 V10"),
    ("PI022K25600H31", "Ângulo Externo", 70, 190, None, 3000, "P ANG EXT       APP 0,50 DIM       ,70x190x3000 V10"),
    ("PI022K27700H31", "Ângulo Externo", 70, 240, None, 3000, "P ANG EXT       APP 0,50 DIM       ,70x240x3000 V10"),
    ("PI022172600H31", "Ângulo Externo", 110, 120, None, 3000, "P ANG EXT       APP 0,50 DIM       ,110x120x3000 V10"),
    ("PI022263500H31", "Ângulo Externo", 120, 140, None, 3000, "P ANG EXT       APP 0,50 DIM       ,120x140x3000 V10"),
    ("PI022385600H31", "Ângulo Externo", 150, 190, None, 3000, "P ANG EXT       APP 0,50 DIM       ,150x190x3000 V10"),
    ("PI022423800J21", "Ângulo Externo", 160, 150, None, 3000, "P ANG EXT       APP 0,50 DIM       ,160x150x3000 V10"),
    ("PI722G10000H31", "Liso", 50, None, None, 3000, "P LISO    APP 0,50 DIM       50x3000 V10"),
    ("PI722L70000H31", "Liso", 80, None, None, 3000, "P LISO    APP 0,50 DIM       80x3000 V10"),
    ("PI722000006H31", "Liso", 100, None, None, 3000, "P LISO    APP 0,50 DIM       100x3000 V10"),
    ("PI722170000H31", "Liso", 110, None, None, 3000, "P LISO    APP 0,50 DIM       110x3000 V10"),
    ("PI72230P000H31", "Liso", 130, None, None, 3000, "P LISO    APP 0,50 DIM       130x3000 V10"),
    ("PI722000038H31", "Liso", 150, None, None, 3000, "P LISO    APP 0,50 DIM       150x3000 V10"),
    ("PI722420100H31", "Liso", 160, None, None, 3000, "P LISO    APP 0,50 DIM       160x3000 V10"),
    ("PI722460000H31", "Liso", 170, None, None, 3000, "P LISO    APP 0,50 DIM       170x3000 V10"),
    ("PI722000051H31", "Liso", 180, None, None, 3000, "P  LISO    APP 0,50 DIM       180x3000 V10"),
    ("PI722590000H31", "Liso", 200, None, None, 3000, "P LISO    APP 0,50 DIM       200x3000 V10"),
    ("PI722700000H31", "Liso", 220, None, None, 3000, "P LISO    APP 0,50 DIM       220x3000 V10"),
    ("PI722750000H31", "Liso", 230, None, None, 3000, "P LISO    APP 0,50 DIM       230x3000 V10"),
    ("PI722960000H31", "Liso", 280, None, None, 3000, "P LISO    APP 0,50 DIM       280x3000 V10"),
    ("PIK2263G163H31", "U", 20, 50, 20, 3000, "P U      APP 0,50 DIM       ,20x50x20x3000 V10"),
    ("PIK2263K263H31", "U", 20, 70, 20, 3000, "P U      APP 0,50 DIM       ,20x70x20x3000 V10"),
    ("PIK22630663H31", "U", 20, 100, 20, 3000, "P U      APP 0,50 DIM       ,20x100x20x3000 V10"),
    ("PIK22D0G1D0H31", "U", 40, 50, 40, 3000, "P U      APP 0,50 DIM       ,40x50x40x3000 V10"),
    ("PIK22D0K2D0H31", "U", 40, 70, 40, 3000, "P U      APP 0,50 DIM       ,40x70x40x3000 V10"),
    ("PIK22D0K8D0H31", "U", 40, 75, 40, 3000, "P U      APP 0,50 DIM       ,40x75x40x3000 V10"),
    ("PIK22D0M8D0H31", "U", 40, 90, 40, 3000, "P U      APP 0,50 DIM       ,40x90x40x3000 V10"),
    ("PIK22D006D0H31", "U", 40, 100, 40, 3000, "P U       APP 0,50 DIM       ,40x100x40x3000 V10"),
    ("PIK22D026D0H31", "U", 40, 120, 40, 3000, "P U       APP 0,50 DIM       ,40x120x40x3000 V10"),
    ("PIK22D038D0H31", "U", 40, 150, 40, 3000, "P U       APP 0,50 DIM       ,40x150x40x3000 V10"),
    ("PIK22D042D0H31", "U", 40, 160, 40, 3000, "P U       APP 0,50 DIM       ,40x160x40x3000 V10"),
    ("PIK22D059D0H31", "U", 40, 200, 40, 3000, "P U       APP 0,50 DIM       ,40x200x40x3000 V10"),
    ("PIK22G1G100H31", "U", 50, 50, 50, 3000, "P U       APP 0,50 DIM       ,50x50x50x3000 V10"),
    ("PIN22D063D0H31", "Z", 40, 20, 40, 3000, "P Z       APP 0,50 DIM       ,40x20x40x3000 V10"),
    ("PIN22D085D0H31", "Z", 40, 25, 40, 3000, "P Z       APP 0,50 DIM       ,40x25x40x3000 V10"),
    ("PIN22D0A1D0H31", "Z", 40, 30, 40, 3000, "P Z       APP 0,50 DIM       ,40x30x40x3000 V10"),
    ("PIN22D0G1D0H30", "Z", 40, 50, 40, 3000, "P Z       APP 0,50 DIM       ,40x50x40x3000 V10"),
    ("PIN22D0I3D0H31", "Z", 40, 60, 40, 3000, "P Z       APP 0,50 DIM       ,40x60x40x3000 V10"),
    ("PIN22D0K2D0H31", "Z", 40, 70, 40, 3000, "P Z       APP 0,50 DIM       ,40x70x40x3000 V10"),
    ("PIN22D0L7D0H31", "Z", 40, 80, 40, 3000, "P Z       APP 0,50 DIM       ,40x80x40x3000 V10"),
    ("PIN22D0M8D0H31", "Z", 40, 90, 40, 3000, "P Z       APP 0,50 DIM       ,40x90x40x3000 V11"),
    ("PIN22D006D0H31", "Z", 40, 100, 40, 3000, "P Z       APP 0,50 DIM       ,40x100x40x3000 V10"),
    ("PIN22D026D0H31", "Z", 40, 120, 40, 3000, "P Z       APP 0,50 DIM       ,40x120x40x3000 V10"),
    ("PIN22D030D0H31", "Z", 40, 130, 40, 3000, "P Z       APP 0,50 DIM       ,40x130x40x3000 V10"),
    ("PIN22D035D0H31", "Z", 40, 140, 40, 3000, "P Z       APP 0,50 DIM       ,40x140x40x3000 V10"),
    ("PIN22D038D0H31", "Z", 40, 150, 40, 3000, "P Z       APP 0,50 DIM       ,40x150x40x3000 V10"),
    ("PIN22D059D0H31", "Z", 40, 200, 40, 3000, "P Z       APP 0,50 DIM       ,40x200x40x3000 V10"),
    ("PIN22D063K2H31", "Z", 40, 20, 70, 3000, "P Z       APP 0,50 DIM       ,40x20x70x3000 V10"),
    ("PIN22D0A1K2H31", "Z", 40, 30, 70, 3000, "P Z       APP 0,50 DIM       ,40x30x70x3000 V10"),
    ("PIN22D0G1K2H31", "Z", 40, 50, 70, 3000, "P Z       APP 0,50 DIM       ,40x50x70x3000 V10"),
    ("PIN22D0K2K2H31", "Z", 40, 70, 70, 3000, "P Z       APP 0,50 DIM       ,40x70x70x3000 V10"),
    ("PIN22D0L7K2H31", "Z", 40, 80, 70, 3000, "P Z       APP 0,50 DIM       ,40x80x70x3000 V10"),
    ("PIN22D006K2H31", "Z", 40, 100, 70, 3000, "P Z       APP 0,50 DIM       ,40x100x70x3000 V10"),
    ("PIN22D030K2H31", "Z", 40, 130, 70, 3000, "P Z       APP 0,50 DIM       ,40x130x70x3000 V10"),
    ("PIN22D038K2H31", "Z", 40, 150, 70, 3000, "P Z       APP 0,50 DIM       ,40x150x70x3000 V11"),
    ("PIN19K2G1D0H31", "Z", 70, 50, 40, 3000, "P Z       APP 0,50 DIM       ,70x50x40x3000 V10"),
    ("PIN22K206D0H31", "Z", 70, 100, 40, 3000, "P Z       APP 0,50 DIM       ,70x100x40x3000 V10"),
    ("PIN22K238D0H31", "Z", 70, 150, 40, 3000, "P Z       APP 0,50 DIM       ,70x150x40x3000 V10"),
    ("PIN22K259D0H31", "Z", 70, 200, 40, 3000, "P Z       APP 0,50 DIM       ,70x200x40x3000 V10"),
    ("PIN2242G1K2H31", "Z", 160, 50, 70, 3000, "P Z       APP 0,50 DIM       160x50x70x3000 V10"),
]

# Cadastro simples, fabricante genérico (sem fornecedor definido ainda) — confirmado com o usuário 2026-09-01.
SELANTE_CODIGO = "SEL-PU-001"
SELANTE_DESCRICAO = "Selante PU Câmara Fria (Sikaflex)"
REBITE_CODIGO = "REB-312-001"
REBITE_DESCRICAO = "Rebite Branco Mod 312"
PARAFUSO_CODIGO = "PB-N8-001"
PARAFUSO_DESCRICAO = "Cj Parafuso+Bucha nº 8"


def _get_or_create_fabricante_id(conn, nome: str) -> int:
    conn.execute(
        sa.text("INSERT INTO fabricante (nome) VALUES (:nome) ON CONFLICT (nome) DO NOTHING"),
        {"nome": nome},
    )
    return conn.execute(
        sa.text("SELECT id FROM fabricante WHERE nome = :nome"), {"nome": nome}
    ).scalar_one()


def upgrade() -> None:
    conn = op.get_bind()

    fabricante_perfis_id = _get_or_create_fabricante_id(conn, FABRICANTE_PERFIS)
    t_perfil = sa.table(
        "perfil_metalico",
        sa.column("fabricante_id", sa.Integer),
        sa.column("codigo_fabricante", sa.String),
        sa.column("tipo", sa.String),
        sa.column("medida_1_mm", sa.Integer),
        sa.column("medida_2_mm", sa.Integer),
        sa.column("medida_3_mm", sa.Integer),
        sa.column("comprimento_mm", sa.Integer),
        sa.column("descricao_original", sa.String),
    )
    op.bulk_insert(t_perfil, [
        {
            "fabricante_id": fabricante_perfis_id,
            "codigo_fabricante": cod,
            "tipo": tipo,
            "medida_1_mm": m1,
            "medida_2_mm": m2,
            "medida_3_mm": m3,
            "comprimento_mm": compr,
            "descricao_original": desc,
        }
        for cod, tipo, m1, m2, m3, compr, desc in PERFIS_MBP_ISOBLOCK
    ])

    fabricante_generico_id = _get_or_create_fabricante_id(conn, FABRICANTE_GENERICO)

    t_selante = sa.table(
        "selante_montagem",
        sa.column("fabricante_id", sa.Integer),
        sa.column("codigo_fabricante", sa.String),
        sa.column("descricao", sa.String),
        sa.column("tipo_embalagem", sa.String),
    )
    op.bulk_insert(t_selante, [{
        "fabricante_id": fabricante_generico_id,
        "codigo_fabricante": SELANTE_CODIGO,
        "descricao": SELANTE_DESCRICAO,
        "tipo_embalagem": "aplicador",
    }])

    t_rebite = sa.table(
        "rebite",
        sa.column("fabricante_id", sa.Integer),
        sa.column("codigo_fabricante", sa.String),
        sa.column("descricao", sa.String),
    )
    op.bulk_insert(t_rebite, [{
        "fabricante_id": fabricante_generico_id,
        "codigo_fabricante": REBITE_CODIGO,
        "descricao": REBITE_DESCRICAO,
    }])

    t_parafuso = sa.table(
        "parafuso_bucha",
        sa.column("fabricante_id", sa.Integer),
        sa.column("codigo_fabricante", sa.String),
        sa.column("descricao", sa.String),
    )
    op.bulk_insert(t_parafuso, [{
        "fabricante_id": fabricante_generico_id,
        "codigo_fabricante": PARAFUSO_CODIGO,
        "descricao": PARAFUSO_DESCRICAO,
    }])


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "DELETE FROM perfil_metalico WHERE codigo_fabricante = ANY(:codigos)"
    ), {"codigos": [cod for cod, *_ in PERFIS_MBP_ISOBLOCK]})
    conn.execute(sa.text("DELETE FROM selante_montagem WHERE codigo_fabricante = :cod"), {"cod": SELANTE_CODIGO})
    conn.execute(sa.text("DELETE FROM rebite WHERE codigo_fabricante = :cod"), {"cod": REBITE_CODIGO})
    conn.execute(sa.text("DELETE FROM parafuso_bucha WHERE codigo_fabricante = :cod"), {"cod": PARAFUSO_CODIGO})
