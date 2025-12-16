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
        MAIL_USERNAME=os.getenv("EMAIL_HOST_USER", ""),
        MAIL_PASSWORD=os.getenv("EMAIL_HOST_PASSWORD", ""),
        MAIL_FROM=os.getenv("EMAIL_HOST_USER", ""),
        MAIL_PORT=os.getenv("EMAIL_PORT", 578),
        MAIL_SERVER=os.getenv("EMAIL_HOST", "smtp.mailtrap.io"),
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
