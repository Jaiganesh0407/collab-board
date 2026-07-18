import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/api/boards", tags=["boards"])

DEFAULT_COLUMNS = ["To Do", "In Progress", "Done"]


def _get_workspace_or_404(db, workspace_id, user):
    ws = db.query(models.Workspace).filter(models.Workspace.id == workspace_id).first()
    if not ws or user not in ws.members:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return ws


def _get_board_or_404(db, board_id, user):
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    ws = db.query(models.Workspace).filter(models.Workspace.id == board.workspace_id).first()
    if user not in ws.members:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    return board


@router.post("/workspace/{workspace_id}", response_model=schemas.BoardOut, status_code=201)
def create_board(
    workspace_id: str,
    payload: schemas.BoardCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _get_workspace_or_404(db, workspace_id, current_user)
    board = models.Board(id=str(uuid.uuid4()), name=payload.name, workspace_id=workspace_id)
    db.add(board)
    db.flush()

    for i, col_name in enumerate(DEFAULT_COLUMNS):
        db.add(models.BoardColumn(id=str(uuid.uuid4()), name=col_name, position=i, board_id=board.id))

    db.commit()
    db.refresh(board)
    return board


@router.get("/workspace/{workspace_id}", response_model=list[schemas.BoardOut])
def list_boards(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ws = _get_workspace_or_404(db, workspace_id, current_user)
    return ws.boards


@router.get("/{board_id}/full")
def get_board_full(
    board_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Returns the board with nested columns and cards — one call to render the UI."""
    board = _get_board_or_404(db, board_id, current_user)
    return {
        "id": board.id,
        "name": board.name,
        "columns": [
            {
                "id": col.id,
                "name": col.name,
                "position": col.position,
                "cards": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "description": c.description,
                        "position": c.position,
                        "version": c.version,
                    }
                    for c in col.cards
                ],
            }
            for col in board.columns
        ],
    }


@router.post("/{board_id}/columns", response_model=schemas.ColumnOut, status_code=201)
def create_column(
    board_id: str,
    payload: schemas.ColumnCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _get_board_or_404(db, board_id, current_user)
    col = models.BoardColumn(
        id=str(uuid.uuid4()), name=payload.name, position=payload.position, board_id=board_id
    )
    db.add(col)
    db.commit()
    db.refresh(col)
    return col
