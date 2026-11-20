
from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    phone: str | None = None
    avatar_url: str | None = None
    date_of_birth: date | None = None
    skills: str | None = None
    area: str | None = None
    total_hours: float = 0


class PublicProfileResponse(BaseModel):
    id: int
    full_name: str
    avatar_url: str | None = None
    skills: str | None = None
    area: str | None = None
    total_hours: float = 0
    certificates_count: int = 0
    campaigns_count: int = 0
