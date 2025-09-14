from pydantic import BaseModel, Field
from typing import List, Optional, Annotated

#### USER ####
class UpdateUser(BaseModel):
    password: Optional[Annotated[
        str,
        Field(
            pattern=r"[^:]{6,}",
            max_length=999,
            description="Passwort (mindestens 3 aus 4: Klein, Groß, Sonderzeichen, Zahl",
            examples=['Secret!']
        )
    ]] = None
    comment: Optional[Annotated[
        str,
        Field(
            pattern=r"[a-zA-Z0-9_\-\. ]*",
            max_length=999,
            examples=['Ein Kommentar']
        )
    ]] = None
    shell: Optional[Annotated[
        str,
        Field(
            pattern=r"[-0-9A-Za-z/]*",
            max_length=999,
            description="Die Shell die bei eine ssh Verbindung geladen werden soll",
            default="/bin/bash",
        )
    ]] = None
    quota_softlimit: Optional[Annotated[
        str,
        Field(
            pattern=r"[0-9]*",
            max_length=999,
            description="Quota Softlimit. Kann um 50% für eine Weile überschritten werden"
        )
    ]] = None

    quota_hardlimit: Optional[Annotated[
        str,
        Field(pattern=r"[0-9]*", max_length=999)
    ]] = None

    storage_softlimit: Optional[Annotated[
        str,
        Field(pattern=r"[0-9]*", max_length=999)
    ]] = None

    storage_hardlimit: Optional[Annotated[
        str,
        Field(pattern=r"[0-9]*", max_length=999)
    ]] = None

class CreateUser(UpdateUser):
    name: Annotated[
        str,
        Field(
            pattern=r"[a-z0-9]{5}(-[a-z0-9\._]{1,26})?",
            max_length=999,
            description="Benutzername (beim Anlegen einmalig festgelegt)",
            examples=['xyz00-username']
        )
    ]

class User(CreateUser):
    pac: Optional[Annotated[
        str,
        Field(
            pattern=r"[a-z0-9]*",
            max_length=999,
            examples=['xyz00']
        )
    ]] = None
    homedir: Optional[Annotated[
        str,
        Field(
            pattern=r"[a-z0-9/_\-\.]*",
            max_length=999,
            examples=['/home/pacs/xyz00/users/username']
        )
    ]] = None

    locked: Optional[Annotated[
        bool,
        Field(
            description="Internes Flag (nicht sichtbar im UI)"
        )
    ]] = None