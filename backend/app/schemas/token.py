from typing import Optional
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class AccessTokenPayload(BaseModel):
    # Token subject (user ID)
    sub: str = None

    # The security stamp of the user
    iss: str

    @property
    def security_stamp(self):
        """ Friendlier alias for `iss` field """
        return self.iss
    

class RefreshTokenPayload(BaseModel):
    # Token subject (user ID)
    sub: str = None

    # The security stamp of the user
    iss: str

    # The expiration time of the token
    exp: datetime = None

    @property
    def security_stamp(self):
        """ Friendlier alias for `iss` field """
        return self.iss


class DoctorConnectTokenBase(BaseModel):
    token: str
    expires_at: datetime
    is_used: bool = False


class DoctorConnectTokenCreate(BaseModel):
    expires_in_minutes: int = 60  # Default expiration time


class DoctorConnectToken(DoctorConnectTokenBase):
    id: int
    doctor_id: int

    class Config:
        orm_mode = True