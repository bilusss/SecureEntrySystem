import io
import numpy as np
from fastapi import UploadFile

from app.settings import TEST_PHOTOS_DIR
from app.utils import verify_face

# IMPORTANT: Altering names/deleting files in test_uploads directory may break tests below

def test_verify_face_match():
    photo_path = TEST_PHOTOS_DIR / "user_1.png"

    # user_1 and user_1_2 are the same person but different photos
    # 
    with open(TEST_PHOTOS_DIR / "user_1_2.png", "rb") as f:
        file_bytes = UploadFile(
            file=io.BytesIO(f.read()),
            filename="user_1_2.png"
        )
    result = verify_face(str(photo_path), file_bytes)

    assert result == True


def test_verify_face_no_match():
    photo_path = TEST_PHOTOS_DIR / "user_1.png"

    # user_1 and user_2 are different people
    with open(TEST_PHOTOS_DIR / "user_2.png", "rb") as f:
        file_bytes = UploadFile(
            file=io.BytesIO(f.read()),
            filename="user_2.png"
        )
    result = verify_face(str(photo_path), file_bytes)

    assert result == False
