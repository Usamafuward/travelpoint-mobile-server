from pydantic import BaseModel
from typing import Optional

class BookingRequest(BaseModel):
    type: str
    provider_id: int
    customer_id: int
    item_id: int
    book_date: str
    book_time: str
    service_date: Optional[str] = None
    service_time: Optional[str] = None
    deliver_date: Optional[str] = None
    deliver_time: Optional[str] = None
    quantity: int
    status: str

class BookingResponse(BookingRequest):
    id: int
