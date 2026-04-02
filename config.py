import os
from dotenv import load_dotenv

# Load environment variables from .env file, overriding any stale shell vars
load_dotenv(override=True)

class Config:
    # ─── Security ────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ironforge-ng-change-in-production-2024')

    # ─── Database ─────────────────────────────────────────────────────────────
    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
    # Render provides 'postgres://', but SQLAlchemy requires 'postgresql://'
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
