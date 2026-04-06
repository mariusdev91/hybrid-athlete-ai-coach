from pydantic import BaseModel

class UserProfile(BaseModel):
    name: str
    age: int
    sport: str
    level: str
    equipment: list
