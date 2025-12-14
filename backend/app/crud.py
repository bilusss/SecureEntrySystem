from typing import Sequence, Any
from sqlmodel import Session, select, false
from datetime import date
from fastapi import HTTPException
from app.models import Employee, QRCode, EntryExitRecord
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