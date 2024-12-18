from fastapi import APIRouter, UploadFile, Form, HTTPException, File, status
from app.database import cur, conn
from fastapi.responses import JSONResponse
from typing import List, Optional
from app.schemas.services import EquipmentResponse, CreateEquipmentRequest
import datetime
from app.utils.image_processing import process_images

router = APIRouter()

endpoint_errors = {
    500: {"description": "Database Error"},
    404: {"description": "Equipment not found"},
}


@router.post("/equipment/create")
async def create_equipment(
    owner_id: int = Form(...),
    type: str = Form(...),
    location: str = Form(...),
    description: Optional[str] = Form(None),
    photo: Optional[UploadFile] = None,
):
    photo_path = None
    if photo:
        processed_images = await process_images([photo])
        if processed_images:
            photo_path = processed_images[0]
            
    # Prepare and execute database query
    query = """
    INSERT INTO equipments (Owner_id, type, description, photo_path, location)
    VALUES (%s, %s, %s, %s, %s) RETURNING id
    """
    
    try:
        cur.execute(
            query,
            (
                owner_id,
                type,
                description,
                photo_path,
                location,
            ),
        )
        equipment_id = cur.fetchone()
        conn.commit()
        
        return JSONResponse(
            content={
                "message": "Equipment created successfully",
                "equipment_id": equipment_id,
            },
        )
    except Exception as e:
        conn.rollback()
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.get("/equipment/{equipment_id}", response_model=EquipmentResponse, responses=endpoint_errors)
async def get_equipment(equipment_id: int):
    try:
        query = """
            SELECT 
                equipments.id,
                equipments.owner_id,
                equipments.type,
                equipments.quantity,
                equipments.location,
                equipments.description,
                equipments.price_per_day,
                equipments.wishlist,
                equipments.availability,
                equipments.photo_path,
                users.first_name,
                users.last_name,
                users.email,
                users.phone_number
            FROM equipments JOIN users ON equipments.owner_id = users.id
            WHERE id = %s
        """
        cur.execute(query, (equipment_id,))
        equipment = cur.fetchone()
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=endpoint_errors[404]["description"],
            )
        return EquipmentResponse(
            id=equipment["id"],
                owner_id=equipment["owner_id"],
                type=equipment["type"],
                description=equipment["description"],
                price_per_day=equipment["price_per_day"],
                photo_path=equipment["photo_path"],
                quantity=equipment["quantity"],
                wishlist=equipment["wishlist"],
                phone_number=equipment["phone_number"],
                email=equipment["email"],
                name=equipment["first_name"] + " " + equipment["last_name"],
                availability=equipment["availability"],
                location=equipment["location"],
        )
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.get("/equipment/all", response_model=List[EquipmentResponse], responses=endpoint_errors)
async def get_all_equipment():
    try:
        query = """
            SELECT 
                equipments.id,
                equipments.owner_id,
                equipments.type,
                equipments.quantity,
                equipments.location,
                equipments.description,
                equipments.price_per_day,
                equipments.wishlist,
                equipments.availability,
                equipments.photo_path,
                users.first_name,
                users.last_name,
                users.email,
                users.phone_number
            FROM equipments JOIN users ON equipments.owner_id = users.id
        """
        cur.execute(query)
        equipments = cur.fetchall()
        return [
            EquipmentResponse(
                id=equipment["id"],
                owner_id=equipment["owner_id"],
                type=equipment["type"],
                description=equipment["description"],
                price_per_day=equipment["price_per_day"],
                photo_path=equipment["photo_path"],
                quantity=equipment["quantity"],
                wishlist=equipment["wishlist"],
                email=equipment["email"],
                phone_number=equipment["phone_number"],
                name=equipment["first_name"] + " " + equipment["last_name"],
                availability=equipment["availability"],
                location=equipment["location"],
            )
            for equipment in equipments
        ]
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.put("/equipment/{equipment_id}", responses=endpoint_errors)
async def update_equipment(
    equipment_id: int,
    name: Optional[str] = Form(None),
    type: Optional[str] = Form(None),
    condition: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
):
    try:
        updates = []
        params = []
        if name:
            updates.append("name = %s")
            params.append(name)
        if type:
            updates.append("type = %s")
            params.append(type)
        if condition:
            updates.append("condition = %s")
            params.append(condition)
        if description:
            updates.append("description = %s")
            params.append(description)

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided",
            )

        params.append(equipment_id)
        query = f"UPDATE equipment SET {', '.join(updates)} WHERE id = %s"
        cur.execute(query, params)
        conn.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"message": "Equipment updated successfully"}
        )
    except Exception as e:
        conn.rollback()
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.delete("/equipment/{equipment_id}", responses=endpoint_errors)
async def delete_equipment(equipment_id: int):
    try:
        query = "DELETE FROM equipment WHERE id = %s"
        cur.execute(query, (equipment_id,))
        conn.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"message": "Equipment deleted successfully"}
        )
    except Exception as e:
        conn.rollback()
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.get("/equipment/status/{owner_id}", responses=endpoint_errors)
async def get_equipment_status(owner_id: int):
    try:
        query = """
        SELECT status FROM equipments
        WHERE owner_id = %s
        ORDER BY created_at DESC
        LIMIT 1;
        """
        cur.execute(query, (owner_id,))
        result = cur.fetchone()

        if not result:
            return {"status": 0}

        return {"status": result["status"]}
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )
