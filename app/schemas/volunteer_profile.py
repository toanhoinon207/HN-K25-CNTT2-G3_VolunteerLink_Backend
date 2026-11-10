from datetime import date
from pydantic import BaseModel, ConfigDict, Field

class VolunteerProfileCreate(BaseModel):
    date_of_birth: date | None = None
    skills: str | None = None
    area: str | None = Field(default=None, max_length=255)

class VolunteerProfileResponse(VolunteerProfileCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
