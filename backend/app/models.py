from sqlmodel import Field, SQLModel
from datetime import date, datetime


class Employee(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    first_name: str
    last_name: str
    photo_path: str | None = None

class QRCode(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id")
    token_hash: str
    expires_at: date
    is_revoked: bool = False

class EntryExitRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id")
    timestamp: datetime
    successful: bool
    denial_reason: str | None = None