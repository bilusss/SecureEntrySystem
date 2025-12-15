import cv2

def test_camera_live_preview():
    cap = cv2.VideoCapture(0)
    assert cap.isOpened(), "Nie udało się otworzyć kamerki"

    print("Naciśnij 'q', aby zakończyć podgląd...")
    while True:
        ret, frame = cap.read()
        assert ret, "Nie udało się przechwycić obrazu z kamerki"

        cv2.imshow("Podgląd kamery", frame)

        # naciśnij 'q', aby zamknąć okno
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
