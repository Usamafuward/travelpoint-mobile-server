from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
import pyotp

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME = "your_email@example.com",  # Update with your email
    MAIL_PASSWORD = "your_password",  # Update with your email password or app-specific password
    MAIL_FROM = "your_email@example.com",  # Update with your email
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.example.com",  # Example: "smtp.gmail.com"
    MAIL_TLS = True,
    MAIL_SSL = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True,
)

# OTP generator
def generate_otp() -> str:
    otp = pyotp.random_base32()
    return otp

# Send OTP function
async def send_otp_email(email: EmailStr, otp: str) -> None:
    message = MessageSchema(
        subject="Your OTP Code",
        recipients=[email],
        body=f"Your OTP code is: {otp}",
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message)

# Store OTP in memory (or database/cache in real-world scenarios)
otp_storage = {}  # In-memory storage for demo purposes

# Function to save OTP
def save_otp(email: str, otp: str) -> None:
    otp_storage[email] = otp

# Function to validate OTP
def validate_otp(email: str, otp: str) -> bool:
    stored_otp = otp_storage.get(email)
    return stored_otp == otp
