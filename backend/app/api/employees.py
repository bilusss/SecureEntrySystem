from typing import Annotated
import logging
from datetime import date, timedelta
import secrets
import hashlib
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app import crud
from app.db import SessionDep
from app.schemas import EmployeeUpdate, EmployeeCreate, QRCodeBase
from app.utils import save_photo, generate_qr_and_send_email
from app.users import current_user
from app.models import User

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
    user: User = Depends(current_user),
    session: SessionDep,
    employee: EmployeeCreate = Depends(EmployeeCreate.as_form),
    photo: UploadFile,
):
    logger.info(
        "User %s requested employee creation for email=%s",
        getattr(user, "email", str(user)),
        employee.email,
    )
    employee_exists = crud.get_employee_by_email(session=session, email=employee.email)
    if employee_exists is not None:
        logger.error("Employee with email %s already exists.", employee.email)
        raise HTTPException(
            status_code=400,
            detail="Employee with this email already exists.",
        )

    created_employee = crud.create_employee(session=session, employee=employee)
    logger.info("Employee created with ID: %s", created_employee.id)
    employee_id = created_employee.id
    assert employee_id is not None

    photo_name = f"user_{created_employee.id}.png"
    try:
        save_photo(photo_name, photo)
        logger.info("Photo saved as: %s for employee_id=%s", photo_name, employee_id)
    except Exception as e:
        logger.exception("Failed to save photo for employee_id=%s: %s", employee_id, e)
        raise HTTPException(status_code=500, detail="Failed to save photo.")

    employee_in = EmployeeUpdate(photo_path=photo_name)

    updated_employee = crud.update_employee(
        session=session, employee_id=employee_id, employee_in=employee_in
    )
    logger.info("Employee updated (photo_path set) for ID: %s", employee_id)
    return updated_employee


@r.get("/", status_code=200)
def list_employees(*, user: User = Depends(current_user), session: SessionDep):
    logger.info("User %s requested employee list", getattr(user, "email", str(user)))
    employees = crud.list_employees(session=session)
    logger.info(
        "Returning %d employees", len(employees) if employees is not None else 0
    )
    return employees


@r.put("/{employee_id}", status_code=200)
async def update_employee(
    *,
    user: User = Depends(current_user),
    employee_id: int,
    session: SessionDep,
    employee_in: EmployeeUpdate = Depends(EmployeeUpdate.as_form),
    photo: Annotated[UploadFile | None, File()] = None,
):
    logger.info(
        "User %s requested update for employee_id=%s",
        getattr(user, "email", str(user)),
        employee_id,
    )

    if employee_in.email is not None:
        employee_exists = crud.get_employee_by_email(
            session=session, email=employee_in.email
        )
    else:
        employee_exists = None

    if employee_exists is not None and employee_exists.id != employee_id:
        logger.error(
            "Employee with email %s already exists (conflict with id=%s).",
            employee_in.email,
            employee_exists.id,
        )
        raise HTTPException(
            status_code=400,
            detail="Employee with this email already exists.",
        )

    if photo is not None:
        photo_name = f"user_{employee_id}.png"
        try:
            save_photo(photo_name, photo)
            logger.info(
                "Photo updated and saved as: %s for employee_id=%s",
                photo_name,
                employee_id,
            )
            employee_in.photo_path = photo_name
        except Exception as e:
            logger.exception(
                "Failed to save updated photo for employee_id=%s: %s", employee_id, e
            )
            raise HTTPException(status_code=500, detail="Failed to save photo.")

    employee = crud.update_employee(
        session=session, employee_id=employee_id, employee_in=employee_in
    )
    logger.info("Employee updated successfully for ID: %s", employee_id)
    return employee


@r.delete("/{employee_id}", status_code=204)
async def delete_employee(
    *, user: User = Depends(current_user), employee_id: int, session: SessionDep
):
    logger.info(
        "User %s requested deletion of employee_id=%s",
        getattr(user, "email", str(user)),
        employee_id,
    )
    crud.delete_employee(session=session, employee_id=employee_id)
    logger.info("Employee deleted: %s", employee_id)


@r.post("/{employee_id}/generate_qr_code", status_code=204)
async def generate_qr_code_for_employee(
    *,
    user: User = Depends(current_user),
    employee_id: int,
    session: SessionDep,
) -> None:
    logger.info(
        "User %s requested QR code generation for employee_id=%s",
        getattr(user, "email", str(user)),
        employee_id,
    )
    employee = crud.get_employee(session=session, employee_id=employee_id)
    if employee is None:
        logger.error("Employee not found for ID: %s", employee_id)
        raise HTTPException(status_code=404, detail="Employee not found.")
    recipient_email = employee.email
    logger.info(
        "Generating token for employee_id=%s to be sent to %s",
        employee_id,
        recipient_email,
    )

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    logger.debug("Token hash generated for employee_id=%s", employee_id)

    current_date = date.today()
    expiration_date = current_date + timedelta(weeks=4)
    logger.info(
        "QR code will expire at %s for employee_id=%s", expiration_date, employee_id
    )

    qr_code_in = QRCodeBase(
        employee_id=employee_id,
        token_hash=token_hash,
        expires_at=expiration_date,
    )
    qr_code = crud.create_qr_code(session=session, qr_code=qr_code_in)
    logger.info(
        "QR code record created (id=%s) for employee_id=%s",
        getattr(qr_code, "id", None),
        employee_id,
    )

    try:
        await generate_qr_and_send_email(
            recipient=recipient_email, token=f"{employee_id}:{token}"
        )
        logger.info(
            "QR code email sent to %s for employee_id=%s", recipient_email, employee_id
        )
    except Exception as e:
        logger.exception(
            "Failed to generate/send QR code email for employee_id=%s: %s",
            employee_id,
            e,
        )
        raise HTTPException(status_code=500, detail="Failed to send QR code email.")


@r.delete("/{employee_id}/revoke_qr_code", status_code=204)
def revoke_qr_code_for_employee(
    *, user: User = Depends(current_user), employee_id: int, session: SessionDep
) -> None:
    logger.info(
        "User %s requested QR code revocation for employee_id=%s",
        getattr(user, "email", str(user)),
        employee_id,
    )
    employee = crud.get_employee(session=session, employee_id=employee_id)
    if employee is None:
        logger.error("Employee not found for QR revocation, ID=%s", employee_id)
        raise HTTPException(status_code=404, detail="Employee not found.")
    crud.revode_qr_code(session=session, employee_id=employee_id)
    logger.info("QR code revoked for employee_id=%s", employee_id)

