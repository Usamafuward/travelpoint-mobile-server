from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
import random

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME = "travelpoint192@gmail.com",  # Update with your email
    MAIL_PASSWORD = "fkfb ncht xsbx lari",  # Update with your email password or app-specific password
    MAIL_FROM = "travelpoint192@gmail.com",  # Update with your email
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",  # Example: "smtp.gmail.com"
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

# OTP generator
def generate_otp() -> str:
    otp = f"{random.randint(100000, 999999)}"
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
