# app/infrastructure/camera.py
import cv2


def capture_photo() -> "np.ndarray":
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Nie można otworzyć kamerki")

    try:
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Nie udało się zrobić zdjęcia")
        return frame
    finally:
        cap.release()
