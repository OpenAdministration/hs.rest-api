from pydantic import BaseModel, Field
from typing import List, Optional, Annotated

class EmailUpdate(BaseModel):
    target: List[str] = Field(
        None,
        description="Liste von Zielen (Usernames oder Emailadressen)",
        examples=[['xyz00-postfach', 'abc@example.com']]
    )

class EmailIn(EmailUpdate):
    localpart: str = Field(
        None,
        examples=["info"]
    )
    domain: str = Field(
        None,
        examples=["example.org"]
    )


class EmailOut(EmailIn):
    admin: str = Field(
        None,
        examples=["xyz00-domains"],
        description="Domain-Admin"
    )
    emailaddress: str = Field(
        None,
        examples=["abuse@example.com"]
    )
    fulldomain: str = Field(
        None,
        examples=["example.com"]
    )
    id: int
    pac: str = Field(
        None,
        examples=["xyz00"], 
        description="Paketkennung"
    )



