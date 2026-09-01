from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.matching import norm
from app.database.session import get_db
from app.models.apelido_fornecedor_item import ApelidoFornecedorItem
from app.models.cotacao import Fornecedor, Cotacao, CotacaoItem
from app.schemas.auth import UserOut
from app.schemas.cotacao import (
    FornecedorCreate, FornecedorUpdate, FornecedorOut,
    CotacaoCreate, CotacaoOut, CotacaoComItens,
)
from app.services.auth import get_current_user, get_empresa_atual
from app.services.cotacao_excel import gerar_planilha_cotacao_v2
from app.services.cotacao_import import extrair_codigo, ler_itens_planilha, casar_itens
from app.services.cotacao_pdf import analisar_pdf_cotacao

router = APIRouter(prefix="/api/v1/cotacoes", tags=["cotacoes"])


# ── Fornecedores ────────────────────────────────────────────────────────────

@router.post("/fornecedores", response_model=FornecedorOut, status_code=status.HTTP_201_CREATED)
async def criar_fornecedor(
    payload: FornecedorCreate,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    fornecedor = Fornecedor(owner_id=usuario.id, empresa_id=empresa_id, **payload.model_dump())
    db.add(fornecedor)
    await db.commit()
    await db.refresh(fornecedor)
    return fornecedor


@router.get("/fornecedores", response_model=list[FornecedorOut])
async def listar_fornecedores(
    incluir_inativos: bool = False,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    stmt = select(Fornecedor).where(Fornecedor.empresa_id == empresa_id)
    if not incluir_inativos:
        stmt = stmt.where(Fornecedor.ativo.is_(True))
    result = await db.execute(stmt.order_by(Fornecedor.nome))
    return result.scalars().all()


@router.patch("/fornecedores/{fornecedor_id}", response_model=FornecedorOut)
async def atualizar_fornecedor(
    fornecedor_id: int,
    payload: FornecedorUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    fornecedor = await _obter_fornecedor(db, fornecedor_id, empresa_id)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(fornecedor, campo, valor)
    await db.commit()
    await db.refresh(fornecedor)
    return fornecedor


@router.delete("/fornecedores/{fornecedor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def desativar_fornecedor(
    fornecedor_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    """Desativa (soft delete) — preserva o histórico de cotações."""
    fornecedor = await _obter_fornecedor(db, fornecedor_id, empresa_id)
    fornecedor.ativo = False
    await db.commit()
    return None


async def _obter_fornecedor(db: AsyncSession, fornecedor_id: int, empresa_id) -> Fornecedor:
    result = await db.execute(
        select(Fornecedor).where(
            Fornecedor.id == fornecedor_id,
            Fornecedor.empresa_id == empresa_id,
        )
    )
    fornecedor = result.scalar_one_or_none()
    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    return fornecedor


# ── Cotações ────────────────────────────────────────────────────────────────

async def _gerar_codigo(db: AsyncSession, fornecedor_id: int) -> str:
    ano = datetime.now().year
    result = await db.execute(
        select(func.count(Cotacao.id)).where(
            func.extract("year", Cotacao.created_at) == ano
        )
    )
    seq = (result.scalar() or 0) + 1
    return f"COT-{ano}-{seq:04d}-F{fornecedor_id:03d}"


@router.post("", response_model=CotacaoOut, status_code=status.HTTP_201_CREATED)
async def criar_cotacao(
    payload: CotacaoCreate,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    if not payload.itens:
        raise HTTPException(status_code=422, detail="A cotação precisa ter ao menos um item")

    await _obter_fornecedor(db, payload.fornecedor_id, empresa_id)
    codigo = await _gerar_codigo(db, payload.fornecedor_id)

    cotacao = Cotacao(
        codigo=codigo,
        owner_id=usuario.id,
        empresa_id=empresa_id,
        fornecedor_id=payload.fornecedor_id,
        projeto_id=payload.projeto_id,
        nome_projeto=payload.nome_projeto,
        validade_dias=payload.validade_dias,
        observacoes=payload.observacoes,
        status="rascunho",
    )
    db.add(cotacao)
    await db.flush()

    for item in payload.itens:
        db.add(CotacaoItem(cotacao_id=cotacao.id, **item.model_dump()))

    await db.commit()
    await db.refresh(cotacao)
    return cotacao


@router.get("", response_model=list[CotacaoOut])
async def listar_cotacoes(
    fornecedor_id: int | None = None,
    projeto_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    stmt = select(Cotacao).where(Cotacao.empresa_id == empresa_id)
    if fornecedor_id:
        stmt = stmt.where(Cotacao.fornecedor_id == fornecedor_id)
    if projeto_id:
        stmt = stmt.where(Cotacao.projeto_id == projeto_id)
    result = await db.execute(stmt.order_by(Cotacao.created_at.desc()))
    return result.scalars().all()


@router.get("/{cotacao_id}", response_model=CotacaoComItens)
async def obter_cotacao(
    cotacao_id: UUID,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    return await _obter_cotacao_com_itens(db, cotacao_id, empresa_id)


@router.get("/{cotacao_id}/excel")
async def baixar_excel_cotacao(
    cotacao_id: UUID,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    cotacao = await _obter_cotacao_com_itens(db, cotacao_id, empresa_id)

    result = await db.execute(
        select(Fornecedor).where(Fornecedor.id == cotacao.fornecedor_id)
    )
    fornecedor = result.scalar_one()

    itens = [
        {
            "ref_id": i.ref_id,
            "tipo": i.tipo_item,
            "descricao": i.descricao,
            "detalhe": i.detalhe or "",
            "qtde": float(i.qtde),
            "unidade": i.unidade,
            "qtde_metros": float(i.qtde_metros) if i.qtde_metros else None,
        }
        for i in cotacao.itens
    ]

    xlsx = gerar_planilha_cotacao_v2(
        codigo=cotacao.codigo,
        itens=itens,
        fornecedor_nome=fornecedor.nome,
        fornecedor_contato=fornecedor.contato or fornecedor.telefone or "",
        nome_projeto=cotacao.nome_projeto or "Projeto",
        validade_dias=cotacao.validade_dias,
    )

    # Marca como enviada no primeiro download
    if cotacao.status == "rascunho":
        cotacao.status = "enviada"
        await db.commit()

    filename = f"{cotacao.codigo}.xlsx"
    return Response(
        content=xlsx,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{cotacao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancelar_cotacao(
    cotacao_id: UUID,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    """Cancela a cotação (soft) — preserva o registro para o histórico."""
    cotacao = await _obter_cotacao_com_itens(db, cotacao_id, empresa_id)
    cotacao.status = "cancelada"
    await db.commit()
    return None


# ── Importação da planilha devolvida (Fase 2) ──────────────────────────────

@router.post("/importar/analisar")
async def analisar_planilha_devolvida(
    arquivo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    """
    Lê a planilha devolvida pelo fornecedor e retorna o relatório de conferência.
    NADA é gravado — o usuário revisa e confirma no passo seguinte.
    """
    if not arquivo.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=422, detail="Envie um arquivo Excel (.xlsx)")

    conteudo = await arquivo.read()

    codigo = extrair_codigo(conteudo)
    if not codigo:
        raise HTTPException(
            status_code=422,
            detail="Código da cotação não encontrado na planilha. "
                   "Verifique se é o arquivo gerado pelo sistema (COT-...).",
        )

    result = await db.execute(
        select(Cotacao)
        .where(Cotacao.codigo == codigo, Cotacao.empresa_id == empresa_id)
        .options(selectinload(Cotacao.itens), selectinload(Cotacao.fornecedor))
    )
    cotacao = result.scalar_one_or_none()
    if not cotacao:
        raise HTTPException(
            status_code=404,
            detail=f"Cotação {codigo} não encontrada na sua conta.",
        )
    if cotacao.status == "cancelada":
        raise HTTPException(status_code=422, detail=f"A cotação {codigo} está cancelada.")

    try:
        itens_planilha = ler_itens_planilha(conteudo)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Não foi possível ler a planilha. A estrutura pode ter sido alterada.",
        )

    relatorio = casar_itens(cotacao.itens, itens_planilha)

    resumo = {
        "ok": sum(1 for r in relatorio if r["status"] == "ok"),
        "sem_preco": sum(1 for r in relatorio if r["status"] == "sem_preco"),
        "preco_invalido": sum(1 for r in relatorio if r["status"] == "preco_invalido"),
        "nao_encontrado": sum(1 for r in relatorio if r["status"] == "nao_encontrado"),
        "linha_extra": sum(1 for r in relatorio if r["status"] == "linha_extra"),
    }

    return {
        "cotacao_id": str(cotacao.id),
        "codigo": cotacao.codigo,
        "fornecedor": cotacao.fornecedor.nome,
        "status_atual": cotacao.status,
        "ja_processada": cotacao.status == "processada",
        "resumo": resumo,
        "itens": relatorio,
    }


@router.post("/{cotacao_id}/importar/analisar-pdf")
async def analisar_pdf_devolvido(
    cotacao_id: UUID,
    arquivo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    """
    Lê uma cotação em PDF (formato próprio do fornecedor) via IA e retorna o
    mesmo relatório de conferência do importador de planilha. NADA é gravado
    — o usuário revisa e confirma no passo seguinte (mesmo endpoint de
    confirmar da planilha).

    Diferente da planilha (que se autoidentifica pelo código embutido), o PDF
    do fornecedor não carrega nosso código — por isso a cotação é escolhida
    explicitamente pela URL, não descoberta do conteúdo do arquivo.
    """
    if not arquivo.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Envie um arquivo PDF.")

    cotacao = await _obter_cotacao_com_itens(db, cotacao_id, empresa_id)
    if cotacao.status == "cancelada":
        raise HTTPException(status_code=422, detail=f"A cotação {cotacao.codigo} está cancelada.")

    fornecedor = (await db.execute(
        select(Fornecedor).where(Fornecedor.id == cotacao.fornecedor_id)
    )).scalar_one()

    conteudo = await arquivo.read()

    itens_banco = [
        {
            "id": i.id,
            "tipo_item": i.tipo_item,
            "descricao": i.descricao,
            "detalhe": i.detalhe,
            "qtde": float(i.qtde),
            "unidade": i.unidade,
        }
        for i in cotacao.itens
    ]

    result = await db.execute(
        select(ApelidoFornecedorItem)
        .where(ApelidoFornecedorItem.fornecedor_id == cotacao.fornecedor_id)
    )
    apelidos = [
        {"termo_fornecedor": a.termo_fornecedor, "nosso_descricao": a.nosso_descricao}
        for a in result.scalars().all()
    ]

    try:
        relatorio = analisar_pdf_cotacao(conteudo, itens_banco, apelidos)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Não foi possível processar o PDF com a IA. Tente novamente ou use o "
                   "caminho da planilha Excel.",
        )

    resumo = {
        "ok": sum(1 for r in relatorio if r["status"] == "ok"),
        "possivel_substituicao": sum(1 for r in relatorio if r["status"] == "possivel_substituicao"),
        "nao_encontrado": sum(1 for r in relatorio if r["status"] == "nao_encontrado"),
        "linha_extra": sum(1 for r in relatorio if r["status"] == "linha_extra"),
    }

    return {
        "cotacao_id": str(cotacao.id),
        "codigo": cotacao.codigo,
        "fornecedor": fornecedor.nome,
        "status_atual": cotacao.status,
        "ja_processada": cotacao.status == "processada",
        "resumo": resumo,
        "itens": relatorio,
    }


class ItemConfirmacao(BaseModel):
    item_id: int
    preco_unitario: float | None = None
    marca_modelo_cotado: str | None = None
    prazo_entrega_dias: int | None = None
    obs_fornecedor: str | None = None
    termo_fornecedor: str | None = None  # presente só quando veio do import de PDF — grava/atualiza o apelido


class ConfirmacaoImportacao(BaseModel):
    itens: list[ItemConfirmacao]


@router.post("/{cotacao_id}/importar/confirmar", response_model=CotacaoComItens)
async def confirmar_importacao(
    cotacao_id: UUID,
    payload: ConfirmacaoImportacao,
    db: AsyncSession = Depends(get_db),
    usuario: UserOut = Depends(get_current_user),
    empresa_id: UUID = Depends(get_empresa_atual),
):
    """Grava os preços conferidos pelo usuário e marca a cotação como processada."""
    cotacao = await _obter_cotacao_com_itens(db, cotacao_id, empresa_id)

    itens_por_id = {i.id: i for i in cotacao.itens}

    # Apelidos já existentes pra esse fornecedor, carregados uma vez só — evita
    # duplicar quando dois itens da mesma confirmação normalizam pro mesmo termo
    # (ex: "Luva de Redução 5/8x1/2" e "...1/2x3/8" ambos viram "luva de cobre
    # redutora"): sem esse cache, o segundo não veria o primeiro ainda não
    # commitado e tentava inserir de novo, violando a unicidade.
    apelidos_existentes: dict[str, ApelidoFornecedorItem] = {
        a.termo_fornecedor: a
        for a in (await db.execute(
            select(ApelidoFornecedorItem).where(ApelidoFornecedorItem.fornecedor_id == cotacao.fornecedor_id)
        )).scalars().all()
    }

    atualizados = 0
    for conf in payload.itens:
        item = itens_por_id.get(conf.item_id)
        if not item:
            continue
        item.preco_unitario = conf.preco_unitario
        item.marca_modelo_cotado = conf.marca_modelo_cotado
        item.prazo_entrega_dias = conf.prazo_entrega_dias
        item.obs_fornecedor = conf.obs_fornecedor
        atualizados += 1

        # Confirmação de um casamento vindo do import por PDF (via IA) — grava/
        # atualiza o apelido pra esse fornecedor não precisar de IA de novo no mesmo termo.
        if conf.termo_fornecedor:
            termo = norm(conf.termo_fornecedor)
            existente = apelidos_existentes.get(termo)
            if existente:
                existente.nosso_ref_id = item.ref_id
                existente.nosso_tipo_item = item.tipo_item
                existente.nosso_descricao = item.descricao
            else:
                novo = ApelidoFornecedorItem(
                    fornecedor_id=cotacao.fornecedor_id,
                    empresa_id=empresa_id,
                    termo_fornecedor=termo,
                    nosso_ref_id=item.ref_id,
                    nosso_tipo_item=item.tipo_item,
                    nosso_descricao=item.descricao,
                )
                db.add(novo)
                apelidos_existentes[termo] = novo

    if atualizados == 0:
        raise HTTPException(status_code=422, detail="Nenhum item válido para atualizar.")

    cotacao.status = "processada"
    cotacao.data_recebimento = datetime.now().strftime("%Y-%m-%d %H:%M")
    await db.commit()

    return await _obter_cotacao_com_itens(db, cotacao_id, empresa_id)


async def _obter_cotacao_com_itens(db: AsyncSession, cotacao_id: UUID, empresa_id) -> Cotacao:
    result = await db.execute(
        select(Cotacao)
        .where(Cotacao.id == cotacao_id, Cotacao.empresa_id == empresa_id)
        .options(selectinload(Cotacao.itens))
    )
    cotacao = result.scalar_one_or_none()
    if not cotacao:
        raise HTTPException(status_code=404, detail="Cotação não encontrada")
    return cotacao
