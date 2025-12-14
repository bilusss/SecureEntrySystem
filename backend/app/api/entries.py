# dostaje qr code i twarz i sprawdza i daje access albo no access i zapisuje entrance/wyjsice
# generowanie raportu + export do pdfa]
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Form, UploadFile, HTTPException
from app import crud
from app.db import SessionDep
from app.utitls import verify_token, verify_face, save_photo
from app.models import EntryExitRecord

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


entries_router = r = APIRouter(prefix="/entries")


@r.post("/", status_code=201)
async def entrance(
    *,
    session: SessionDep,
    qr_code_payload: str = Form(...),
    photo: UploadFile,
):
    """Handle employee entrance using QR code and face recognition."""
    logger.info("Entrance attempt received.")
    employee_id, qr_code_token = qr_code_payload.split(":")
    try:
        int(employee_id)
    except ValueError:
        logger.error("Invalid employee ID in QR code payload.")
        raise HTTPException(
            status_code=400,
            detail="Invalid QR code payload.",
        )
    logger.info(f"Processing entrance for employee ID: {employee_id}")
    qr_code = crud.get_active_qr_code(session=session, employee_id=int(employee_id))
    employee = crud.get_employee(session=session, employee_id=int(employee_id))

    initial_record = EntryExitRecord(
        employee_id=int(employee_id),
        timestamp=datetime.now(),
        successful=False,
    )
    record = crud.create_entry_exit_record(session=session, record=initial_record)
    save_photo(f"entrance_attempt_{record.id}.png", photo)

    if employee.photo_path is None:
        logger.error("Employee has no photo for face verification.")
        record.denial_reason = "User has no photo in the system."
        crud.update_entry_exit_record(session=session, record=record)
        raise HTTPException(
            status_code=404,
            detail="Employee has no photo. Please update profile with a photo.",
        )

    if qr_code is None:
        logger.error("No active QR code found for this employee.")
        record.denial_reason = "User has no active QR code."
        crud.update_entry_exit_record(session=session, record=record)
        raise HTTPException(
            status_code=400,
            detail="No active QR code found for this employee.",
        )

    if not verify_token(qr_code_token, qr_code.token_hash):
        logger.error("Invalid QR code token provided.")
        record.denial_reason = "Invalid QR code token."
        crud.update_entry_exit_record(session=session, record=record)
        raise HTTPException(
            status_code=401,
            detail="Invalid QR code token.",
        )
    if not verify_face(photo, employee.photo_path):
        logger.error("Face verification failed.")
        record.denial_reason = "Face verification failed."
        crud.update_entry_exit_record(session=session, record=record)
        raise HTTPException(
            status_code=401,
            detail="Face verification failed.",
        )

    save_photo(f"user_{employee.id}.png", photo)
    record.successful = True
    crud.update_entry_exit_record(session=session, record=record)
    logger.info(f"Entrance granted for employee ID: {employee_id}")


@r.post("/generate-raport", status_code=200)
async def generate_raport(*, session: SessionDep):
    """Generate entrance/exit report."""
    logger.info("Report generation requested.")
    # Placeholder for report generation logic
    # In a real implementation, this would involve querying the database
    # for entrance/exit records and compiling them into a report format (e.g., PDF).
    logger.info("Report generated successfully.")
