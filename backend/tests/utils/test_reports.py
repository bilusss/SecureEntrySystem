import pytest

from app.utils import generate_report_pdf, send_report_email


def test_generate_report_pdf_generates_pdf_bytes():
    data = [
        {"employee_id": 1, "first_name": "Jan", "last_name": "Kowalski", "total_hours": 5.5},
        {"employee_id": 2, "first_name": "Anna", "last_name": "Nowak", "total_hours": 3.0},
    ]

    pdf_bytes = generate_report_pdf(data, days=7)

    # Basic sanity checks
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 100  # non-empty content
    assert pdf_bytes.startswith(b"%PDF")  # reportlab outputs PDF header


@pytest.mark.anyio
async def test_send_report_email_uses_fastmail(monkeypatch):
    sent = {}

    class DummyFastMail:
        def __init__(self, config):  # noqa: D401 - test double
            self.config = config

        async def send_message(self, message):
            sent["message"] = message

    monkeypatch.setattr("app.utils.FastMail", DummyFastMail)

    pdf_content = b"%PDF-1.4 dummy"
    await send_report_email("admin@example.com", pdf_content, days=3)

    assert "message" in sent
    msg = sent["message"]
    # recipients is list of NameEmail objects
    assert any(getattr(r, "email", "") == "admin@example.com" for r in msg.recipients)
    # attachments may be UploadFile or (UploadFile, meta)
    def _filename(att):
        if isinstance(att, tuple):
            att = att[0]
        return getattr(att, "filename", "")

    assert any(_filename(att).startswith("raport_czasu_pracy_") for att in msg.attachments)
