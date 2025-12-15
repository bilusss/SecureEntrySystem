import os
import shutil
import qrcode
import io
import hashlib
import hmac
from fastapi import UploadFile
from fastapi_mail import FastMail, MessageSchema
from app import settings
from app.settings import mail_config
import cv2
import face_recognition
import tempfile


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

def verify_face(stored_photo_path: str, tolerance: float = 0.5) -> bool:

    # Wczytaj obraz referencyjny
    known_image = face_recognition.load_image_file(stored_photo_path)
    known_encodings = face_recognition.face_encodings(known_image)
    if not known_encodings:
        print("Nie znaleziono twarzy na zdjęciu referencyjnym")
        return False
    known_encoding = known_encodings[0]

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Nie można otworzyć kamerki")

    print("Naciśnij 'q', aby zakończyć podgląd")
    match_found = False

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Błąd odczytu z kamery")
                break

            rgb_frame = frame[:, :, ::-1]  # BGR -> RGB
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=tolerance)
                if matches[0]:
                    color = (0, 255, 0)
                    label = "MATCH"
                    match_found = True
                else:
                    color = (0, 0, 255)
                    label = "NO MATCH"

                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

            cv2.imshow('Live Face Verification', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

    return match_found