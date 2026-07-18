import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth
from app.ws_manager import manager
from app.routers.boards import _get_board_or_404

router = APIRouter(prefix="/api/cards", tags=["cards"])


def _board_id_for_column(db, column_id):
    col = db.query(models.BoardColumn).filter(models.BoardColumn.id == column_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    return col.board_id, col


@router.post("", response_model=schemas.CardOut, status_code=201)
async def create_card(
    payload: schemas.CardCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    board_id, _ = _board_id_for_column(db, payload.column_id)
    _get_board_or_404(db, board_id, current_user)

    card = models.Card(
        id=str(uuid.uuid4()),
        title=payload.title,
        description=payload.description,
        column_id=payload.column_id,
        position=payload.position,
        created_by=current_user.id,
    )
    db.add(card)
    db.add(models.ActivityLog(
        id=str(uuid.uuid4()), board_id=board_id, user_id=current_user.id,
        action="card_created", detail=payload.title,
    ))
    db.commit()
    db.refresh(card)

    await manager.broadcast(board_id, {
        "type": "card_created",
        "card": {"id": card.id, "title": card.title, "description": card.description,
                  "column_id": card.column_id, "position": card.position, "version": card.version},
        "by": current_user.name,
    })
    return card


@router.patch("/{card_id}/move", response_model=schemas.CardOut)
async def move_card(
    card_id: str,
    payload: schemas.CardMove,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Moves a card to a new column/position.
    Uses optimistic locking: the client must send the `version` it last saw.
    If another user moved the card in the meantime, this returns 409 Conflict
    so the client can refresh and retry instead of silently overwriting changes.
    """
    card = db.query(models.Card).filter(models.Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    board_id, _ = _board_id_for_column(db, card.column_id)
    _get_board_or_404(db, board_id, current_user)

    if card.version != payload.version:
        raise HTTPException(
            status_code=409,
            detail="This card was updated by someone else. Refresh and try again.",
        )

    card.column_id = payload.column_id
    card.position = payload.position
    card.version += 1
    db.commit()
    db.refresh(card)

    await manager.broadcast(board_id, {
        "type": "card_moved",
        "card": {"id": card.id, "column_id": card.column_id, "position": card.position,
                  "version": card.version},
        "by": current_user.name,
    })
    return card


@router.delete("/{card_id}", status_code=204)
async def delete_card(
    card_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    card = db.query(models.Card).filter(models.Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    board_id, _ = _board_id_for_column(db, card.column_id)
    _get_board_or_404(db, board_id, current_user)

    db.delete(card)
    db.commit()

    await manager.broadcast(board_id, {"type": "card_deleted", "card_id": card_id, "by": current_user.name})
