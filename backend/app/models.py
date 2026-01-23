from sqlmodel import Field, SQLModel
from datetime import date, datetime
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID



class User(SQLModel, table=True):
    __tablename__ = "auth_user"
    id: int | None = Field(default=None, primary_key=True)
    email: str
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

class Employee(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    first_name: str
    last_name: str
    photo_path: str | None = None
    is_present: bool = False

class QRCode(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id", ondelete="CASCADE")
    token_hash: str
    expires_at: date
    is_revoked: bool = False

class EntryExitRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id")
    timestamp: datetime
    successful: bool
    denial_reason: str | None = None
    is_entry: bool | None = None  # True for entry, False for exit


class WorkTimeRecord(SQLModel, table=True):
    """Record of work time for an employee (created when employee exits)."""
    id: int | None = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id", ondelete="CASCADE")
    date: date  # Date of the work session
    entry_time: datetime  # When employee entered
    exit_time: datetime  # When employee exited
    duration_minutes: int  # Duration in minutes for easy querying