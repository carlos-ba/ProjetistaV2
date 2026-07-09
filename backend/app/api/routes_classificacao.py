from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.models.classificacao import BlocoOrcamento, ClassificacaoItem, ItemClassificacao
from app.schemas.auth import UserOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/classificacoes", tags=["classificacoes"])


# ── Schemas ───────────────────────────────────────────────────────────────
class BlocoPayload(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    ordem: int = 0


class ClassificacaoPayload(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    bloco_id: int
    ordem: int = 0


class RemapPayload(BaseModel):
    tipo_item: str = Field(..., min_length=1, max_length=50)
    classificacao_id: int


# ── Árvore (consumida pelo frontend) ──────────────────────────────────────
@router.get("")
async def obter_arvore(db: AsyncSession = Depends(get_db)):
    blocos = (await db.execute(select(BlocoOrcamento).order_by(BlocoOrcamento.ordem))).scalars().all()
    classes = (await db.execute(select(ClassificacaoItem).order_by(ClassificacaoItem.ordem))).scalars().all()
    itens = (await db.execute(select(ItemClassificacao))).scalars().all()
    return {
        "blocos": [{"id": b.id, "nome": b.nome, "ordem": b.ordem} for b in blocos],
        "classificacoes": [
            {"id": c.id, "nome": c.nome, "bloco_id": c.bloco_id, "ordem": c.ordem} for c in classes
        ],
        "mapa": {i.tipo_item: i.classificacao_id for i in itens},
    }


# ── Blocos ────────────────────────────────────────────────────────────────
@router.post("/blocos", status_code=201)
async def criar_bloco(payload: BlocoPayload, usuario: UserOut = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    bloco = BlocoOrcamento(**payload.model_dump())
    db.add(bloco)
    await db.commit()
    await db.refresh(bloco)
    return {"id": bloco.id, "nome": bloco.nome, "ordem": bloco.ordem}


@router.put("/blocos/{bloco_id}")
async def atualizar_bloco(bloco_id: int, payload: BlocoPayload,
                          usuario: UserOut = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bloco = await db.get(BlocoOrcamento, bloco_id)
    if not bloco:
        raise HTTPException(404, "Bloco não encontrado")
    bloco.nome = payload.nome
    bloco.ordem = payload.ordem
    await db.commit()
    return {"id": bloco.id, "nome": bloco.nome, "ordem": bloco.ordem}


@router.delete("/blocos/{bloco_id}", status_code=204)
async def deletar_bloco(bloco_id: int, usuario: UserOut = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    bloco = await db.get(BlocoOrcamento, bloco_id)
    if not bloco:
        raise HTTPException(404, "Bloco não encontrado")
    await db.delete(bloco)
    await db.commit()


# ── Classificações ────────────────────────────────────────────────────────
@router.post("/itens-classificacao", status_code=201)
async def criar_classificacao(payload: ClassificacaoPayload,
                              usuario: UserOut = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cls = ClassificacaoItem(**payload.model_dump())
    db.add(cls)
    await db.commit()
    await db.refresh(cls)
    return {"id": cls.id, "nome": cls.nome, "bloco_id": cls.bloco_id, "ordem": cls.ordem}


@router.put("/itens-classificacao/{cls_id}")
async def atualizar_classificacao(cls_id: int, payload: ClassificacaoPayload,
                                  usuario: UserOut = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cls = await db.get(ClassificacaoItem, cls_id)
    if not cls:
        raise HTTPException(404, "Classificação não encontrada")
    cls.nome = payload.nome
    cls.bloco_id = payload.bloco_id
    cls.ordem = payload.ordem
    await db.commit()
    return {"id": cls.id, "nome": cls.nome, "bloco_id": cls.bloco_id, "ordem": cls.ordem}


@router.delete("/itens-classificacao/{cls_id}", status_code=204)
async def deletar_classificacao(cls_id: int, usuario: UserOut = Depends(get_current_user),
                                db: AsyncSession = Depends(get_db)):
    cls = await db.get(ClassificacaoItem, cls_id)
    if not cls:
        raise HTTPException(404, "Classificação não encontrada")
    await db.delete(cls)
    await db.commit()


# ── Remapeia tipo_item → classificação ────────────────────────────────────
@router.put("/mapa")
async def remapear_item(payload: RemapPayload, usuario: UserOut = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ItemClassificacao).where(ItemClassificacao.tipo_item == payload.tipo_item)
    )
    item = result.scalar_one_or_none()
    if item:
        item.classificacao_id = payload.classificacao_id
    else:
        item = ItemClassificacao(tipo_item=payload.tipo_item, classificacao_id=payload.classificacao_id)
        db.add(item)
    await db.commit()
    return {"tipo_item": payload.tipo_item, "classificacao_id": payload.classificacao_id}
