from pydantic import BaseModel, EmailStr
from typing import Optional

class Profile(BaseModel):
    firstname: Optional[str]
    lastname: Optional[str]
    username: Optional[str]
    email: EmailStr
    contactInfo: Optional[int]
    dateOfBirth: Optional[str]
    profilePic: Optional[str]
    bio: Optional[str]
    type: Optional[int]