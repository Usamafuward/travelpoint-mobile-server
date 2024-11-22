from pydantic import BaseModel

class SimpleErrorMessage(BaseModel):
    message: str