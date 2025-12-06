from app import settings
import os 
import shutil

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
