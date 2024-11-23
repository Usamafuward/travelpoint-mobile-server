from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PostCreate(BaseModel):
    poster_id: int
    caption: Optional[str] = None
    video_url: Optional[str] = None
    location: Optional[str] = None
    images: List[str]
    tagged_users: Optional[List[int]] = None

class PostResponse(BaseModel):
    id: int
    poster_id: int
    caption: Optional[str] = None
    images: List[str] 
    video_url: Optional[str] = None
    location: Optional[str] = None
    created_at: str
    likes: int
    username: Optional[str]
    profile_pic: Optional[str]


