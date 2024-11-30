from pydantic import BaseModel, EmailStr

class UserRegistration(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    username: str
    phone_number: int
    nic_passport: str
    location: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class OTPVerification(BaseModel):
    email: str
    otp: str