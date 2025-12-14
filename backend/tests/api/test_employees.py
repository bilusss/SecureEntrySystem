import shutil
from io import BytesIO
from random import choice

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import select

from app import settings
from app.models import Employee, QRCode
from tests.factories import EmployeeFactory


def _build_photo():
    img_buf = BytesIO()
    Image.new("RGB", (10, 10), color=choice(["red", "blue", "white"])).save(
        img_buf, format="JPEG"
    )
    img_buf.seek(0)
    return img_buf


@pytest.fixture(autouse=True)
def testing_env(monkeypatch):
    monkeypatch.setenv("TESTING", "true")
    yield
    # Keep uploads directory clean between tests
    upload_dir = settings.TEST_UPLOAD_DIR
    if upload_dir.exists():
        shutil.rmtree(upload_dir)


def _create_employee(client: TestClient):
    employee_data = EmployeeFactory.build()
    response = client.post(
        "/api/employees/",
        data={
            "email": employee_data.email,
            "first_name": employee_data.first_name,
            "last_name": employee_data.last_name,
        },
        files={"photo": ("avatar.jpg", _build_photo(), "image/jpeg")},
    )
    assert response.status_code == 201
    return employee_data, response.json()


def test_create_employee(client: TestClient, override_auth):
    employee_data = EmployeeFactory.build()
    response = client.post(
        "/api/employees/",
        data={
            "email": employee_data.email,
            "first_name": employee_data.first_name,
            "last_name": employee_data.last_name,
        },
        files={"photo": ("avatar.jpg", _build_photo(), "image/jpeg")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == employee_data.email
    assert data["first_name"] == employee_data.first_name
    assert data["last_name"] == employee_data.last_name
    assert data["photo_path"] == f"user_{data['id']}.png"


def test_list_employees(client: TestClient, override_auth):
    first, created_first = _create_employee(client)
    second, created_second = _create_employee(client)

    response = client.get("/api/employees/")
    assert response.status_code == 200

    data = response.json()
    emails = {emp["email"] for emp in data}
    assert created_first["email"] in emails
    assert created_second["email"] in emails
    assert len(data) == 2


def test_update_employee(client: TestClient, override_auth, session):
    _, created = _create_employee(client)
    employee_id = created["id"]

    response = client.put(
        f"/api/employees/{employee_id}",
        data={"first_name": "New", "last_name": "Name"},
        files={"photo": ("avatar.jpg", _build_photo(), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "New"
    assert data["last_name"] == "Name"
    assert data["photo_path"] == f"user_{employee_id}.png"

    db_employee = session.exec(select(Employee).where(Employee.id == employee_id)).one()
    assert db_employee.first_name == "New"
    assert db_employee.photo_path == f"user_{employee_id}.png"


def test_delete_employee(client: TestClient, override_auth):
    _, created = _create_employee(client)
    employee_id = created["id"]

    response = client.delete(f"/api/employees/{employee_id}")
    assert response.status_code == 204

    response = client.get("/api/employees/")
    assert response.status_code == 200
    assert all(emp["id"] != employee_id for emp in response.json())


def test_create_employee_invalid_data(client: TestClient, override_auth):
    response = client.post(
        "/api/employees/",
        data={"email": "not-an-email", "first_name": "x", "last_name": "y"},
        files={"photo": ("avatar.jpg", _build_photo(), "image/jpeg")},
    )

    assert response.status_code == 422


def test_update_employee_invalid_data(client: TestClient, override_auth):
    _, created = _create_employee(client)
    employee_id = created["id"]

    response = client.put(
        f"/api/employees/{employee_id}",
        data={"email": "not-an-email"},
    )

    assert response.status_code == 422


def test_create_employee_duplicate_email(client: TestClient, override_auth):
    employee_data = EmployeeFactory.build()
    first_resp = client.post(
        "/api/employees/",
        data={
            "email": employee_data.email,
            "first_name": employee_data.first_name,
            "last_name": employee_data.last_name,
        },
        files={"photo": ("avatar.jpg", _build_photo(), "image/jpeg")},
    )
    assert first_resp.status_code == 201

    second_resp = client.post(
        "/api/employees/",
        data={
            "email": employee_data.email,
            "first_name": "Other",
            "last_name": "Person",
        },
        files={"photo": ("avatar.jpg", _build_photo(), "image/jpeg")},
    )

    assert second_resp.status_code == 400
    assert second_resp.json()["detail"] == "Employee with this email already exists."


def test_update_employee_duplicate_email(client: TestClient, override_auth):
    first, created_first = _create_employee(client)
    second, created_second = _create_employee(client)

    response = client.put(
        f"/api/employees/{created_second['id']}",
        data={"email": created_first["email"]},
    )

    assert response.status_code == 400


def test_delete_nonexistent_employee(client: TestClient, override_auth):
    response = client.delete("/api/employees/9999")
    assert response.status_code == 404


def test_generate_and_revoke_qr_code(client: TestClient, override_auth, session, monkeypatch):
    _, created = _create_employee(client)
    employee_id = created["id"]

    async def _fake_send(*, recipient: str, token: str):  # noqa: ANN001
        return None

    monkeypatch.setattr("app.api.employees.generate_qr_and_send_email", _fake_send)

    generate_resp = client.post(f"/api/employees/{employee_id}/generate_qr_code")
    assert generate_resp.status_code == 204

    qr_codes = session.exec(
        select(QRCode).where(QRCode.employee_id == employee_id, QRCode.is_revoked == False)  # noqa: E712
    ).all()
    assert len(qr_codes) == 1

    revoke_resp = client.delete(f"/api/employees/{employee_id}/revoke_qr_code")
    assert revoke_resp.status_code == 204

    qr_codes = session.exec(select(QRCode).where(QRCode.employee_id == employee_id)).all()
    assert qr_codes[0].is_revoked is True

