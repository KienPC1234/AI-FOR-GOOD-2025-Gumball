from typing import Optional
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str
    

class BaseTokenPayload(BaseModel):
    # Token subject (user ID)
    sub: int

    # The security stamp of the user
    iss: str

    # The expiration time of the token
    exp: datetime

    @property
    def security_stamp(self):
        """ Friendlier alias for `iss` field """
        return self.iss


class AccessTokenPayload(BaseTokenPayload):
    pass
    

class RefreshTokenPayload(BaseTokenPayload):
    pass


class TaskTokenPayload(BaseTokenPayload):
    # Celery task ID
    task_id: str

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