import cv2
from infrastructure.camera import capture_photo


def test_capture_photo_display():
    """
    MANUAL TEST:
    - takes a photo
    - displays the frame
    - closes the window after a key press
    """

    frame = capture_photo()

    assert frame is not None
    assert frame.size > 0

    cv2.imshow("Captured frame - press any key", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
