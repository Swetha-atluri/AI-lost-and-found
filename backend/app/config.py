import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
MOCK_EMAIL_DIR = BASE_DIR / "mock_emails"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MOCK_EMAIL_DIR.mkdir(parents=True, exist_ok=True)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/lost_found.db")

# JWT Security Configurations
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey_for_ai_lost_found_assistant_123456!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# AI Matching Configuration
# Score ranges from 0.0 (no match) to 1.0 (exact match)
# 0.60 is generally a solid threshold for combined semantic and image matching
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.60"))
TEXT_WEIGHT = 0.5
IMAGE_WEIGHT = 0.5

# SMTP Email Configuration (Optional - for real email sending)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "lostandfound@example.com")
