import os
import shutil
import qrcode
import io
import hashlib
import hmac
from datetime import datetime, timedelta
from fastapi import UploadFile
from fastapi_mail import FastMail, MessageSchema, MessageType
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from app import settings
from app.settings import mail_config
import cv2
import face_recognition
import numpy as np


def _get_upload_path(file_name: str) -> str:
    print(os.environ.get("TESTING"))
    if os.environ.get("TESTING"):
        upload_dir = settings.TEST_UPLOAD_DIR
    else:
        upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    return str(upload_dir / file_name)


def save_photo(path_name, photo):
    """Saves photo to uploads folder"""
    file_path = _get_upload_path(path_name)
    with open(file_path, "wb") as file:
        shutil.copyfileobj(photo.file, file)


async def generate_qr_and_send_email(*, recipient: str, token: str) -> None:
    """Generates QR code image and sends it via email"""
    qr_img = qrcode.make(token)
    qr_img = qr_img.convert("RGB")
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)

    upload_file = UploadFile(
        file=buffer,
        filename="qrcode.png"
    )
    message = MessageSchema(
        subject="Your QR Code",
        recipients=[recipient],
        body="Here is your QR code. Check the attachment.",
        subtype="plain",
        attachments=[upload_file],
    )

    fm = FastMail(mail_config)
    await fm.send_message(message)

def verify_token(token: str, stored_hash: str) -> bool:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return hmac.compare_digest(token_hash, stored_hash)

def verify_face(
    stored_photo_path: str,
    photo: UploadFile,
    tolerance: float = 0.5
) -> bool:
    """
    Porównuje twarz ze zdjęcia z bazy z twarzą z klatki kamery
    """

    # --- zdjęcie z bazy ---
    photo_path = _get_upload_path(stored_photo_path)
    known_image = face_recognition.load_image_file(photo_path)
    known_encodings = face_recognition.face_encodings(known_image)

    if not known_encodings:
        return False

    known_encoding = known_encodings[0]

    # Change UploadFile to numpy array
    photo.file.seek(0)
    file_bytes = np.frombuffer(photo.file.read(), dtype=np.uint8)
    if file_bytes.size == 0:
        return False

    camera_frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if camera_frame is None:
        return False

    rgb_frame = np.ascontiguousarray(camera_frame[:, :, ::-1])
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    if not face_encodings:
        return False

    return face_recognition.compare_faces(
        [known_encoding],
        face_encodings[0],
        tolerance=tolerance
    )[0]


def generate_report_pdf(report_data: list[dict], days: int) -> bytes:
    """Generate a PDF report with work time summary for the last N days.
    
    Args:
        report_data: List of dicts with employee_id, first_name, last_name, total_hours
        days: Number of days the report covers
        
    Returns:
        PDF file as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Title
    elements.append(Paragraph("Raport Czasu Pracy", styles['Heading1']))
    elements.append(Paragraph(f"Okres: {start_date} - {end_date}", styles['Normal']))
    elements.append(Paragraph(f"Wygenerowano: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Employee rows
    elements.append(Paragraph("ID | Imię | Nazwisko | Godziny", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    total_hours = 0
    for row in report_data:
        line = f"{row['employee_id']} | {row['first_name']} | {row['last_name']} | {row['total_hours']:.2f} h"
        elements.append(Paragraph(line, styles['Normal']))
        total_hours += row['total_hours']
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"SUMA: {total_hours:.2f} h", styles['Heading2']))
    elements.append(Paragraph(f"Liczba pracowników: {len(report_data)}", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


async def send_report_email(recipient_email: str, pdf_content: bytes, days: int) -> None:
    """Send the work time report PDF via email."""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    # Wrap bytes into UploadFile to satisfy fastapi-mail validation
    pdf_file = UploadFile(
        filename=f"raport_czasu_pracy_{start_date}_{end_date}.pdf",
        file=io.BytesIO(pdf_content),
    )

    message = MessageSchema(
        subject=f"Raport Czasu Pracy ({start_date} - {end_date})",
        recipients=[recipient_email],
        body=f"""
        <html>
        <body>
            <h2>Raport Czasu Pracy</h2>
            <p>W załączniku znajduje się raport czasu pracy za ostatnie {days} dni.</p>
            <p>Okres: {start_date} - {end_date}</p>
            <p>Raport zawiera podsumowanie godzin pracy wszystkich pracowników.</p>
            <br>
            <p style="color: gray; font-size: 12px;">
                Wiadomość wygenerowana przez SecureEntrySystem.<br>
                Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </body>
        </html>
        """,
        subtype=MessageType.html,
        attachments=[pdf_file],
    )

    fm = FastMail(mail_config)
    await fm.send_message(message)