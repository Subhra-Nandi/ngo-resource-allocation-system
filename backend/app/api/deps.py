from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.ngo_resource import NgoUser

bearer_scheme = HTTPBearer()


async def get_current_ngo(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> NgoUser:
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    ngo_id = payload.get("sub")
    result = await db.execute(select(NgoUser).where(NgoUser.id == ngo_id))
    ngo = result.scalar_one_or_none()

    if not ngo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NGO account not found",
        )
    return ngo