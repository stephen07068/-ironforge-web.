import os
from dotenv import load_dotenv

# Load environment variables from .env file, overriding any stale shell vars
load_dotenv(override=True)

class Config:
    # ─── Security ────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ironforge-ng-change-in-production-2024')

    # ─── Database ─────────────────────────────────────────────────────────────
    # Cloud Run + Cloud SQL: connect via Unix socket (set CLOUD_SQL_CONNECTION_NAME)
    # Format: project:region:instance-name
    _cloud_sql_conn = os.environ.get('CLOUD_SQL_CONNECTION_NAME', '')
    _db_user        = os.environ.get('DB_USER', '')
    _db_pass        = os.environ.get('DB_PASS', '')
    _db_name        = os.environ.get('DB_NAME', 'ironforge')

    if _cloud_sql_conn and _db_user and _db_pass:
        # Unix socket path created by Cloud SQL Auth Proxy on Cloud Run
        _socket_dir = f"/cloudsql/{_cloud_sql_conn}"
        _db_url = (
            f"postgresql+psycopg2://{_db_user}:{_db_pass}@/{_db_name}"
            f"?host={_socket_dir}"
        )
    else:
        # Fallback: use DATABASE_URL (local dev, Render, etc.)
        _db_url = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
        # Render / older Heroku-style URLs use 'postgres://' prefix
        if _db_url.startswith('postgres://'):
            _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ─── Paystack ─────────────────────────────────────────────────────────────
    PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', 'sk_test_your_paystack_secret_key')
    PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', 'pk_test_your_paystack_public_key')

    # ─── Business ─────────────────────────────────────────────────────────────
    WHATSAPP_NUMBER  = '2347044891567'
    BUSINESS_EMAIL   = 'miracleinvestment32@gmail.com'
    BUSINESS_NAME    = 'IronForge Nigeria'

    # ─── Admin ────────────────────────────────────────────────────────────────
    ADMIN_USERNAME    = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD    = os.environ.get('ADMIN_PASSWORD', 'admin123')
    ADMIN_SECRET_PATH = os.environ.get('ADMIN_SECRET_PATH', 'admin')

    # ─── Uploads ──────────────────────────────────────────────────────────────
    UPLOAD_FOLDER     = os.path.join('static', 'images', 'products')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16 MB

    # ─── Email (SMTP) ──────────────────────────────────────────────────────────────
    MAIL_SERVER   = os.environ.get('MAIL_SERVER',   'smtp.gmail.com')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')    # your Gmail address
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')    # Gmail App Password
    ADMIN_EMAIL   = os.environ.get('ADMIN_EMAIL',   '')    # where reset link is sent
    RESET_TOKEN_EXPIRY_HOURS = 1
