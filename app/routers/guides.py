from fastapi import APIRouter, UploadFile, Form, HTTPException, File, status
from app.database import cur, conn
from fastapi.responses import JSONResponse
from typing import List, Optional
from app.schemas.services import GuideResponse, CreateGuideRequest
import datetime
from app.utils.image_processing import process_images
import os

router = APIRouter()

endpoint_errors = {
    500: {"description": "Database Error"},
    404: {"description": "Guide not found"},
}

@router.post("/guide/create")
async def create_guide(
    user_id: int = Form(...),
    language: str = Form(...),
    location: str = Form(...),
    preference: str = Form(...),
    description: Optional[str] = Form(None),
    document: Optional[UploadFile] = None,
    photo: Optional[UploadFile] = None,
):
    os.makedirs("uploads", exist_ok=True)
    
    document_path = None
    if document:
        document_path = f"uploads/{document.filename}"
        with open(document_path, "wb") as buffer:
            buffer.write(await document.read())

    photo_path = None
    if photo:
        processed_images = await process_images([photo])
        if processed_images:
            photo_path = processed_images[0]

    # Prepare and execute database query
    query = """
    INSERT INTO guides (user_id, language, location, preference, description, document_path, photo_path)
    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
    """
    try:
        
        cur.execute(
            query,
            (
                user_id,
                language,
                location,
                preference,
                description,
                document_path,
                photo_path,
            ),
        )
        guide_id = cur.fetchone()
        conn.commit()

        return JSONResponse(
            content={
                "message": "Guide created successfully",
                "guide_id": guide_id,
            },
        )
    except Exception as e:
        conn.rollback()
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.get("/guides/{guide_id}", response_model=GuideResponse, responses=endpoint_errors)
async def get_guide(guide_id: int):
    try:
        query = "SELECT * FROM guides WHERE id = %s"
        cur.execute(query, (guide_id,))
        guide = cur.fetchone()
        if not guide:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=endpoint_errors[404]["description"],
            )
        return GuideResponse(
            id=guide["id"],
            language=guide["language"],
            location=guide["location"],
            preference=guide["preference"].split(","),
            description=guide["description"],
            document_path=guide["document_path"],
            photo_path=guide["photo_path"],
            created_at=int(guide["created_at"].timestamp()),
        )
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.get("/guides/all", response_model=List[GuideResponse], responses=endpoint_errors)
async def get_all_guides():
    try:
        query = "SELECT * FROM guides"
        cur.execute(query)
        guides = cur.fetchall()
        return [
            GuideResponse(
                id=guide["id"],
                language=guide["language"],
                location=guide["location"],
                preference=guide["preference"].split(","),
                description=guide["description"],
                document_path=guide["document_path"],
                photo_path=guide["photo_path"],
                created_at=int(guide["created_at"].timestamp()),
            )
            for guide in guides
        ]
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.put("/guides/{guide_id}", responses=endpoint_errors)
async def update_guide(
    guide_id: int,
    language: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    preference: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
):
    try:
        updates = []
        params = []
        if language:
            updates.append("language = %s")
            params.append(language)
        if location:
            updates.append("location = %s")
            params.append(location)
        if preference:
            updates.append("preference = %s")
            params.append(preference)
        if description:
            updates.append("description = %s")
            params.append(description)

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided",
            )

        params.append(guide_id)
        query = f"UPDATE guides SET {', '.join(updates)} WHERE id = %s"
        cur.execute(query, params)
        conn.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"message": "Guide updated successfully"}
        )
    except Exception as e:
        conn.rollback()
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.delete("/guides/{guide_id}", responses=endpoint_errors)
async def delete_guide(guide_id: int):
    try:
        query = "DELETE FROM guides WHERE id = %s"
        cur.execute(query, (guide_id,))
        conn.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"message": "Guide deleted successfully"}
        )
    except Exception as e:
        conn.rollback()
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )