from sqlmodel import Field, SQLModel


class Employee(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    first_name: str
    last_name: str
    photo_path: str | None = None