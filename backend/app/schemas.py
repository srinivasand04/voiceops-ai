from pydantic import BaseModel


class CallCreate(BaseModel):
    filename: str