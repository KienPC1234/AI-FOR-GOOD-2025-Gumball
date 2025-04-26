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