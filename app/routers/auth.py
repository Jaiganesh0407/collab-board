import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED
)
def register(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    # Validate email & password
    auth.validate_email(payload.email)
    auth.validate_password(payload.password)

    existing_user = (
        db.query(models.User)
        .filter(models.User.email == payload.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered."
        )

    user = models.User(
        id=str(uuid.uuid4()),
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        hashed_password=auth.hash_password(payload.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(models.User.email == form_data.username.lower())
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password."
        )

    if not auth.verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password."
        )

    access_token = auth.create_access_token(
        user.id,
        user.email
    )

    refresh_token = auth.create_refresh_token(
        user.id
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


@router.get(
    "/me",
    response_model=schemas.UserOut
)
def me(
    current_user: models.User = Depends(
        auth.get_current_user
    )
):
    return current_user


@router.post("/refresh")
def refresh_token(
    token: schemas.RefreshToken,
    db: Session = Depends(get_db)
):
    payload = auth.decode_token(token.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token."
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type."
        )

    user = (
        db.query(models.User)
        .filter(models.User.id == payload.get("sub"))
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    access_token = auth.create_access_token(
        user.id,
        user.email
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
