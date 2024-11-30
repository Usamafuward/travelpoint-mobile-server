from fastapi import APIRouter, HTTPException, Form, File, UploadFile, status
from app.database import cur, conn
from app.schemas.user import Profile
from fastapi.responses import JSONResponse
from app.schemas.error import SimpleErrorMessage
from typing import Optional
from PIL import Image
import base64
import io
import psycopg
from app.utils.image_processing import process_images
from app.schemas.post import PostResponse
from typing import List, Optional

router = APIRouter()

endpoint_errors = {
    500: {"model": SimpleErrorMessage, "description": "Database Error"},
}

@router.get(
    "/profile/{user_id}",
    responses={
        404: {"description": "Profile not found"},
        500: {"description": "Internal Server Error"},
    },
    response_model= Profile,  # Specify that the response will be of type Profile
)
async def get_profile(user_id: int ):
    query = "SELECT * FROM users WHERE id = %s"
    try:
        # Check if the database connection and cursor are set up correctly
        cur.execute(query, (user_id,))
        result = cur.fetchone()

        date_of_birth_str = (
            result["date_of_birth"].strftime("%Y-%m-%d")
            if result["date_of_birth"]
            else None
        )

        if result:
            # Create a Profile instance using the query result
            profile = Profile(
                firstname=result["first_name"],
                lastname=result["last_name"],
                username=result["username"],
                email=result["email"],
                contactInfo=result[
                    "phone_number"
                ],
                dateOfBirth=date_of_birth_str,
                profilePic=result[
                    "profile_pic"
                ],
                bio=result["bio"],
                type=result["type"]
            )
            return JSONResponse(
                content=profile.dict()
            )  # Convert Profile instance to a dict for JSON response
        else:
            raise HTTPException(status_code=404, detail="Profile not found")

    except psycopg.Error as db_error:
        print(f"Database Error: {db_error}")
        raise HTTPException(
            status_code=500,
            detail="Database query failed. Please check logs for details.",
        )
    except Exception as e:
        print(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@router.post("/profile/update", responses=endpoint_errors)
async def update_profile(
    id: int = Form(...),
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    contactInfo: Optional[str] = Form(None),
    dateOfBirth: Optional[str] = Form(None),
    profilePic: Optional[UploadFile] = File(None),
    bio: Optional[str] = Form(None),
):
    try:
        # Update the profile picture if provided
        if profilePic:
            processed_images = await process_images([profilePic])
            if processed_images:
                profilePicData = processed_images[0]

            # Update profile with new picture
            query = b"""UPDATE users
                        SET username = %s, email = %s, phone_number = %s, date_of_birth = %s, profile_pic = %s, bio =%s
                        WHERE id = %s"""
            cur.execute(
                query,
                (
                    username,
                    email,
                    contactInfo,
                    dateOfBirth,
                    profilePicData,
                    bio,
                    id,
                ),
            )
        else:
            # Update profile without changing the picture
            query = b"""UPDATE users
                        SET username = %s, email = %s, phone_number = %s, date_of_birth = %s, bio =%s
                        WHERE id = %s"""
            cur.execute(
                query,
                (
                    username,
                    email,
                    contactInfo,
                    dateOfBirth,
                    bio,
                    id,
                ),
            )

        conn.commit()
        return JSONResponse(content={"message": "Profile updated successfully"})
    except Exception as e:
        conn.rollback()  # Rollback in case of any exception
        print(f"ERROR - DB:\n{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": endpoint_errors[500]["description"]},
        )
        
@router.get("/profile/posts/{poster_id}", response_model=List[PostResponse], responses=endpoint_errors)
async def get_posts_by_user(poster_id: int):
    """
    Retrieve all posts created by a specific user.
    """
    query = b"""SELECT 
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
    JOIN users ON posts.poster_id = users.id WHERE poster_id = %s"""
    try:
        cur.execute(query, (poster_id,))
        result = cur.fetchall()

        if not result:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "No posts found for this user"},
            )

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
            content=[post.dict() for post in processed_result],
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": endpoint_errors[500]["description"]},
        )    


