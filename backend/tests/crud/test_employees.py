from tests.factories import EmployeeFactory
from app import crud

# Session is automatically provided by pytest fixture
def test_create_employee(session):
    employee_data = EmployeeFactory.build()
    employee = crud.create_employee(session=session, employee=employee_data)
    assert employee.email == employee_data.email
    assert employee.first_name == employee_data.first_name
    assert employee.last_name == employee_data.last_name
