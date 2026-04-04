from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.ngo_resource import NgoUser
from app.schemas.resource import NgoLogin, NgoRegister, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register_ngo(data: NgoRegister, db: AsyncSession = Depends(get_db)):
    """Register a new NGO. Each NGO gets one account to manage their resources."""
    # Check email not already taken
    existing = await db.execute(
        select(NgoUser).where(NgoUser.email == data.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    ngo = NgoUser(
        ngo_name=data.ngo_name,
        email=data.email,
        hashed_password=hash_password(data.password),
        contact_phone=data.contact_phone,
    )
    db.add(ngo)
    await db.flush()  # gets the generated id without full commit

    token = create_access_token({"sub": str(ngo.id), "email": ngo.email})
    return {
        "message": "NGO registered successfully",
        "ngo_id": str(ngo.id),
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=TokenResponse)
async def login_ngo(data: NgoLogin, db: AsyncSession = Depends(get_db)):
    """NGO admin login. Returns JWT used for all protected endpoints."""
    result = await db.execute(
        select(NgoUser).where(NgoUser.email == data.email)
    )
    ngo = result.scalar_one_or_none()

    if not ngo or not verify_password(data.password, ngo.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": str(ngo.id), "email": ngo.email})
    return TokenResponse(access_token=token)