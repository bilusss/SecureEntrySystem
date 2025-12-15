from pathlib import Path
import sys
import os
from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig

load_dotenv()


BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))
UPLOAD_DIR = BASE_DIR / "uploads"
TEST_UPLOAD_DIR = BASE_DIR / "tests" / "test_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
DATABASE_URL = "sqlite:///api.db"
TEST_DATABASE_URL = "sqlite:///memory:test.db"

TESTING = os.getenv("TESTING", "false") == "true"

if not TESTING:
    mail_config = ConnectionConfig(
        MAIL_USERNAME="dummy_user@example.com",
        MAIL_PASSWORD="dummy_password",
        MAIL_FROM="dummy_user@example.com",
        MAIL_PORT=587,
        MAIL_SERVER="smtp.example.com",
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
    )
else:
    mail_config = ConnectionConfig(
        MAIL_USERNAME="test_user",
        MAIL_PASSWORD="test_password",
        MAIL_FROM="test@test.com",
        MAIL_PORT=1025,
        MAIL_SERVER="localhost",
        MAIL_STARTTLS=False,
        MAIL_SSL_TLS=False,
    )