from pydantic import BaseModel
from typing import List

class FollowRequest(BaseModel):
    user_id: int
    follower_id: int
    is_followed: bool

class UserListResponse(BaseModel):
    users: List[int]