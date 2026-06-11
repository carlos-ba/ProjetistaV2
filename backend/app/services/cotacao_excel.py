"""
Gera planilha Excel de cotação vinculada a um fornecedor.

A planilha contém o código da cotação embutido (cabeçalho visível + propriedade
do documento) para que, ao ser devolvida preenchida, o sistema identifique
exatamente de qual cotação/fornecedor se trata (Fase 2 — importação).

Células travadas: tudo, exceto as colunas que o fornecedor preenche:
  G  Preço Unitário (R$)
  I  Marca/Modelo ofertado
  J  Prazo de entrega (dias)
  K  Observações do fornecedor
"""
from __future__ import annotations
from io import BytesIO
from datetime import datetime, timedelta

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, Protection
from openpyxl.utils import get_column_letter

COR_HEADER    = "1E3A5F"
COR_EQUIP     = "EBF5FB"
COR_MATERIAL  = "FDFEFE"
COR_PREENCHER = "FFFACD"
COR_TOTAL     = "EAF2FF"
COR_RODAPE    = "F4F6F6"
COR_CODIGO    = "FFE8CC"

BORDA_FINA = Border(
    left=Side(style="thin", color="CCCCCC"),
    right=Side(style="thin", color="CCCCCC"),
    top=Side(style="thin", color="CCCCCC"),
    bottom=Side(style="thin", color="CCCCCC"),
)

DESBLOQUEADA = Protection(locked=False)

# Colunas que o fornecedor preenche (índices 1-based)
COLUNAS_EDITAVEIS = {7, 9, 10, 11}

COLUNAS = [
    ("Código",                  8),
    ("Tipo",                   13),
    ("Descrição",              40),
    ("Detalhe / Esp. Técnica", 28),
    ("Qtde",                    7),
    ("Un",                      6),
    ("Preço Unit. (R$)",       15),
    ("Total (R$)",             13),
    ("Marca/Modelo ofertado",  22),
    ("Prazo (dias)",           10),
    ("Obs. Fornecedor",        20),
]
ULT_COL = get_column_letter(len(COLUNAS))   # K


def _celula(ws, linha, col, valor, negrito=False, cor_fundo=None,
            cor_texto="000000", alinhamento="left", tamanho=10, italico=False):
    c = ws.cell(row=linha, column=col, value=valor)
    c.font = Font(name="Arial", bold=negrito, italic=italico,
                  color=cor_texto, size=tamanho)
    if cor_fundo:
        c.fill = PatternFill("solid", fgColor=cor_fundo)
    c.alignment = Alignment(horizontal=alinhamento, vertical="center")
    c.border = BORDA_FINA
    return c


def gerar_planilha_cotacao_v2(
    codigo: str,
    itens: list[dict],
    fornecedor_nome: str,
    fornecedor_contato: str = "",
    nome_projeto: str = "Projeto",
    nome_cliente: str = "",
    validade_dias: int = 30,
) -> bytes:
    """
    Cada item: {ref_id, tipo, descricao, detalhe, qtde, unidade}
    Retorna bytes do .xlsx.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Cotação"
    ws.sheet_view.showGridLines = False

    # Código embutido como propriedade do documento (leitura na importação)
    wb.properties.subject = codigo
    wb.properties.keywords = f"cotacao:{codigo}"

    # ── Cabeçalho ─────────────────────────────────────────────────────────
    ws.merge_cells(f"A1:{ULT_COL}1")
    c = ws.cell(row=1, column=1, value="PLANILHA DE COTAÇÃO — MATERIAIS E EQUIPAMENTOS")
    c.font = Font(name="Arial", bold=True, size=14, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=COR_HEADER)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    # Linha do código — destaque (campo-chave da identificação no retorno)
    ws.merge_cells("A2:C2")
    cc = ws.cell(row=2, column=1, value=f"CÓDIGO DA COTAÇÃO: {codigo}")
    cc.font = Font(name="Arial", bold=True, size=11, color="8B4513")
    cc.fill = PatternFill("solid", fgColor=COR_CODIGO)
    cc.alignment = Alignment(horizontal="left", vertical="center")

    ws.merge_cells(f"D2:{ULT_COL}2")
    emissao = datetime.now()
    validade = emissao + timedelta(days=validade_dias)
    cd = ws.cell(
        row=2, column=4,
        value=(f"Fornecedor: {fornecedor_nome}"
               + (f" ({fornecedor_contato})" if fornecedor_contato else "")
               + f" | Emissão: {emissao.strftime('%d/%m/%Y')}"
               + f" | Validade solicitada: {validade.strftime('%d/%m/%Y')}"),
    )
    cd.font = Font(name="Arial", size=9, color="555555")
    cd.fill = PatternFill("solid", fgColor=COR_CODIGO)
    cd.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[2].height = 20

    ws.merge_cells(f"A3:{ULT_COL}3")
    info = f"Projeto: {nome_projeto}"
    if nome_cliente:
        info += f" | Cliente: {nome_cliente}"
    c3 = ws.cell(row=3, column=1, value=info)
    c3.font = Font(name="Arial", size=9, color="555555", italic=True)
    c3.fill = PatternFill("solid", fgColor="EBF2FF")
    c3.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[3].height = 16

    ws.merge_cells(f"A4:{ULT_COL}4")
    inst = ws.cell(
        row=4, column=1,
        value=("INSTRUÇÕES: Preencha apenas as colunas em amarelo — Preço Unitário, "
               "Marca/Modelo ofertado, Prazo e Observações. As demais células estão protegidas. "
               "NÃO altere o código da cotação."),
    )
    inst.font = Font(name="Arial", size=8, color="8B4513", bold=True)
    inst.fill = PatternFill("solid", fgColor=COR_PREENCHER)
    inst.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[4].height = 16

    # ── Cabeçalho de colunas ──────────────────────────────────────────────
    LINHA_HDR = 5
    for col_idx, (titulo, largura) in enumerate(COLUNAS, 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = largura
        editavel = col_idx in COLUNAS_EDITAVEIS
        c = ws.cell(row=LINHA_HDR, column=col_idx, value=titulo)
        c.font = Font(name="Arial", bold=True, size=9,
                      color="000000" if editavel else "FFFFFF")
        c.fill = PatternFill("solid", fgColor=COR_PREENCHER if editavel else COR_HEADER)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDA_FINA
    ws.row_dimensions[LINHA_HDR].height = 26

    # ── Itens ─────────────────────────────────────────────────────────────
    lin = LINHA_HDR + 1
    primeira_linha_item = lin
    for item in itens:
        cor = COR_EQUIP if item.get("tipo") == "Equipamento" else COR_MATERIAL

        _celula(ws, lin, 1, str(item.get("ref_id") or "-"), cor_fundo=cor,
                alinhamento="center", tamanho=8, cor_texto="888888")
        _celula(ws, lin, 2, item.get("tipo", ""), cor_fundo=cor, tamanho=9)
        _celula(ws, lin, 3, item.get("descricao", ""), cor_fundo=cor, negrito=True, tamanho=9)
        _celula(ws, lin, 4, item.get("detalhe", ""), cor_fundo=cor, tamanho=8, cor_texto="555555")
        _celula(ws, lin, 5, item.get("qtde", 1), cor_fundo=cor, alinhamento="center", tamanho=9)
        _celula(ws, lin, 6, item.get("unidade", "un"), cor_fundo=cor, alinhamento="center", tamanho=9)

        # G — preço unitário (editável)
        cg = ws.cell(row=lin, column=7)
        cg.fill = PatternFill("solid", fgColor=COR_PREENCHER)
        cg.border = BORDA_FINA
        cg.alignment = Alignment(horizontal="right", vertical="center")
        cg.number_format = "#,##0.00"
        cg.protection = DESBLOQUEADA

        # H — total (fórmula, travada)
        ch = ws.cell(row=lin, column=8,
                     value=f'=IF(G{lin}="","",E{lin}*G{lin})')
        ch.fill = PatternFill("solid", fgColor=COR_TOTAL)
        ch.border = BORDA_FINA
        ch.alignment = Alignment(horizontal="right", vertical="center")
        ch.number_format = "#,##0.00"
        ch.font = Font(name="Arial", bold=True, size=9)

        # I, J, K — marca/modelo, prazo, obs (editáveis)
        for col in (9, 10, 11):
            ce = ws.cell(row=lin, column=col)
            ce.fill = PatternFill("solid", fgColor=COR_PREENCHER)
            ce.border = BORDA_FINA
            ce.alignment = Alignment(horizontal="left", vertical="center")
            ce.protection = DESBLOQUEADA
            if col == 10:
                ce.alignment = Alignment(horizontal="center", vertical="center")

        ws.row_dimensions[lin].height = 18
        lin += 1

    # ── Total geral ───────────────────────────────────────────────────────
    ws.merge_cells(f"A{lin}:G{lin}")
    ct = ws.cell(row=lin, column=1, value="TOTAL GERAL")
    ct.font = Font(name="Arial", bold=True, size=10, color="FFFFFF")
    ct.fill = PatternFill("solid", fgColor=COR_HEADER)
    ct.alignment = Alignment(horizontal="right", vertical="center")

    tc = ws.cell(row=lin, column=8, value=f"=SUM(H{primeira_linha_item}:H{lin - 1})")
    tc.fill = PatternFill("solid", fgColor="D6EAF8")
    tc.font = Font(name="Arial", bold=True, size=11, color="1E3A5F")
    tc.alignment = Alignment(horizontal="right", vertical="center")
    tc.number_format = 'R$ #,##0.00'
    tc.border = BORDA_FINA
    ws.row_dimensions[lin].height = 24

    # ── Rodapé ────────────────────────────────────────────────────────────
    lin += 2
    ws.merge_cells(f"A{lin}:{ULT_COL}{lin}")
    rod = ws.cell(
        row=lin, column=1,
        value=(f"* Cotação {codigo} gerada automaticamente. "
               "Os preços informados são de responsabilidade do fornecedor. "
               "Devolva este arquivo preenchido sem alterar sua estrutura."),
    )
    rod.font = Font(name="Arial", size=7, color="999999", italic=True)
    rod.fill = PatternFill("solid", fgColor=COR_RODAPE)
    rod.alignment = Alignment(horizontal="left", vertical="center")

    # ── Proteção da planilha ──────────────────────────────────────────────
    # Tudo travado por padrão; apenas células marcadas com locked=False editáveis
    ws.protection.sheet = True
    ws.protection.formatColumns = False
    ws.protection.formatRows = False

    ws.freeze_panes = f"A{primeira_linha_item}"

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
