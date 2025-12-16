import numpy as np
from unittest.mock import patch

from app.utitls import verify_face

@patch("app.utitls.face_recognition.compare_faces")
@patch("app.utitls.face_recognition.face_encodings")
@patch("app.utitls.face_recognition.face_locations")
@patch("app.utitls.face_recognition.load_image_file")
def test_verify_face_match(
    mock_load_image,
    mock_face_locations,
    mock_face_encodings,
    mock_compare_faces,
):
    # --- fake klatka z kamerki ---
    camera_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # --- mock zdjęcia z bazy ---
    mock_load_image.return_value = np.zeros((100, 100, 3))

    # face_encodings wywoływane 2x:
    # 1) dla zdjęcia z bazy
    # 2) dla klatki z kamerki
    mock_face_encodings.side_effect = [
        [np.array([0.1, 0.2, 0.3])],  # baza
        [np.array([0.1, 0.2, 0.3])]   # kamera
    ]

    mock_face_locations.return_value = [(0, 50, 50, 0)]
    mock_compare_faces.return_value = [True]

    result = verify_face("fake_path.jpg", camera_frame)

    assert result is True

@patch("app.utitls.face_recognition.face_encodings")
@patch("app.utitls.face_recognition.load_image_file")
def test_verify_face_no_face_in_database(
    mock_load_image,
    mock_face_encodings,
):
    camera_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    mock_load_image.return_value = np.zeros((100, 100, 3))
    mock_face_encodings.return_value = []  # brak twarzy w bazie

    result = verify_face("fake.jpg", camera_frame)

    assert result is False


@patch("app.utitls.face_recognition.face_encodings")
@patch("app.utitls.face_recognition.face_locations")
@patch("app.utitls.face_recognition.load_image_file")
def test_verify_face_no_face_on_camera(
    mock_load_image,
    mock_face_locations,
    mock_face_encodings,
):
    camera_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    mock_load_image.return_value = np.zeros((100, 100, 3))

    mock_face_encodings.side_effect = [
        [np.array([0.1, 0.2, 0.3])],  # baza
        []                            # kamera
    ]

    mock_face_locations.return_value = []

    result = verify_face("fake.jpg", camera_frame)

    assert result is False
