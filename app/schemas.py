import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceOut(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class BoardCreate(BaseModel):
    name: str


class BoardOut(BaseModel):
    id: str
    name: str
    workspace_id: str

    class Config:
        from_attributes = True


class ColumnCreate(BaseModel):
    name: str
    position: int = 0


class ColumnOut(BaseModel):
    id: str
    name: str
    position: int

    class Config:
        from_attributes = True


class CardCreate(BaseModel):
    title: str
    description: Optional[str] = None
    column_id: str
    position: int = 0


class CardMove(BaseModel):
    column_id: str
    position: int
    version: int  # client must send the version it last saw (optimistic locking)


class CardOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    column_id: str
    position: int
    version: int

    class Config:
        from_attributes = True


class InviteMember(BaseModel):
    email: EmailStr
