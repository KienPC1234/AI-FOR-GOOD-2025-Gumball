from typing import List, Union

from pydantic import EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # General
    BASE_STORAGE_PATH: str
    BASE_USER_STORAGE_PATH: str
    MAX_FILE_UPLOAD_SIZE: int
    IMAGE_FILE_ALLOWED_EXTENSIONS: List[str] = [
    ".png",".dicom",".jpe",".jpeg",".jpg",".pjpg",".jfif",".jfif-tbnl",".jif"
    ]

    @field_validator("IMAGE_FILE_ALLOWED_EXTENSIONS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and v.startswith("["):
            return [i.strip() for i in v.rstrip()[:-1].split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Server information
    PROJECT_NAME: str
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8000", "http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and v.startswith("["):
            return [i.strip() for i in v.rstrip()[:-1].split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    REFRESH_SECRET_KEY: str            # e.g. set in your .env
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7   # default 7 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Mailjet
    MAILJET_API_KEY: str
    MAILJET_SECRET_KEY: str
    MAILJET_SENDER_EMAIL: EmailStr
    MAILJET_SENDER_NAME: str

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env.example"
    )


settings = Settings()
