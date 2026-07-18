import datetime
import enum
import uuid

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Integer, Text, Enum, Table, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.database import Base, engine


def _uuid_col():
    # Use a plain String for SQLite compatibility, PG UUID for Postgres
    if engine.dialect.name == "postgresql":
        return Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    return Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))


class RoleEnum(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


workspace_members = Table(
    "workspace_members",
    Base.metadata,
    Column("workspace_id", String(36), ForeignKey("workspaces.id"), primary_key=True),
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
    Column("role", Enum(RoleEnum), default=RoleEnum.member, nullable=False),
)


class User(Base):
    __tablename__ = "users"

    id = _uuid_col()
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    workspaces = relationship(
        "Workspace", secondary=workspace_members, back_populates="members"
    )


class Workspace(Base):
    __tablename__ = "workspaces"

    id = _uuid_col()
    name = Column(String(255), nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    members = relationship("User", secondary=workspace_members, back_populates="workspaces")
    boards = relationship("Board", back_populates="workspace", cascade="all, delete-orphan")


class Board(Base):
    __tablename__ = "boards"

    id = _uuid_col()
    name = Column(String(255), nullable=False)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    workspace = relationship("Workspace", back_populates="boards")
    columns = relationship(
        "BoardColumn", back_populates="board", cascade="all, delete-orphan",
        order_by="BoardColumn.position"
    )


class BoardColumn(Base):
    __tablename__ = "board_columns"

    id = _uuid_col()
    name = Column(String(255), nullable=False)
    position = Column(Integer, nullable=False, default=0)
    board_id = Column(String(36), ForeignKey("boards.id"), nullable=False)

    board = relationship("Board", back_populates="columns")
    cards = relationship(
        "Card", back_populates="column", cascade="all, delete-orphan",
        order_by="Card.position"
    )


class Card(Base):
    __tablename__ = "cards"

    id = _uuid_col()
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    position = Column(Integer, nullable=False, default=0)
    column_id = Column(String(36), ForeignKey("board_columns.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    version = Column(Integer, nullable=False, default=1)  # optimistic locking
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    column = relationship("BoardColumn", back_populates="cards")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = _uuid_col()
    board_id = Column(String(36), ForeignKey("boards.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    action = Column(String(255), nullable=False)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
