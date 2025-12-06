from pathlib import Path
import sys
import os


BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))
UPLOAD_DIR = BASE_DIR / "uploads"
TEST_UPLOAD_DIR = BASE_DIR / "tests" / "test_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
DATABASE_URL = "sqlite:///api.db"
TEST_DATABASE_URL = "sqlite:///memory:test.db"