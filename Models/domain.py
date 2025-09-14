from pydantic import BaseModel, Field
from typing import List, Optional, Annotated

class DomainCreate(BaseModel):
    name: str = Field(
            pattern=r"([-a-z0-9]+\.)+[a-z]{2,}",
            max_length=999,
            description="Domain-Name",
            examples=['example.org']
        )
    user: str = Field(
        pattern=r"[a-z0-9_\-\.]*",
        max_length=999
    )

class DomainUpdate(BaseModel):
    validsubdomainnames : Optional[str] = Field(
        None,
        examples=['www,blog', '*', 'www']
    )
    domainoptions : Optional[List[str]] = Field(
        None,
        examples=[['greylisting', 'letsencrypt']],
    )
    passengerpython: Optional[str] = Field(
        None,
        pattern=r"[a-zA-Z0-9_\-\/\.]*",
        max_length=999,
        alias="passenger_python",
        examples=['/usr/bin/python3']
    )
    passengernodejs: Optional[str] = Field(
        None,
        pattern=r"[a-zA-Z0-9_\-\/\.]*",
        max_length=999,
        alias="passenger_nodejs",
        examples = ['/usr/bin/node']
    )
    passengerruby: Optional[str] = Field(
        None,
        pattern=r"[a-zA-Z0-9_\-\/\.]*",
        max_length=999,
        alias="passenger_ruby",
        examples = ['/usr/bin/ruby']
    )
    fcgiphpbin: Optional[str] = Field(
        None,
        pattern=r"[a-zA-Z0-9_\-\/\.]*",
        max_length=999,
        alias="fcgi_php_bin",
        examples=['/usr/lib/cgi-bin/php8.4', '/usr/lib/cgi-bin/php']
    )


class DomainOut(DomainCreate, DomainUpdate):
    hive: str = Field(examples=['h01'])
    since : str = Field(pattern=r"[0-9\./\-]*", max_length=999, examples=["13.09.25"])
    pac : str = Field(examples=['xyz00'])
    id : int = Field()
