from pydantic import BaseModel
from typing import Optional

class Pokemon(BaseModel):
    name: str
    id: int
    hp: int
    type: str 
    level: int 
    xp: int

class BatchPokeDelete(BaseModel):
    min_level: int
    max_level: int