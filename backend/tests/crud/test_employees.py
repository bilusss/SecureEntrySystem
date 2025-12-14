from datetime import date, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from sqlmodel import select

from app import crud
from app.models import QRCode
from app.schemas import EmployeeUpdate, QRCodeBase
from tests.factories import EmployeeFactory


def test_create_and_get_employee(session):
	employee_data = EmployeeFactory.build()

	created = crud.create_employee(session=session, employee=employee_data)

	assert created.id is not None
	assert created.email == employee_data.email

	fetched = crud.get_employee(session=session, employee_id=created.id)
	assert fetched.email == employee_data.email


def test_get_employee_not_found(session):
	with pytest.raises(HTTPException) as excinfo:
		crud.get_employee(session=session, employee_id=999)

	assert excinfo.value.status_code == 404


def test_get_employee_by_email(session):
	employee_data = EmployeeFactory.build()
	created = crud.create_employee(session=session, employee=employee_data)

	fetched = crud.get_employee_by_email(session=session, email=employee_data.email)
	assert fetched is not None
	assert fetched.id == created.id


def test_list_employees(session):
	first = crud.create_employee(session=session, employee=EmployeeFactory.build())
	second = crud.create_employee(session=session, employee=EmployeeFactory.build())

	employees = crud.list_employees(session=session)
	ids = {emp.id for emp in employees}

	assert first.id in ids and second.id in ids
	assert len(employees) == 2


def test_update_employee_partial(session):
	employee_data = EmployeeFactory.build()
	created = crud.create_employee(session=session, employee=employee_data)

	updated = crud.update_employee(
		session=session,
		employee_id=created.id,
		employee_in=EmployeeUpdate(first_name="NewName"),
	)

	assert updated.first_name == "NewName"
	assert updated.last_name == employee_data.last_name
	assert updated.email == employee_data.email


def test_update_employee_duplicate_email(session):
	first = crud.create_employee(session=session, employee=EmployeeFactory.build())
	second = crud.create_employee(session=session, employee=EmployeeFactory.build())

	with pytest.raises(IntegrityError):
		crud.update_employee(
			session=session,
			employee_id=second.id,
			employee_in=EmployeeUpdate(email=first.email),
		)


def test_delete_employee(session):
    created = crud.create_employee(session=session, employee=EmployeeFactory.build())

    crud.delete_employee(session=session, employee_id=created.id)

	with pytest.raises(HTTPException):
		crud.get_employee(session=session, employee_id=created.id)


def test_qr_code_lifecycle(session):
	employee = crud.create_employee(session=session, employee=EmployeeFactory.build())
	qr1 = crud.create_qr_code(
		session=session,
		qr_code=QRCodeBase(
			employee_id=employee.id,
			token_hash="hash1",
			expires_at=date.today() + timedelta(days=1),
		),
	)

	active = crud.get_active_qr_code(session=session, employee_id=employee.id)
	assert active is not None and active.id == qr1.id and active.is_revoked is False

	qr2 = crud.create_qr_code(
		session=session,
		qr_code=QRCodeBase(
			employee_id=employee.id,
			token_hash="hash2",
			expires_at=date.today() + timedelta(days=1),
		),
	)

	# old is revoked, new is active
	stored_qrs = session.exec(select(QRCode).where(QRCode.employee_id == employee.id)).all()
	assert any(q.id == qr1.id and q.is_revoked for q in stored_qrs)
	assert any(q.id == qr2.id and not q.is_revoked for q in stored_qrs)

	crud.revode_qr_code(session=session, employee_id=employee.id)
	latest = crud.get_active_qr_code(session=session, employee_id=employee.id)
	assert latest is None
