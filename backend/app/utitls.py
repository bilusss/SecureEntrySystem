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
    """
    Robi jedno zdjęcie z kamerki i porównuje twarz ze zdjęciem referencyjnym
    """

    # --- Wczytaj zdjęcie z bazy ---
    known_image = face_recognition.load_image_file(stored_photo_path)
    known_encodings = face_recognition.face_encodings(known_image)

    if not known_encodings:
        print("Brak twarzy na zdjęciu referencyjnym")
        return False

    known_encoding = known_encodings[0]

    # --- Uruchom kamerkę ---
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Nie można otworzyć kamerki")

    try:
        ret, frame = cap.read()
        if not ret:
            print("Nie udało się zrobić zdjęcia")
            return False
    finally:
        cap.release()

    # --- Przetwarzanie zdjęcia z kamerki ---
    rgb_frame = frame[:, :, ::-1]  # BGR -> RGB
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    if not face_encodings:
        print("Nie wykryto twarzy na zdjęciu z kamerki")
        return False

    # --- Porównanie (pierwsza wykryta twarz) ---
    match = face_recognition.compare_faces(
        [known_encoding],
        face_encodings[0],
        tolerance=tolerance
    )[0]

    return match
