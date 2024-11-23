from fastapi import APIRouter, status
from app.database import cur, conn
from fastapi.responses import JSONResponse
from app.schemas.error import SimpleErrorMessage
from typing import List, Optional
from app.schemas.post import PostResponse
import datetime


router = APIRouter()

endpoint_errors = {
    500: {"model": SimpleErrorMessage, "description": "Database Error"},
}

@router.get("/get_all_posts", response_model=List[PostResponse], responses=endpoint_errors)  # type: ignore
async def get_all_posts():
    query = b"""
    SELECT 
        posts.id, 
        posts.poster_id, 
        posts.caption, 
        posts.images, 
        posts.video_url, 
        posts.location, 
        posts.tagged_users, 
        posts.created_at, 
        posts.likes,
        users.username, 
        users.profile_pic
    FROM posts
    JOIN users ON posts.poster_id = users.id
    """
    try:
        cur.execute(query)
        result = cur.fetchall()

        processed_result = []
        for row in result:
            # Decode images if present
            images = row["images"]
            if images:
                images = [img.decode("utf-8") if isinstance(img, bytes) else img for img in images]
            else:
                images = []
                
            created_at = row["created_at"]
            # Convert created_at to ISO string format
            created_at_str = created_at.isoformat() if created_at else None

            # Create PostResponse object for each row
            post_data = PostResponse(
                id=row["id"],
                poster_id=row["poster_id"],
                username=row["username"],
                profile_pic=row["profile_pic"],
                caption=row["caption"],
                images=images,
                video_url=row.get("video_url"),
                location=row.get("location"),
                created_at=created_at_str,
                likes=row.get("likes", 0)
            )
            processed_result.append(post_data)

        return JSONResponse(
            content=[post.dict() for post in processed_result]
        )
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": endpoint_errors[500]["description"]},
        )