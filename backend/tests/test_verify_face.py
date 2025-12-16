import numpy as np
from unittest.mock import patch, MagicMock

from app.utitls import verify_face


@patch("app.utitls.face_recognition.compare_faces")
@patch("app.utitls.face_recognition.face_encodings")
@patch("app.utitls.face_recognition.face_locations")
@patch("app.utitls.face_recognition.load_image_file")
@patch("app.utitls.cv2.VideoCapture")
def test_verify_face_match(
    mock_video_capture,
    mock_load_image,
    mock_face_locations,
    mock_face_encodings,
    mock_compare_faces,
):
    # --- zdjęcie z bazy ---
    mock_load_image.return_value = np.zeros((100, 100, 3))

    mock_face_encodings.side_effect = [
        [np.array([0.1, 0.2, 0.3])],  # encoding z bazy
        [np.array([0.1, 0.2, 0.3])]   # encoding z kamerki
    ]

    mock_face_locations.return_value = [(0, 50, 50, 0)]
    mock_compare_faces.return_value = [True]

    # --- kamerka ---
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.read.return_value = (True, fake_frame)
    mock_video_capture.return_value = cap

    result = verify_face("fake_path.jpg")

    assert result is True


@patch("app.utitls.face_recognition.face_encodings")
@patch("app.utitls.face_recognition.load_image_file")
@patch("app.utitls.cv2.VideoCapture")
def test_verify_face_no_face_on_camera(
    mock_video_capture,
    mock_load_image,
    mock_face_encodings,
):
    mock_load_image.return_value = np.zeros((100, 100, 3))

    mock_face_encodings.side_effect = [
        [np.array([0.1, 0.2, 0.3])],  # z bazy
        []                            # z kamerki
    ]

    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.read.return_value = (True, fake_frame)
    mock_video_capture.return_value = cap

    result = verify_face("fake_path.jpg")

    assert result is False
