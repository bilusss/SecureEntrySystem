from datetime import datetime, timedelta

from app import crud
from app.models import Employee, EntryExitRecord


def test_toggle_employee_presence(session):
    emp = Employee(email="e1@example.com", first_name="Jan", last_name="Kowalski", photo_path="p1")
    session.add(emp)
    session.commit()
    session.refresh(emp)

    assert emp.is_present is False

    new_state = crud.toggle_employee_presence(session=session, employee_id=emp.id)
    assert new_state is True

    new_state = crud.toggle_employee_presence(session=session, employee_id=emp.id)
    assert new_state is False


def test_get_last_successful_entry(session):
    emp = Employee(email="e2@example.com", first_name="Anna", last_name="Nowak", photo_path="p2")
    session.add(emp)
    session.commit()
    session.refresh(emp)

    now = datetime.now()
    records = [
        EntryExitRecord(
            employee_id=emp.id,
            timestamp=now - timedelta(minutes=30),
            successful=True,
            is_entry=True,
        ),
        EntryExitRecord(
            employee_id=emp.id,
            timestamp=now - timedelta(minutes=10),
            successful=True,
            is_entry=True,
        ),
        EntryExitRecord(
            employee_id=emp.id,
            timestamp=now - timedelta(minutes=5),
            successful=True,
            is_entry=False,
        ),
    ]
    session.add_all(records)
    session.commit()

    last_entry = crud.get_last_successful_entry(session=session, employee_id=emp.id)
    assert last_entry is not None
    # Should be the most recent successful entry with is_entry=True (10 minutes ago)
    assert abs((last_entry.timestamp - (now - timedelta(minutes=10))).total_seconds()) < 1


def test_create_work_time_record_and_filter(session):
    emp = Employee(email="e3@example.com", first_name="Piotr", last_name="Zielinski", photo_path="p3")
    session.add(emp)
    session.commit()
    session.refresh(emp)

    start = datetime.now() - timedelta(hours=2)
    end = datetime.now()

    record = crud.create_work_time_record(
        session=session,
        employee_id=emp.id,
        entry_time=start,
        exit_time=end,
    )

    assert record.duration_minutes == 120
    assert record.employee_id == emp.id

    recent = crud.get_work_time_records(session=session, timedelta_days=1)
    assert any(r.id == record.id for r in recent)
