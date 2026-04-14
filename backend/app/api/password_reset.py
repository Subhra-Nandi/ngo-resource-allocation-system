import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password
from app.models.ngo_resource import NgoUser

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory store for reset tokens
# In production use Redis — fine for hackathon
_reset_tokens: dict[str, dict] = {}


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generates a reset token.
    In production this emails the link — for now returns token directly
    so you can test without email setup.
    """
    result = await db.execute(
        select(NgoUser).where(NgoUser.email == data.email)
    )
    user = result.scalar_one_or_none()

    # Always return success — never reveal if email exists
    if not user:
        return {"message": "If that email exists, a reset link has been sent."}

    token = secrets.token_urlsafe(32)
    _reset_tokens[token] = {
        "email": data.email,
        "expires": datetime.now(timezone.utc) + timedelta(minutes=30),
    }

    # TODO: In production send email with link
    # For now return token directly for testing
    reset_link = f"http://localhost:3000/reset-password?token={token}"
    print(f"PASSWORD RESET LINK: {reset_link}")

    return {
        "message": "If that email exists, a reset link has been sent.",
        # Remove this line in production:
        "debug_reset_link": reset_link,
    }


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validates reset token and updates password."""
    token_data = _reset_tokens.get(data.token)

    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if datetime.now(timezone.utc) > token_data["expires"]:
        del _reset_tokens[data.token]
        raise HTTPException(status_code=400, detail="Reset token has expired")

    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    await db.execute(
        update(NgoUser)
        .where(NgoUser.email == token_data["email"])
        .values(hashed_password=hash_password(data.new_password))
    )
    await db.commit()

    del _reset_tokens[data.token]

    return {"message": "Password reset successfully. You can now log in."}