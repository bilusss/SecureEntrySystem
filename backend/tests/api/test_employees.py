from fastapi.testclient import TestClient
from tests.factories import EmployeeFactory
from io import BytesIO
from random import choice
from PIL import Image


def test_create_employee(client: TestClient):
    employee_data = EmployeeFactory.build()

    img_buf = BytesIO()
    Image.new("RGB", (10, 10), color=choice(["red", "blue", "white"])).save(img_buf, format="JPEG")
    img_buf.seek(0)

    response = client.post(
        "api/employees/",
        data={
            "email": employee_data.email,
            "first_name": employee_data.first_name,
            "last_name": employee_data.last_name,
        },
        files={"photo": ("avatar.jpg", img_buf, "image/jpeg")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == employee_data.email
    assert "id" in data
    print(employee_data)

def test_list_employees(client: TestClient):
    pass

def test_update_employee(client: TestClient):
    pass

def test_delete_employee(client: TestClient):
    pass

def test_get_employee(client: TestClient):
    pass

def test_create_employee_invalid_data(client: TestClient):
    pass

def test_update_employee_invalid_data(client: TestClient):
    pass

def test_create_employee_duplicate_email(client: TestClient):
    pass

def test_update_employee_duplicate_email(client: TestClient):
    pass

def test_delete_nonexistent_employee(client: TestClient):
    pass

def test_get_nonexistent_employee(client: TestClient):
    pass

