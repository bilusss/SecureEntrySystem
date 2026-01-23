import pytest
from datetime import datetime, timedelta

from app.main import app
from app.models import Employee, WorkTimeRecord
from app.users import current_active_user


@pytest.mark.anyio
async def test_generate_raport_aggregates_and_sends(client, session, monkeypatch):
	# Override auth dependency to provide a current active user with an email
	user = type("U", (), {"email": "admin@example.com"})()
	app.dependency_overrides[current_active_user] = lambda: user

	now = datetime.now()

	# Create employees
	e1 = Employee(email="e1@example.com", first_name="Jan", last_name="Kowalski", photo_path="p1.png")
	e2 = Employee(email="e2@example.com", first_name="Anna", last_name="Nowak", photo_path="p2.png")
	session.add_all([e1, e2])
	session.commit()
	session.refresh(e1)
	session.refresh(e2)

	# Work time records within last 30 days
	r1 = WorkTimeRecord(
		employee_id=e1.id,
		date=now.date(),
		entry_time=now - timedelta(hours=3),
		exit_time=now - timedelta(hours=1),
		duration_minutes=120,
	)
	r2 = WorkTimeRecord(
		employee_id=e1.id,
		date=now.date(),
		entry_time=now - timedelta(days=1, hours=2),
		exit_time=now - timedelta(days=1, hours=1),
		duration_minutes=60,
	)
	r3 = WorkTimeRecord(
		employee_id=e2.id,
		date=now.date(),
		entry_time=now - timedelta(hours=4),
		exit_time=now - timedelta(hours=2, minutes=30),
		duration_minutes=90,
	)
	session.add_all([r1, r2, r3])
	session.commit()

	captured = {}

	def fake_pdf(data, days):
		captured["pdf_data"] = data
		captured["pdf_days"] = days
		return b"%PDF-1.4 mock"

	async def fake_send(email, pdf, days):
		captured["sent"] = {"email": email, "pdf": pdf, "days": days}

	monkeypatch.setattr("app.api.entries.generate_report_pdf", fake_pdf)
	monkeypatch.setattr("app.api.entries.send_report_email", fake_send)

	response = client.post("/api/entries/generate-raport", params={"days": 30})
	app.dependency_overrides.pop(current_active_user, None)

	assert response.status_code == 200
	body = response.json()

	assert body["employees_count"] == 2
	assert body["total_hours"] == pytest.approx(4.5)  # 120+60+90 minutes -> 4.5 hours

	# Check that PDF generation received aggregated data sorted by employee_id
	assert captured["pdf_days"] == 30
	assert len(captured["pdf_data"]) == 2
	assert captured["pdf_data"][0]["employee_id"] == e1.id
	assert captured["pdf_data"][0]["total_hours"] == pytest.approx(3.0)
	assert captured["pdf_data"][1]["employee_id"] == e2.id
	assert captured["pdf_data"][1]["total_hours"] == pytest.approx(1.5)

	# Ensure email send is scheduled with current user email
	assert captured["sent"]["email"] == "admin@example.com"
	assert captured["sent"]["days"] == 30
