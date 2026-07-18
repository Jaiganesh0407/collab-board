import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.post("", response_model=schemas.WorkspaceOut, status_code=201)
def create_workspace(
    payload: schemas.WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ws = models.Workspace(id=str(uuid.uuid4()), name=payload.name, owner_id=current_user.id)
    ws.members.append(current_user)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


@router.get("", response_model=list[schemas.WorkspaceOut])
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return current_user.workspaces


@router.post("/{workspace_id}/invite", status_code=204)
def invite_member(
    workspace_id: str,
    payload: schemas.InviteMember,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ws = db.query(models.Workspace).filter(models.Workspace.id == workspace_id).first()
    if not ws or current_user not in ws.members:
        raise HTTPException(status_code=404, detail="Workspace not found")

    invitee = db.query(models.User).filter(models.User.email == payload.email).first()
    if not invitee:
        raise HTTPException(status_code=404, detail="No user with that email")
    if invitee not in ws.members:
        ws.members.append(invitee)
        db.commit()
