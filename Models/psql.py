from pydantic import BaseModel, Field
from typing import List, Optional, Annotated


# -----------------------------
# Models: PostgreSQL
# -----------------------------

class PGUserBase(BaseModel):
    name: str
    password: str

class PGUserUpdate(BaseModel):
    password: Optional[str] = None

class PGDBBase(BaseModel):
    name: str
    owner: str

class PGDBUpdate(BaseModel):
    owner: Optional[str] = None
