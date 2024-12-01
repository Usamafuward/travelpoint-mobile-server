from fastapi import APIRouter, UploadFile, Form, HTTPException, File, status
from app.database import cur, conn
from app.utils.image_processing import process_images
from fastapi.responses import JSONResponse
from app.schemas.error import SimpleErrorMessage
from typing import List, Optional
from app.schemas.post import PostResponse
import datetime


router = APIRouter()

endpoint_errors = {
    500: {"model": SimpleErrorMessage, "description": "Database Error"},
}

@router.post("/posts/create")
async def create_post(
    poster_id: int = Form(...),
    caption: Optional[str] = Form(None),
    video_url: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    images: List[UploadFile] = File(...),
):

    # Process images
    processed_images = await process_images(images)

    query = b"""INSERT INTO posts (poster_id, caption, images, video_url, location) VALUES (%s, %s, %s, %s, %s) RETURNING id"""

    try:
        # Use the resized image in the query
        # images_array = "{" + ",".join([f'"{img}"' for img in processed_images]) + "}"
        cur.execute(
            query,
            (
                poster_id,
                caption,
                processed_images,
                video_url,
                location,
            ),
        )
        post_id = cur.fetchone()  # type: ignore
        conn.commit()
        return JSONResponse(
            content={
                "message": "Post created successfully",
                "post_id": post_id,
            },
        )
    except Exception as e:
        conn.rollback()  # Rollback in case of any exception
        print(f"ERROR - DB:\n{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": endpoint_errors[500]["description"]},
        )


endpoint_status_codes = {
    200: {"description": "Post liked"},
    500: {"description": "Database Error"},
    404: {"description": "Post not found"},
}


@router.put("/posts/like/{post_id}", responses=endpoint_status_codes)  # type: ignore
async def like_post(post_id: int):
    query = b"SELECT * FROM posts WHERE id = %s"
    try:
        cur.execute(query, (post_id,))
        result = cur.fetchone()
        if result:
            likes = result["likes"] + 1  # type: ignore
            query = b"UPDATE posts SET likes = %s WHERE id = %s"
            cur.execute(query, (likes, post_id))
            conn.commit()
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": endpoint_status_codes[200]["description"],
                    "likes": likes,
                },
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": endpoint_status_codes[404]["description"]},
            )
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": endpoint_errors[500]["description"]},
        )



@router.get("/posts/get_all", response_model=List[PostResponse], responses=endpoint_errors)  # type: ignore
async def get_all_posts():
    query = b"SELECT * FROM posts"
    try:
        cur.execute(query)
        result = cur.fetchall()
        processed_result = []
        if result:
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
                    caption=row["caption"],
                    images=images,
                    video_url=row.get("video_url"),
                    location=row.get("location"),
                    tagged_users=row.get("tagged_users", []),
                    created_at=created_at_str,
                    likes=row.get("likes", 0)
                )
                processed_result.append(post_data)
                print(processed_result)

            return JSONResponse(
                content=[post.dict() for post in processed_result]
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "No posts found"},
            )
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": endpoint_errors[500]["description"]},
        )


@router.get("/posts/{post_id}", response_model=PostResponse, responses=endpoint_errors)  # type: ignore
async def get_post(post_id: int):
    query = b"SELECT * FROM posts WHERE id = %s"
    try:
        cur.execute(query, (post_id,))
        result = cur.fetchone()

        if result:
            # Decode images if present
            images = result["images"]
            if images:
                images = [img.decode("utf-8") if isinstance(img, bytes) else img for img in images]
            else:
                images = []

            created_at = result["created_at"]
            # Convert created_at to ISO string format
            created_at_str = created_at.isoformat() if created_at else None
            
            # Create a PostResponse object
            post_data = PostResponse(
                id=result["id"],
                poster_id=result["poster_id"],
                caption=result["caption"],
                images=images,
                video_url=result.get("video_url"),
                location=result.get("location"),
                tagged_users=result.get("tagged_users", []),
                created_at=created_at_str,
                likes=result.get("likes", 0)
            )

            return post_data
        else:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="Post not found"
            )
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"]
        )
