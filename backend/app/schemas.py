from pydantic import BaseModel, EmailStr, ValidationError, Field
from datetime import date
from fastapi import Form
from fastapi.exceptions import RequestValidationError
from fastapi_users.schemas import BaseUserCreate, BaseUser
import uuid 


class EmployeeBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    photo_path: str


class EmployeeUpdate(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    photo_path: str | None = None

    @classmethod
    def as_form(
        cls,
        email: str | None = Form(default=None), 
        first_name: str | None = Form(default=None),
        last_name: str | None = Form(default=None)
    ):
        try:
            return cls(email=email, first_name=first_name, last_name=last_name)
        except ValidationError as e:
            raise RequestValidationError(e.errors()) from e



class EmployeeCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

    @classmethod
    def as_form(
        cls,
        email: str = Form(...),
        first_name: str = Form(...),
        last_name: str = Form(...),
    ):
        try:
            return cls(email=email, first_name=first_name, last_name=last_name)
        except ValidationError as e:
            raise RequestValidationError(e.errors()) from e


class QRCodeBase(BaseModel):
    employee_id: int
    token_hash: str
    expires_at: date

class UserLogin(BaseModel):
    username: EmailStr = Field(..., alias="email")
    password: str

class UserRead(BaseUser):
    pass


class UserCreate(BaseUserCreate):
    email: EmailStr
    password: str