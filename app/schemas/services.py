from pydantic import BaseModel
from typing import Optional

class GuideResponse(BaseModel):
    id: int
    user_id: int
    name: str
    language: str
    location: str
    preference: str
    description: Optional[str]
    document_path: Optional[str]
    photo_path: Optional[str]
    created_at: int

class CreateGuideRequest(BaseModel):
    name: str
    language: str
    location: str
    preference: str
    description: Optional[str]

class EquipmentResponse(BaseModel):
    id: int
    owner_id: int
    type: str
    description: Optional[str]
    price_per_day: float
    condition: str
    photo_path: Optional[str]
    created_at: int

class CreateEquipmentRequest(BaseModel):
    name: str
    category: str
    description: Optional[str]
    price_per_day: float
    condition: str
    
class VehicleResponse(BaseModel):
    id: int
    owner_id: int
    type: str
    capacity: int
    milage: float
    price: float
    description: Optional[str]
    document_path: Optional[str]
    photo_path: Optional[str]
    created_at: int

class CreateVehicleRequest(BaseModel):
    type: str
    capacity: int
    milage: float
    price: float
    description: Optional[str]
    
class AuthorityResponse(BaseModel):
    id: int
    user_id: int
    name: str
    location: str
    description: Optional[str]
    document_path: Optional[str]
    photo_path: Optional[str]
    created_at: int

class CreateAuthorityRequest(BaseModel):
    name: str
    location: str
    description: Optional[str]