from fastapi import APIRouter, status, HTTPException
from app.database import cur, conn
from fastapi.responses import JSONResponse
from app.schemas.error import SimpleErrorMessage
from app.schemas.booking import BookingRequest, BookingResponse
from typing import List

router = APIRouter()

endpoint_errors = {
    500: {"model": SimpleErrorMessage, "description": "Database Error"},
    400: {"model": SimpleErrorMessage, "description": "Invalid Input"},
}

@router.post("/book", response_model=BookingResponse, responses=endpoint_errors)
async def book_item(booking: BookingRequest):
    """
    Book a vehicle, equipment, or guide.
    """
    query = b"""
    INSERT INTO booking (
        type, provider_id, customer_id, item_id, book_date, book_time, service_date, service_time, deliver_date, deliver_time, quantity, status
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)   
    RETURNING id, type, provider_id, customer_id, item_id, book_date, book_time, service_date, service_time, deliver_date, deliver_time, quantity, status
    """
    try:
        cur.execute(
            query,
            (
                booking.type,
                booking.provider_id,
                booking.customer_id,
                booking.item_id,
                booking.book_date,
                booking.book_time,
                booking.service_date,
                booking.service_time,
                booking.deliver_date,
                booking.deliver_time,
                booking.quantity,
                booking.status,
            ),
        )
        conn.commit()
        result = cur.fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create booking."
            )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": result["id"],
                "type": result["type"],
                "provider_id": result["provider_id"],
                "customer_id": result["customer_id"],
                "item_id": result["item_id"],
                "book_date": result["book_date"],
                "book_time": result["book_time"],
                "service_date": result["service_date"],
                "service_time": result["service_time"],
                "deliver_date": result["deliver_date"],
                "deliver_time": result["deliver_time"],
                "quantity": result["quantity"],
            },
        )
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": endpoint_errors[500]["description"]},
        )
        
@router.get("/bookings", response_model=List[BookingResponse], responses=endpoint_errors)  # type: ignore
async def get_booking_all():
    """
    Retrieve all bookings.
    """
    query = b"""
    SELECT 
        id, type, provider_id, customer_id, item_id, book_date, book_time, service_date, service_time, deliver_date, deliver_time, quantity, status
    FROM booking
    """
    try:
        cur.execute(query)
        results = cur.fetchall()

        bookings = [
            BookingResponse(
                id=row["id"],
                type=row["type"],
                provider_id=row["provider_id"],
                customer_id=row["customer_id"],
                item_id=row["item_id"],
                book_date=row["bookdate"],
                book_time=row["booktime"],
                service_date=row["service_date"],
                service_time=row["service_time"],
                deliver_date=row["deliver_date"],
                deliver_time=row["deliver_time"],
                quantity=row["quantity"],
                status=row["status"],
            )
            for row in results
        ]

        return JSONResponse(content=[booking.dict() for booking in bookings])
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": endpoint_errors[500]["description"]},
        )
        
@router.get("/bookings/{booking_id}", response_model=BookingResponse, responses=endpoint_errors)  # type: ignore
async def get_booking(booking_id: int):
    """
    Retrieve booking details by ID.
    """
    query = b"""
    SELECT 
        id, type, provider_id, customer_id, item_id, book_date, book_time, service_date, service_time, deliver_date, deliver_time, quantity, status
    FROM booking
    WHERE id = %s
    """
    try:
        cur.execute(query, (booking_id,))
        result = cur.fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking with ID {booking_id} not found.",
            )

        booking = BookingResponse(
            id=result["id"],
            type=result["type"],
            provider_id=result["provider_id"],
            customer_id=result["customer_id"],
            item_id=result["item_id"],
            book_date=result["book_date"],
            book_time=result["book_time"],
            service_date=result["service_date"],
            service_time=result["service_time"],
            deliver_date=result["deliver_date"],
            deliver_time=result["deliver_time"],
            quantity=result["quantity"],
            status=result["status"],
        )

        return JSONResponse(content=booking.dict())
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": endpoint_errors[500]["description"]},
        )


