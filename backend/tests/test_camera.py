import cv2
from infrastructure.camera import capture_photo


def test_capture_photo_display():
    """
    TEST MANUALNY:
    - robi zdjęcie
    - wyświetla klatkę
    - zamyka okno po naciśnięciu klawisza
    """

    frame = capture_photo()

    assert frame is not None
    assert frame.size > 0

    cv2.imshow("Captured frame - press any key", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
