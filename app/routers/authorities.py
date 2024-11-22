from fastapi import APIRouter, UploadFile, Form, HTTPException, status, File
from fastapi.responses import JSONResponse
from typing import List, Optional
from app.database import cur, conn
from app.schemas.services import AuthorityResponse, CreateAuthorityRequest

router = APIRouter()

endpoint_errors = {
    500: {"description": "Database Error"},
    404: {"description": "Authority not found"},
}


@router.post("/authority/create", response_model=AuthorityResponse, responses=endpoint_errors)
async def create_authority(
    user_id: int = Form(...),
    name: str = Form(...),
    location: str = Form(...),
    description: Optional[str] = Form(None),
    document: Optional[UploadFile] = None,
):
    try:
        # Save uploaded files (if any)
        document_path = None
        if document:
            document_path = f"uploads/{document.filename}"
            with open(document_path, "wb") as buffer:
                buffer.write(await document.read())

        # Insert into the database
        query = """
        INSERT INTO authority (user_id, name, location, description, document_path)
        VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at
        """
        cur.execute(query, (name, location, description, document_path))
        authority = cur.fetchone()
        conn.commit()

        # Return response
        return AuthorityResponse(
            id=authority["id"],
            user_id=user_id,
            name=name,
            location=location,
            description=description,
            document_path=document_path,
            created_at=int(authority["created_at"].timestamp()),
        )
    except Exception as e:
        conn.rollback()
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.get("/authorities/{authority_id}", response_model=AuthorityResponse, responses=endpoint_errors)
async def get_authority(authority_id: int):
    try:
        query = "SELECT * FROM authority WHERE id = %s"
        cur.execute(query, (authority_id,))
        authority = cur.fetchone()
        if not authority:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=endpoint_errors[404]["description"],
            )
        return AuthorityResponse(
            id=authority["id"],
            name=authority["name"],
            location=authority["location"],
            description=authority["description"],
            document_path=authority["document_path"],
            photo_path=authority["photo_path"],
            created_at=int(authority["created_at"].timestamp()),
        )
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.get("/authorities/all", response_model=List[AuthorityResponse], responses=endpoint_errors)
async def get_all_authorities():
    try:
        query = "SELECT * FROM authority"
        cur.execute(query)
        authorities = cur.fetchall()
        return [
            AuthorityResponse(
                id=auth["id"],
                name=auth["name"],
                location=auth["location"],
                description=auth["description"],
                document_path=auth["document_path"],
                photo_path=auth["photo_path"],
                created_at=int(auth["created_at"].timestamp()),
            )
            for auth in authorities
        ]
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.put("/authorities/{authority_id}", responses=endpoint_errors)
async def update_authority(
    authority_id: int,
    name: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
):
    try:
        updates = []
        params = []

        if name:
            updates.append("name = %s")
            params.append(name)
        if location:
            updates.append("location = %s")
            params.append(location)
        if description:
            updates.append("description = %s")
            params.append(description)

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided",
            )

        params.append(authority_id)
        query = f"UPDATE authority SET {', '.join(updates)} WHERE id = %s"
        cur.execute(query, params)
        conn.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"message": "Authority updated successfully"}
        )
    except Exception as e:
        conn.rollback()
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.delete("/authorities/{authority_id}", responses=endpoint_errors)
async def delete_authority(authority_id: int):
    try:
        query = "DELETE FROM authority WHERE id = %s"
        cur.execute(query, (authority_id,))
        conn.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"message": "Authority deleted successfully"}
        )
    except Exception as e:
        conn.rollback()
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )
