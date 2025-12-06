from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Depends
import logging

from app import crud
from app.db import SessionDep
from app.schemas import  EmployeeUpdate, EmployeeCreate
from app.utitls import save_photo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


employees_router = r = APIRouter(prefix="/employees")


@r.post("/", status_code=201)
async def create_employee(
    *,
    session: SessionDep,
    employee: EmployeeCreate = Depends(EmployeeCreate.as_form),
    photo: UploadFile,
):
    created_employee = crud.create_employee(session=session, employee=employee)
    logger.info(f"Employee created with ID: {created_employee.id}")
    employee_id = created_employee.id
    assert employee_id is not None

    photo_name = f"user_{created_employee.id}.png"
    save_photo(photo_name, photo)
    logger.info(f"Photo saved as: {photo_name}")
    employee_in = EmployeeUpdate(photo_path=photo_name)

    updated_employee = crud.update_employee(
        session=session, employee_id=employee_id, employee_in=employee_in
    )
    return updated_employee


@r.get("/", status_code=200)
def list_employees(*, session: SessionDep):
    employees = crud.list_employees(session=session)
    return employees


@r.put("/{employee_id}", status_code=200)
async def update_employee(
    *,
    employee_id: int,
    session: SessionDep,
    employee_in: EmployeeUpdate = Depends(EmployeeUpdate.as_form),
    photo: Annotated[UploadFile | None, File()] = None,
):

    if photo is not None:
        photo_name = f"user_{employee_id}.png"
        save_photo(photo_name, photo)

    employee = crud.update_employee(
        session=session, employee_id=employee_id, employee_in=employee_in
    )
    return employee


@r.delete("/{employee_id}", status_code=204)
async def delete_employee(*, employee_id: int, session: SessionDep):
    crud.delete_employee(session=session, employee_id=employee_id)
