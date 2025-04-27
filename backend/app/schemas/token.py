from typing import Optional
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenPayload(BaseModel):
    # Token subject (user ID)
    sub: Optional[str] = None

    # The security stamp of the user
    iss: str

    @property
    def security_stamp(self):
        """ Friendlier alias for `iss` field """
        return self.iss


class DoctorConnectTokenBase(BaseModel):
    token: str
    expires_at: datetime
    password: Optional[str] = None
    is_used: bool = False


class DoctorConnectTokenCreate(BaseModel):
    expires_in_minutes: int = 60  # Default expiration time
    password: Optional[str] = None


class DoctorConnectToken(DoctorConnectTokenBase):
    id: int
    doctor_id: int

    class Config:
        orm_mode = True