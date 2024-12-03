from fastapi import APIRouter, UploadFile, Form, HTTPException, File, status
from app.database import cur, conn
from fastapi.responses import JSONResponse
from typing import List, Optional
from app.schemas.services import VehicleResponse, CreateVehicleRequest
import os
from app.utils.image_processing import process_images
from app.utils.pdf_processing import process_pdf
import json


router = APIRouter()

endpoint_errors = {
    500: {"description": "Database Error"},
    404: {"description": "Vehicle not found"},
}

@router.post("/vehicle/create")
async def create_vehicle(
    owner_id: int = Form(...),
    type: str = Form(...),
    capacity: int = Form(...),
    milage: float = Form(...),
    price: float = Form(...),
    description: Optional[str] = Form(None),
    document: Optional[UploadFile] = None,
    photo: Optional[UploadFile] = None,
):
    os.makedirs("uploads", exist_ok=True)
    
    document_path = None
    if document:
        document_content = await process_pdf(document)
        if document_content:
            document_path = json.dumps(document_content)

    photo_path = None
    if photo:
        processed_images = await process_images([photo])
        if processed_images:
            photo_path = processed_images[0]

    # Prepare and execute database query
    query = """
    INSERT INTO vehicles (owner_id, type, capacity, milage, price, description, document_path, photo_path)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    """
    
    try:
        cur.execute(
            query,
            (
                owner_id,
                type,
                capacity,
                milage,
                price,
                description or None,
                document_path or None,
                photo_path or None,
            ),
        )
        vehicle_id = cur.fetchone()
        conn.commit()

        return JSONResponse(
            content={
                "message": "Vehicle created successfully",
                "vehicle_id": vehicle_id,
            },
        )
    except Exception as e:
        conn.rollback()
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse, responses=endpoint_errors)
async def get_vehicle(vehicle_id: int):
    try:
        query = "SELECT * FROM vehicles WHERE id = %s"
        cur.execute(query, (vehicle_id,))
        vehicle = cur.fetchone()
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=endpoint_errors[404]["description"],
            )
        return VehicleResponse(
            id=vehicle["id"],
            type=vehicle["type"],
            capacity=vehicle["capacity"],
            milage=vehicle["milage"],
            price=vehicle["price"],
            description=vehicle["description"],
            document_path=vehicle["document_path"],
            photo_path=vehicle["photo_path"],
            created_at=int(vehicle["created_at"].timestamp()),
        )
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.get("/vehicles/all", response_model=List[VehicleResponse], responses=endpoint_errors)
async def get_all_vehicles():
    try:
        query = "SELECT * FROM vehicles"
        cur.execute(query)
        vehicles = cur.fetchall()
        return [
            VehicleResponse(
                id=vehicle["id"],
                type=vehicle["type"],
                capacity=vehicle["capacity"],
                milage=vehicle["milage"],
                price=vehicle["price"],
                description=vehicle["description"],
                document_path=vehicle["document_path"],
                photo_path=vehicle["photo_path"],
                created_at=int(vehicle["created_at"].timestamp()),
            )
            for vehicle in vehicles
        ]
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.put("/vehicles/{vehicle_id}", responses=endpoint_errors)
async def update_vehicle(
    vehicle_id: int,
    type: Optional[str] = Form(None),
    capacity: Optional[int] = Form(None),
    milage: Optional[float] = Form(None),
    price: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
):
    try:
        updates = []
        params = []
        if type:
            updates.append("type = %s")
            params.append(type)
        if capacity:
            updates.append("capacity = %s")
            params.append(capacity)
        if milage:
            updates.append("milage = %s")
            params.append(milage)
        if price:
            updates.append("price = %s")
            params.append(price)
        if description:
            updates.append("description = %s")
            params.append(description)

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided",
            )

        params.append(vehicle_id)
        query = f"UPDATE vehicles SET {', '.join(updates)} WHERE id = %s"
        cur.execute(query, params)
        conn.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"message": "Vehicle updated successfully"}
        )
    except Exception as e:
        conn.rollback()
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )


@router.delete("/vehicles/{vehicle_id}", responses=endpoint_errors)
async def delete_vehicle(vehicle_id: int):
    try:
        query = "DELETE FROM vehicles WHERE id = %s"
        cur.execute(query, (vehicle_id,))
        conn.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"message": "Vehicle deleted successfully"}
        )
    except Exception as e:
        conn.rollback()
        print(f"ERROR - DB:\n{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=endpoint_errors[500]["description"],
        )
    
@router.get("/vehicles/status/{owner_id}", responses=endpoint_errors)
async def check_vehicle_status(owner_id: int):
    try:
        query = """
        SELECT status FROM vehicles
        WHERE owner_id = %s
        ORDER BY created_at DESC LIMIT 1
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