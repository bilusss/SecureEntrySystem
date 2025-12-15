import os
import pytest
from app.utitls import verify_face

@pytest.mark.manual
def test_verify_face_live_real_camera():
    """
    TEST MANUALNY:
    - Otwiera kamerkę
    - Pokazuje podgląd
    - Zwraca True jeśli twarz pasuje do zdjęcia
    - Zamknij okno klawiszem 'q'
    """

    reference_photo = "uploads/foto.jpeg"

    assert os.path.exists(reference_photo), (
        "Brak zdjęcia referencyjnego assets/reference.jpg"
    )

    result = verify_face(
        stored_photo_path=reference_photo,
        tolerance=0.5
    )

    assert result is True, "Twarz NIE zgadza się ze zdjęciem referencyjnym"
