from app.configs import UPLOAD_DIR
import shutil

def save_photo(path_name, photo):
    """Saves photo to uploads folder"""
    file_path = UPLOAD_DIR / path_name
    with open(file_path, "wb") as file:
        shutil.copyfileobj(photo.file, file)
