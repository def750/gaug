from . import BaseModel


class LoginData(BaseModel):
    username: str
    pw_md5: str


class Token(BaseModel):
    token: str
    expires: int
