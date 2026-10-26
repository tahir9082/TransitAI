from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models import UserProfile

router = APIRouter(prefix="/api/profiles", tags=["Profiles"])

# Pydantic schema for input validation
class ProfileUpdate(BaseModel):
    session_token: str
    home_station: Optional[str] = None
    work_station: Optional[str] = None
    requires_wheelchair: bool = False

@router.get("/{session_token}")
async def get_profile(session_token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).where(UserProfile.session_token == session_token))
    profile = result.scalars().first()
    
    # Return defaults if the user hasn't saved anything yet
    if not profile:
        return {
            "session_token": session_token,
            "home_station": None, 
            "work_station": None, 
            "requires_wheelchair": False
        }
    return profile

@router.post("/")
async def save_profile(data: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).where(UserProfile.session_token == data.session_token))
    profile = result.scalars().first()
    
    if not profile:
        # Create new profile
        profile = UserProfile(**data.model_dump())
        db.add(profile)
    else:
        # Update existing profile
        profile.home_station = data.home_station
        profile.work_station = data.work_station
        profile.requires_wheelchair = data.requires_wheelchair
        
    await db.commit()
    await db.refresh(profile)
    return profile