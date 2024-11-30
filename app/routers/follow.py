from fastapi import APIRouter, HTTPException, status
from typing import List
from app.database import conn, cur
from app.schemas.follow import FollowRequest, UserListResponse
from fastapi.responses import JSONResponse
import traceback

router = APIRouter()

endpoint_errors = {
    404: {"description": "User not found or invalid operation"},
    500: {"description": "Database error"},
}

@router.post("/follow", status_code=status.HTTP_201_CREATED)
async def follow_user(request: FollowRequest):
    print(f"User ID: {request.user_id}, Follower ID: {request.follower_id}")
    try:
        # Step 1: Check if a follow record already exists
        check_query = """
        SELECT * FROM follow 
        WHERE user_id = %s AND follower_id = %s
        """
        cur.execute(check_query, (request.user_id, request.follower_id))
        existing_follow = cur.fetchone()

        if existing_follow:
            # Step 2: If a record exists, update the 'is_followed' field to True (if not already True)
            update_query = """
            UPDATE follow 
            SET is_followed = true
            WHERE user_id = %s AND follower_id = %s
            """
            cur.execute(update_query, (request.user_id, request.follower_id))
            conn.commit()  # Don't forget to commit changes to the database

            return JSONResponse(
                content={"message": "Follow status updated."},
                status_code=status.HTTP_200_OK
            )
        else:
            # Step 3: If no record exists, insert a new one with 'is_followed' set to True
            insert_query = """
            INSERT INTO follow (user_id, follower_id, is_followed) 
            VALUES (%s, %s, true)
            """
            cur.execute(insert_query, (request.user_id, request.follower_id))
            conn.commit()  # Commit the new follow relationship

            return JSONResponse(
                content={"message": "User followed successfully."},
                status_code=status.HTTP_201_CREATED
            )
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        )


@router.post("/unfollow", responses=endpoint_errors)
async def unfollow_user(request: FollowRequest):
    query = """
    UPDATE follow
    SET is_followed = FALSE
    WHERE user_id = %s AND follower_id = %s AND is_followed = TRUE
    RETURNING user_id;
    """
    try:
        cur.execute(query, (request.user_id, request.follower_id))
        if cur.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Follow relationship does not exist or is already inactive",
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

@router.get("/following/{id}", response_model=UserListResponse, responses=endpoint_errors)
async def get_following(id: int):
    try:
        # Fetch the list of following user IDs for the given user_id
        query = "SELECT follower_id FROM follow WHERE user_id = %s AND is_followed = TRUE"
        cur.execute(query, (id,))
        followings = [row['follower_id'] for row in cur.fetchall()]
        print(followings)
        return JSONResponse(
            content={"users": followings},
            status_code=status.HTTP_200_OK,
        )
    
    except Exception as e:
        # Log the full exception traceback for better debugging
        print(f"ERROR - DB:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        )

@router.get("/followers/{id}", response_model=UserListResponse, responses=endpoint_errors)
async def get_followers(id: int):
    """
    Retrieves a list of active followers for the specified user.
    """
    query = """
    SELECT user_id
    FROM follow
    WHERE follower_id = %s AND is_followed = TRUE;
    """
    try:
        cur.execute(query, (id,))
        followers = [row['user_id'] for row in cur.fetchall()]
        print(followers)
        return JSONResponse(
            content={"users": followers},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        # Log the error for debugging
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        )

