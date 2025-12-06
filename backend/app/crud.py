from typing import Sequence, Any
from sqlmodel import Session, select
from fastapi import HTTPException
from app.models import Employee
from app.schemas import EmployeeBase, EmployeeUpdate, EmployeeCreate


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

    update_data: dict[str, Any] = employee_in.model_dump(exclude_unset=True)
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
