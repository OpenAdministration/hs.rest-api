from typing import List

from fastapi import FastAPI, HTTPException, Request
from starlette.responses import Response

from Models.domain import DomainCreate, DomainUpdate, DomainOut
from Models.mail import EmailIn, EmailOut, EmailUpdate
from Models.mysql import MySQLDBBase, MySQLUserBase, MySQLUserUpdate, MySQLDBUpdate
from Models.psql import PGDBUpdate, PGDBBase, PGUserBase, PGUserUpdate
from Models.user import CreateUser, User
from hs_client import hs_search, hs_add, hs_update, hs_delete, hs_api

app = FastAPI(title="Hostsharing HS-Admin API", version="1.0.0")

# -----------------------------
# Endpoints
# -----------------------------

not_found_response = {
    404: {"description": "Item not found"},
}

@app.get("/hsapi")
def properties_search(request: Request):
    """Fetch Hostsharing API information."""
    return hs_api(request)

@app.get("/domain/{name}", tags=['Domain'], responses=not_found_response)
def get_domain(request: Request, name: str) -> DomainOut:
    result = hs_search(request, "domain",  {'name': name})
    if not result:
        raise HTTPException(status_code=404, detail="Domain not found")
    return result[0]


@app.post("/domain", tags=['Domain'], response_model=DomainOut)
def create_domain(request: Request, dom: DomainCreate):
    params = {"name": dom.name, "user": dom.user}
    return hs_add(request,"domain", params)


@app.put("/domain/{name}", tags=['Domain'])
def update_domain(request: Request, name: str, dom: DomainUpdate):
    return hs_update(request,"domain", {"name": name }, dom.model_dump(exclude_none=True))


@app.delete("/domain/{name}", tags=['Domain'], status_code=204)
def delete_domain(request: Request, name: str):
    return hs_delete(request, "domain", {"name": name})

@app.get("/domains", tags=['Domain'], response_model=List[DomainOut])
def get_all_domains(request: Request):
    return hs_search(request,"domain", {})

@app.get("/user/{name}", response_model=User, tags=['User'], responses=not_found_response)
def get_user(request: Request, name: str) :
    result = hs_search(request, "user",  {'name': name})
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result[0]


@app.post("/user", tags=['User'])
def add_user(request: Request, user: CreateUser):
    return hs_add(request, "user", user.model_dump(exclude_none=True))

@app.get("/users", response_model=List[User], tags=['User'])
def all_users(request: Request):
    return hs_search(request, "user", {})


@app.put("/user/{name}", tags=['User'])
def update_user(request: Request, name: str, user: User):
    return hs_update(request, "user", {"name": name}, user.model_dump(exclude_none=True))


@app.delete("/user/{name}", tags=['User'])
def delete_user(request: Request, name: str):
    return hs_delete(request, "user", {"name": name})

@app.get("/email/{localpart}@{domain}", tags=['Email'], responses=not_found_response)
@app.get("/email/@{domain}", tags=['Email'], responses=not_found_response)
def get_email(request: Request, domain: str, localpart : str = "") -> EmailOut:
    """
    Localpart ist optional. Ein leerer Localpart beschreibt eine Catch-All Adresse.
    """
    print(domain, localpart)
    result = hs_search(request, "emailaddress", {"localpart": localpart, "domain": domain})
    if not result:
        raise HTTPException(status_code=404, detail="E-Mail-Adresse nicht gefunden")
    return result[0]

@app.get("/email/search", tags=['Email'])
def search_email(request: Request, domain: str = None, localpart : str = None, target : List[str] = None) -> List[EmailOut]:
    """Suche E-Mail-Adressen nach localpart oder Domain.
    Angegebene, aber leere Localparts suchen nach der Catch-all Adresse

    Vorsicht! Target muss EXAKT korrekt sein, auch die Reihenfolge der elemente muss für einen Suchtreffer stimmen; praktisch ist diese funktion als kaum zu gebrauchen"""
    query = {}
    if domain is not None:
        query["domain"] = domain
    if localpart is not None:
        query["localpart"] = localpart
    if target is not None:
        # hs api expects comma separated string, not array, so we fix that
        query["target"] = ",".join(target)

    return hs_search(request, "emailaddress", query)

@app.post("/email", tags=['Email'])
def create_email(request: Request, mail: EmailIn):
    return hs_add(request, "emailaddress", mail.model_dump())


@app.put("/email/{localpart}@{domain}", tags=['Email'])
def update_email(request: Request, domain: str, update : EmailUpdate, localpart: str = "") -> List[EmailOut]:
    """Update von targets bei einer bestimmten Mailadresse"""
    return hs_update(request, "emailaddress", {"localpart": localpart, "domain": domain}, update.model_dump())

@app.post("/email/{localpart}@{domain}/target", tags=['Email'])
def add_email_target(request: Request, domain: str, update : EmailUpdate, localpart: str = "") -> List[EmailOut]:
    """Adds a (list of) email targets to the list"""
    search_result = hs_search(request, "emailaddress", {"localpart": localpart, "domain": domain})
    mail = search_result[0]
    new_target = mail["target"] + update.target
    return hs_update(request, "emailaddress", where={"localpart": localpart, "domain": domain}, set={"target": new_target})

@app.delete("/email/{localpart}@{domain}/target", tags=['Email'])
def remove_email_target(request: Request, response: Response, domain: str, update : EmailUpdate, localpart: str = "", ) -> List[EmailOut]:
    """Removes a (list of) email targets from the list
    if there is a target left the Email-Address is returned
    if there is no target left the Email-Address is deleted and status 204 is returned
    """
    search_result = hs_search(request, "emailaddress", {"localpart": localpart, "domain": domain})
    mail = search_result[0]
    new_target = list(set(mail["target"]) - set(update.target))
    if not new_target:
        # new target set is empty -> delete the mail
        hs_delete(request, "emailaddress", where={"localpart": localpart, "domain": domain})
        response.status_code = 204
        return []
    else:
        # targets are not empty
        return hs_update(request, "emailaddress", where={"localpart": localpart, "domain": domain}, set={"target": new_target})

@app.put("/email/bulk", tags=['Email'])
def update_email(request: Request, update : EmailUpdate, domain: str = None, localpart: str = None) -> List[EmailOut]:
    """Massenupdate von targets bei potentiell mehreren Mails. Gut um bspw. alle abuse@ oder alle @example.com Mails neu umzuleiten"""
    where = {}
    if domain is not None:
        where['domain'] = domain
    if localpart is not None:
        where['localpart'] = localpart
    return hs_update(request, "emailaddress", where, update.model_dump())


@app.delete("/email/{localpart}@{domain}", tags=['Email'])
def delete_email(request: Request, localpart: str, domain: str):
    return hs_delete(request, "emailaddress", {"localpart": localpart, "domain": domain})


@app.get("/mysql/user/{name}", tags=['Mysql'], responses=not_found_response)
def get_mysql_user(request: Request, name: str):
    res = hs_search(request, "mysqluser", {"name": name})
    if not res:
        raise HTTPException(status_code=404, detail="MySQL user not found")
    return res[0]

@app.post("/mysql/users", tags=['Mysql'])
def create_mysql_user(request: Request, user: MySQLUserBase):
    return hs_add(request, "mysqluser", user.model_dump())

@app.put("/mysql/user/{name}", tags=['Mysql'])
def update_mysql_user(request: Request, name: str, user: MySQLUserUpdate):
    if not user.model_dump(exclude_none=True):
        raise HTTPException(status_code=400, detail="No fields to update provided")
    return hs_update(request, "mysqluser", {"name": name}, user.model_dump(exclude_none=True))

@app.delete("/mysql/user/{name}", tags=['Mysql'])
def delete_mysql_user(request: Request, name: str):
    return hs_delete(request, "mysqluser", {"name": name})


@app.get("/mysql/db/{name}", tags=['Mysql'], responses=not_found_response)
def get_mysql_db(request: Request, name: str):
    res = hs_search(request, "mysqldb", {"name": name})
    if not res:
        raise HTTPException(status_code=404, detail="MySQL database not found")
    return res[0]

@app.post("/mysql/db", tags=['Mysql'])
def create_mysql_db(request: Request, db: MySQLDBBase):
    return hs_add(request, "mysqldb", db.model_dump())

@app.put("/mysql/db/{name}", tags=['Mysql'])
def update_mysql_db(request: Request, name: str, db: MySQLDBUpdate):
    if not db.model_dump(exclude_none=True):
        raise HTTPException(status_code=400, detail="No fields to update provided")
    return hs_update(request, "mysqldb", {"name": name}, db.model_dump(exclude_none=True))

@app.delete("/mysql/db/{name}", tags=['Mysql'])
def delete_mysql_db(request: Request, name: str):
    return hs_delete(request, "mysqldb", {"name": name})

@app.get("/pg/user/{name}", tags=['Pgsql'], responses=not_found_response)
def get_pg_user(request: Request, name: str):
    res = hs_search(request, "pguser", {"name": name})
    if not res:
        raise HTTPException(status_code=404, detail="Postgres user not found")
    return res[0]

@app.post("/pg/user", tags=['Pgsql'])
def create_pg_user(request: Request, user: PGUserBase):
    return hs_add(request, "pguser", user.model_dump())

@app.put("/pg/user/{name}", tags=['Pgsql'])
def update_pg_user(request: Request, name: str, user: PGUserUpdate):
    if not user.model_dump(exclude_none=True):
        raise HTTPException(status_code=400, detail="No fields to update provided")
    return hs_update(request, "pguser", {"name": name}, user.model_dump(exclude_none=True))

@app.delete("/pg/user/{name}", tags=['Pgsql'])
def delete_pg_user(request: Request, name: str):
    return hs_delete(request, "pguser", {"name": name})


@app.get("/pg/db/{name}", tags=['Pgsql'], responses=not_found_response)
def get_pg_db(request: Request, name: str):
    res = hs_search(request, "pgdb", {"name": name})
    if not res:
        raise HTTPException(status_code=404, detail="Postgres database not found")
    return res[0]

@app.post("/pg/db", tags=['Pgsql'])
def create_pg_db(request: Request, db: PGDBBase):
    return hs_add(request, "pgdb", db.model_dump())

@app.put("/pg/db/{name}", tags=['Pgsql'])
def update_pg_db(request: Request, name: str, db: PGDBUpdate):
    if not db.model_dump(exclude_none=True):
        raise HTTPException(status_code=400, detail="No fields to update provided")
    return hs_update(request, "pgdb", {"name": name}, db.model_dump(exclude_none=True))

@app.delete("/pg/db/{name}", tags=['Pgsql'])
def delete_pg_db(request: Request, name: str):
    return hs_delete(request, "pgdb", {"name": name})
