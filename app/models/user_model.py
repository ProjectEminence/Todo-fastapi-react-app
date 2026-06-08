from uuid import UUID
from uuid import uuid4

from pydantic import BaseModel
from pydantic import EmailStr
from sqlmodel import Field
from sqlmodel import SQLModel


class UserBase(SQLModel):
    username: str | None = Field(index=True, unique=True, description="user username")
    email: EmailStr | None = Field(unique=True, description="user email")
    firstName: str | None = Field(default=None, description="user first name")
    lastName: str | None = Field(default=None, description="user last name")
    isAdmin: bool = Field(
        default=False,
        description="Flag to indicate wether user is admin",
    )


class UserCreate(UserBase):
    email: EmailStr = Field(unique=True, description="user email")
    password: str = Field(min_length=5, max_length=24, description="user password")


class UserUpdate(UserBase):
    id: UUID = Field(default_factory=uuid4, description="user id")
    username: str | None = Field(default=None, description="user username")
    email: EmailStr | None = Field(default=None, description="user email")
    new_password: str | None = Field(
        default=None,
        min_length=5,
        max_length=24,
        description="new user password",
    )
    password: str = Field(description="user password")


class User(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, description="user id")
    hashed_password: str = Field(default="The hash of the password")


class UserOut(BaseModel):
    """Plain Pydantic response schema — safe for serializing any object with these fields."""
    id: UUID
    username: str | None
    email: str | None
    firstName: str | None = None
    lastName: str | None = None
    isAdmin: bool = False
    hashed_password: str | None = None

    class Config:
        orm_mode = True
