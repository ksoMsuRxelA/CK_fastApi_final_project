"""Эндпоинты аутентификации: регистрация, логин, профиль."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.jwt import create_access_token
from app.dependencies import CurrentUser, DbSession
from app.schemas import Token, UserCreate, UserRead
from app.services.user_service import (
    UserAlreadyExistsError,
    authenticate_user,
    create_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
)
async def register(data: UserCreate, session: DbSession) -> UserRead:
    """Создать нового пользователя и вернуть его публичные данные."""
    try:
        user = await create_user(session, data)
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        ) from exc
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=Token,
    summary="Вход в систему (OAuth2 Password Flow)",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: DbSession,
) -> Token:
    """Принимает email в поле username и пароль, возвращает JWT."""
    user = await authenticate_user(session, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.id)
    return Token(access_token=token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Текущий пользователь (требует токен)",
)
async def get_me(current_user: CurrentUser) -> UserRead:
    """Вернуть данные пользователя, которому принадлежит токен."""
    return UserRead.model_validate(current_user)
