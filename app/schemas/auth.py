from pydantic import BaseModel, EmailStr

class UserRegistration(BaseModel):
    email: str
    first_name: str
    last_name: str
    username: str
    phone_number: int
    nic_passport: str
    location: str
    password: EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str