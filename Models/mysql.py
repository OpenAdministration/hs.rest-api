from pydantic import BaseModel, Field
from typing import List, Optional, Annotated


class MySQLUserBase(BaseModel):
    name: str
    password: str
    host: Optional[str] = Field("%", description="Host pattern, default '%'")

class MySQLUserUpdate(BaseModel):
    password: Optional[str] = None
    host: Optional[str] = None

class MySQLDBBase(BaseModel):
    name: str
    owner: str

class MySQLDBUpdate(BaseModel):
    owner: Optional[str] = None
