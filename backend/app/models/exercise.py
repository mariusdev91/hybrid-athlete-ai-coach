from pydantic import BaseModel
from typing import List

class Exercise(BaseModel):
    id: str
    name: str
    aliases: List[str]
    category: str
    equipment: List[str]
    primary_muscles: List[str]
    secondary_muscles: List[str]
    instructions: List[str]
