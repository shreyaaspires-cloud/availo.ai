from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.services import auth_service, user_service
from app.dependencies.auth import get_current_user
from app.middleware.rate_limiter import limiter

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await user_service.get_user_by_email(data.email, db)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = await user_service.create_user(data, db)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/15minute")
async def login(
    request: Request,
    response: Response,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.get_user_by_email(data.email, db)
    if not user or not auth_service.verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    payload = {"sub": str(user.id), "roles": user.roles}
    access_token = auth_service.create_access_token(payload)
    refresh_token = auth_service.create_refresh_token(payload)

    # Set httpOnly cookie for refresh token
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production with HTTPS
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        roles=user.roles,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    ref_token = request.cookies.get("refresh_token")
    if not ref_token:
        # Fallback check Authorization header if cookie is missing
        auth_hdr = request.headers.get("Authorization")
        if auth_hdr and auth_hdr.startswith("Bearer "):
            ref_token = auth_hdr.split(" ")[1]

    if not ref_token:
        raise HTTPException(status_code=401, detail="Refresh token required")

    payload = auth_service.decode_token(ref_token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Invalid token")

    import uuid
    user = await user_service.get_user_by_id(uuid.UUID(user_id_str), db)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    new_payload = {"sub": str(user.id), "roles": user.roles}
    new_access = auth_service.create_access_token(new_payload)
    new_refresh = auth_service.create_refresh_token(new_payload)

    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        samesite="lax",
        secure=False,
    )

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        roles=user.roles,
    )


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="refresh_token")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
