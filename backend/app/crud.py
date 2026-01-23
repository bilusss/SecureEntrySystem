from typing import Sequence, Any
from sqlmodel import Session, select, false, desc
from datetime import date, datetime
from fastapi import HTTPException
from app.models import Employee, QRCode, EntryExitRecord, WorkTimeRecord
from app.schemas import EmployeeBase, EmployeeUpdate, EmployeeCreate, QRCodeBase


def create_employee(*, session: Session, employee: EmployeeCreate) -> Employee:
    """Create a new employee.

    Args:
        session (Session): database session   
        employee (EmployeeBase): employee data

    Returns:
        Employee: created employee
    """
    obj = Employee.model_validate(employee)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def list_employees(*, session: Session)-> Sequence[Employee]:
    """List all employees.

    Args:
        session (Session): database session

    Returns:
        Sequence[Employee]: list of employees 
    """
    stmt = select(Employee)
    return session.exec(stmt).all()


def get_employee(*, session: Session, employee_id: int) -> Employee:
    """Get an employee by ID.

    Args:
        session (Session): database session
        employee_id (int): employee ID

    Raises:
        HTTPException: 404 if employee not found

    Returns:
        Employee: employee object
    """
    stmt = select(Employee).where(Employee.id == employee_id)
    employee: Employee | None = session.exec(stmt).first()
    if employee is None:
        raise HTTPException(404, "Employee not found")
    return employee

def get_employee_by_email(*, session: Session, email: str) -> Employee | None:
    """Get an employee by ID.

    Args:
        session (Session): database session
        employee_email (str): employee email

    Raises:
        HTTPException: 404 if employee not found

    Returns:
        Employee: employee object
    """
    stmt = select(Employee).where(Employee.email == email)
    employee: Employee | None = session.exec(stmt).first()
    return employee


def update_employee(*, session: Session, employee_id: int, employee_in: EmployeeUpdate) -> Employee:
    """Update an employee.

    Args:
        session (Session): database session
        employee_id (int): employee ID
        employee_in (EmployeeUpdate): employee data to update
    Returns:
        Employee: updated employee
    """
    employee: Employee = get_employee(session=session, employee_id=employee_id)

    update_data: dict[str, Any] = employee_in.model_dump(
        exclude_unset=True, exclude_none=True
    )
    employee.sqlmodel_update(update_data)
    session.commit()
    session.refresh(employee)
    return employee



def delete_employee(*, session: Session, employee_id: int) -> None:
    """Delete an employee.

    Args:
        session (Session): database session
        employee_id (int): employee ID
    """
    employee: Employee = get_employee(session=session, employee_id=employee_id)
    session.delete(employee)
    session.commit()


def get_active_qr_code(*, session: Session, employee_id: int) -> QRCode | None:
    stmt = select(QRCode).where(
        QRCode.employee_id == employee_id,
        QRCode.is_revoked == false(),
        QRCode.expires_at > date.today()
    )
 
    # Raise exception if more than one active QR code is found
    qr_code: QRCode | None = session.exec(stmt).one_or_none()
    return qr_code

def revode_qr_code(*, session: Session, employee_id: int) -> None:
    qr_code = get_active_qr_code(session=session, employee_id=employee_id)
    if qr_code is None:
        return
    qr_code.is_revoked = True
    session.commit()

def create_qr_code(*, session: Session, qr_code: QRCodeBase) -> QRCode:
    # Deactivate existing active QR codes for the employee
    revode_qr_code(session=session, employee_id=qr_code.employee_id) # Doesnt work?
    obj = QRCode.model_validate(qr_code)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

def create_entry_exit_record(*, session: Session, record: EntryExitRecord) -> EntryExitRecord:
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

def update_entry_exit_record(*, session: Session, record: EntryExitRecord) -> None:
    session.add(record)
    session.commit()

def get_entry_exit_records(
    *,
    session: Session,
    timedelta_days: int,
    successful_only: bool = False,
) -> Sequence[EntryExitRecord]:
    """Return entry/exit records newer than ``timedelta_days``.

    Args:
        session: database session
        timedelta_days: number of days to look back from today
        successful_only: filter only successful attempts when True
    """
    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=timedelta_days)
    cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)

    conditions = [EntryExitRecord.timestamp >= cutoff_date]
    if successful_only:
        conditions.append(EntryExitRecord.successful == True)

    stmt = select(EntryExitRecord).where(*conditions).order_by(EntryExitRecord.timestamp)
    records: Sequence[EntryExitRecord] = session.exec(stmt).all()
    return records


def toggle_employee_presence(*, session: Session, employee_id: int) -> bool:
    """Toggle employee presence status.
    
    Args:
        session: database session
        employee_id: employee ID
        
    Returns:
        bool: New presence status (True = entered, False = exited)
    """
    employee = get_employee(session=session, employee_id=employee_id)
    employee.is_present = not employee.is_present
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee.is_present


def get_last_successful_entry(
    *, session: Session, employee_id: int
) -> EntryExitRecord | None:
    """Get the last successful entry record for an employee.
    
    Args:
        session: database session
        employee_id: employee ID
        
    Returns:
        EntryExitRecord or None if no entry found
    """
    stmt = (
        select(EntryExitRecord)
        .where(
            EntryExitRecord.employee_id == employee_id,
            EntryExitRecord.successful == True,
            EntryExitRecord.is_entry == True,
        )
        .order_by(desc(EntryExitRecord.timestamp))
    )
    return session.exec(stmt).first()


def create_work_time_record(
    *, session: Session, employee_id: int, entry_time: datetime, exit_time: datetime
) -> WorkTimeRecord:
    """Create a work time record when employee exits.
    
    Args:
        session: database session
        employee_id: employee ID
        entry_time: when employee entered
        exit_time: when employee exited
        
    Returns:
        WorkTimeRecord: created work time record
    """
    duration = exit_time - entry_time
    duration_minutes = int(duration.total_seconds() // 60)
    
    record = WorkTimeRecord(
        employee_id=employee_id,
        date=entry_time.date(),
        entry_time=entry_time,
        exit_time=exit_time,
        duration_minutes=duration_minutes,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_work_time_records(
    *,
    session: Session,
    employee_id: int | None = None,
    timedelta_days: int = 30,
) -> Sequence[WorkTimeRecord]:
    """Get work time records.
    
    Args:
        session: database session
        employee_id: optional employee ID to filter by
        timedelta_days: number of days to look back
        
    Returns:
        Sequence[WorkTimeRecord]: list of work time records
    """
    from datetime import timedelta
    
    cutoff_date = datetime.now() - timedelta(days=timedelta_days)
    cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    conditions = [WorkTimeRecord.entry_time >= cutoff_date]
    if employee_id is not None:
        conditions.append(WorkTimeRecord.employee_id == employee_id)
    
    stmt = select(WorkTimeRecord).where(*conditions).order_by(desc(WorkTimeRecord.entry_time))
    return session.exec(stmt).all()