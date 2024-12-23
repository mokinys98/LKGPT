from pydantic import BaseModel

class User(BaseModel):
    email: str
    total_emails: int
    total_cost: float
