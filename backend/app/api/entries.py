# dostaje qr code i twarz i sprawdza i daje access albo no access i zapisuje entrance/wyjsice
# generowanie raportu + export do pdfa]
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Form, UploadFile, HTTPException, BackgroundTasks
from app import crud
from app.db import SessionDep
from app.utils import verify_token, verify_face, save_photo, generate_report_pdf, send_report_email
from app.models import EntryExitRecord, User
from app.users import current_active_user


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


entries_router = r = APIRouter(prefix="/entries")


@r.post("/", status_code=201)
async def gate_access(
    *,
    session: SessionDep,
    qr_code_payload: str = Form(...),
    photo: UploadFile,
):
    """Handle employee entry/exit at the gate using QR code and face recognition.
    
    If employee is not present (is_present=False), this is an entry attempt.
    If employee is present (is_present=True), this is an exit attempt.
    On successful exit, a WorkTimeRecord is created with the duration.
    """
    logger.info("Gate access attempt received.")

    try:
        employee_id, qr_code_token = qr_code_payload.split(":")
    except ValueError:
        logger.error("Invalid QR code payload format.")
        raise HTTPException(
            status_code=400,
            detail="Invalid QR code payload format.",
        )
    try:
        int(employee_id)
    except ValueError:
        logger.error("Invalid employee ID in QR code payload.")
        raise HTTPException(
            status_code=400,
            detail="Invalid QR code payload.",
        )
    
    employee_id_int = int(employee_id)
    logger.info(f"Processing gate access for employee ID: {employee_id}")
    qr_code = crud.get_active_qr_code(session=session, employee_id=employee_id_int)
    employee = crud.get_employee(session=session, employee_id=employee_id_int)

    # Determine if this is an entry or exit based on current presence
    is_entry = not employee.is_present
    action_type = "entry" if is_entry else "exit"
    logger.info(f"This is an {action_type} attempt for employee ID: {employee_id}")

    initial_record = EntryExitRecord(
        employee_id=employee_id_int,
        timestamp=datetime.now(),
        successful=False,
        is_entry=is_entry,
    )
    record = crud.create_entry_exit_record(session=session, record=initial_record)
    save_photo(f"{action_type}_attempt_{record.id}.png", photo)

    # Reset stream after saving attempt snapshot for downstream processing
    if hasattr(photo, "file"):
        photo.file.seek(0)

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
    print("employee photo path:", employee.photo_path)
    # Zamienic photo na camera frame
    if not verify_face(employee.photo_path, photo):
        logger.error("Face verification failed.")
        record.denial_reason = "Face verification failed."
        crud.update_entry_exit_record(session=session, record=record)
        raise HTTPException(
            status_code=401,
            detail="Face verification failed.",
        )

    if hasattr(photo, "file"):
        photo.file.seek(0)
    save_photo(f"user_{employee.id}.png", photo)
    
    # Mark record as successful
    record.successful = True
    crud.update_entry_exit_record(session=session, record=record)
    
    # Toggle presence status
    new_presence = crud.toggle_employee_presence(session=session, employee_id=employee_id_int)
    
    # If this was an exit (employee was present, now is not), create work time record
    work_time_record = None
    if not is_entry:  # This was an exit
        last_entry = crud.get_last_successful_entry(session=session, employee_id=employee_id_int)
        if last_entry:
            work_time_record = crud.create_work_time_record(
                session=session,
                employee_id=employee_id_int,
                entry_time=last_entry.timestamp,
                exit_time=record.timestamp,
            )
            logger.info(
                f"Work time record created for employee {employee_id}: "
                f"{work_time_record.duration_minutes} minutes"
            )
    
    logger.info(f"Gate access granted for employee ID: {employee_id} ({action_type})")
    
    return {
        "message": f"Access granted - {action_type}",
        "employee_id": employee_id_int,
        "is_present": new_presence,
        "action": action_type,
        "work_time_minutes": work_time_record.duration_minutes if work_time_record else None,
    }


@r.post("/generate-raport", status_code=200)
async def generate_raport(
    *,
    session: SessionDep,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    days: int = 30,
):
    """Generate work time report for the last N days and send it via email to the current user.
    
    Args:
        days: Number of days to look back (default: 30)
    """
    logger.info(f"Report generation requested for last {days} days.")
    
    # Get all work time records for the period
    records = crud.get_work_time_records(
        session=session,
        timedelta_days=days,
    )
    
    # Aggregate hours per employee
    employee_hours: dict[int, int] = defaultdict(int)  # employee_id -> total_minutes
    for record in records:
        employee_hours[record.employee_id] += record.duration_minutes
    
    # Build report data with employee info
    report_data = []
    for employee_id, total_minutes in employee_hours.items():
        employee = crud.get_employee(session=session, employee_id=employee_id)
        report_data.append({
            "employee_id": employee_id,
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "total_hours": total_minutes / 60,  # Convert to hours
        })
    
    # Sort by employee_id
    report_data.sort(key=lambda x: x["employee_id"])
    
    # Generate PDF
    pdf_content = generate_report_pdf(report_data, days)
    
    # Send email in background
    background_tasks.add_task(
        send_report_email,
        current_user.email,
        pdf_content,
        days,
    )
    
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    logger.info(f"Report for {start_date} - {end_date} generated and queued for email to {current_user.email}")
    
    return {
        "message": f"Raport za okres {start_date} - {end_date} został wygenerowany i wysłany na {current_user.email}",
        "period_days": days,
        "start_date": start_date,
        "end_date": end_date,
        "employees_count": len(report_data),
        "total_hours": sum(r["total_hours"] for r in report_data),
        "report_data": report_data,
    }
