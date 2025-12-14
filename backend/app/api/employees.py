from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import logging
from datetime import date, timedelta
import secrets
import hashlib
from app import crud
from app.db import SessionDep
from app.schemas import EmployeeUpdate, EmployeeCreate, QRCodeBase
from app.utitls import save_photo, generate_qr_and_send_email

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
    employee_exists = crud.get_employee_by_email(session=session, email=employee.email)
    if employee_exists is not None:
        logger.error(f"Employee with email {employee.email} already exists.")
        raise HTTPException(
            status_code=400,
            detail="Employee with this email already exists.",
        )

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


@r.post("/{employee_id}/generate_qr_code", status_code=204)
async def generate_qr_code_for_employee(
    *,
    employee_id: int,
    session: SessionDep,
) -> None:
    employee = crud.get_employee(session=session, employee_id=employee_id)
    recipient_email = employee.email

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    current_date = date.today()
    expiration_date = current_date + timedelta(weeks=4)

    qr_code_in = QRCodeBase(
        employee_id=employee_id,
        token_hash=token_hash,
        expires_at=expiration_date,
    )
    qr_code = crud.create_qr_code(session=session, qr_code=qr_code_in)

    await generate_qr_and_send_email(
        recipient=recipient_email, token=f"{employee_id}:{token}"
    )


@r.delete("/{employee_id}/revoke_qr_code", status_code=204)
def revoke_qr_code_for_employee(*, employee_id: int, session: SessionDep) -> None:
    employee = crud.get_employee(session=session, employee_id=employee_id)
    crud.revode_qr_code(session=session, employee_id=employee_id)
