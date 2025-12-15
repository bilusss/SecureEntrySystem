import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from fastapi import UploadFile
from io import BytesIO

from app.utitls import verify_face


@pytest.fixture
def fake_upload_file():
    return UploadFile(
        filename="test.jpg",
        file=BytesIO(b"fake-image-content")
    )


@patch("app.utitls.os.remove")
@patch("app.utitls.face_recognition.compare_faces")
@patch("app.utitls.face_recognition.face_encodings")
@patch("app.utitls.face_recognition.load_image_file")
@patch("app.utitls.cv2.imwrite")
@patch("app.utitls.cv2.VideoCapture")
def test_verify_face_success(
    mock_video_capture,
    mock_imwrite,
    mock_load_image,
    mock_face_encodings,
    mock_compare_faces,
    mock_os_remove,
    fake_upload_file,
):
    # 🎥 mock kamerki
    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.read.return_value = (True, np.zeros((100, 100, 3)))
    mock_video_capture.return_value = cap

    # 🖼 mock obrazów
    mock_load_image.return_value = np.zeros((100, 100, 3))

    # 🙂 mock encodingów twarzy
    fake_encoding = np.zeros(128)
    mock_face_encodings.side_effect = [
        [fake_encoding],  # known
        [fake_encoding],  # unknown
    ]

    # 🔍 mock porównania
    mock_compare_faces.return_value = [True]

    result = verify_face(
        uploaded_photo=fake_upload_file,
        stored_photo_path="stored.jpg"
    )

    assert result is True
    mock_compare_faces.assert_called_once()


@patch("app.utitls.cv2.VideoCapture")
def test_verify_face_camera_not_opened(mock_video_capture):
    cap = MagicMock()
    cap.isOpened.return_value = False
    mock_video_capture.return_value = cap

    with pytest.raises(RuntimeError):
        verify_face(
            uploaded_photo=None,
            stored_photo_path="stored.jpg"
        )
