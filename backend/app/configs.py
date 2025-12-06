from pathlib import Path
import sys
import os

BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))
UPLOAD_DIR = BASE_DIR / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)