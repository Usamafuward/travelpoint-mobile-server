from pydantic import BaseModel
from typing import List

class FollowRequest(BaseModel):
    user_id: int
    follower_id: int

class UserListResponse(BaseModel):
    users: List[int]