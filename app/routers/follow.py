from fastapi import APIRouter, HTTPException, status
from typing import List
from app.database import conn, cur
from app.schemas.follow import FollowRequest, UserListResponse
from fastapi.responses import JSONResponse

router = APIRouter()

endpoint_errors = {
    404: {"description": "User not found or invalid operation"},
    500: {"description": "Database error"},
}

@router.post("/follow", responses=endpoint_errors)
async def follow_user(request: FollowRequest):
    query = """
    INSERT INTO follow (user_id, follower_id)
    VALUES (%s, %s)
    ON CONFLICT DO NOTHING RETURNING user_id
    """
    try:
        cur.execute(query, (request.user_id, request.follower_id))
        user_id = cur.fetchone()
        conn.commit()
        return JSONResponse(
            content={
                "message": "Followed successfully",
                "user_id": user_id,
            },
        )
    except Exception as e:
        conn.rollback()
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        )

@router.post("/unfollow", responses=endpoint_errors)
async def unfollow_user(request: FollowRequest):
    query = "DELETE FROM follow WHERE user_id = %s AND follower_id = %s RETURNING user_id"
    try:
        cur.execute(query, (request.user_id, request.follower_id))
        if cur.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Follow relationship does not exist",
            )
        user_id = cur.fetchone()
        conn.commit()
        return JSONResponse(
            content={
                "message": "Unfollowed successfully",
                "user_id": user_id,
            },
        )
    except Exception as e:
        conn.rollback()
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        )

@router.get("/followers/{user_id}", response_model=UserListResponse, responses=endpoint_errors)
async def get_followers(user_id: int):
    query = "SELECT follower_id FROM follows WHERE follower_id = %s"
    try:
        cur.execute(query, (user_id,))
        followers = [row[0] for row in cur.fetchall()]
        return JSONResponse(
            content={"users": followers},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        )

@router.get("/following/{user_id}", response_model=UserListResponse, responses=endpoint_errors)
async def get_following(user_id: int):
    query = "SELECT follower_id FROM follows WHERE follower_id = %s"
    try:
        cur.execute(query, (user_id,))
        following = [row[0] for row in cur.fetchall()]
        return JSONResponse(
            content={"users": following},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        )
