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
        
        


