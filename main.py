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

@app.get("/hsapi")
def properties_search():
    """Fetch Hostsharing API information."""
    return hs_api()

@app.get("/domain/{name}", tags=['Domain'])
def get_domain(name: str) -> DomainOut:
    result = hs_search("domain",  {'name': name})
    if not result:
        raise HTTPException(status_code=404, detail="Domain not found")
    return result[0]


@app.post("/domain", tags=['Domain'], response_model=DomainOut)
def create_domain(dom: DomainCreate):
    params = {"name": dom.name, "user": dom.user}
    return hs_add("domain", params)


@app.put("/domain/{name}", tags=['Domain'])
def update_domain(name: str, dom: DomainUpdate):
    return hs_update("domain", {"name": name }, dom.model_dump(exclude_none=True))


@app.delete("/domain/{name}", tags=['Domain'], status_code=204)
def delete_domain(name: str):
    return hs_delete("domain", {"name": name})


@app.get("/user/{name}", response_model=User, tags=['User'])
def get_user(name: str) :
    result = hs_search("user",  {'name': name})
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result[0]


@app.get("/users", response_model=List[User], tags=['User'])
def all_users():
    return hs_search("user", {})


@app.post("/user", tags=['User'])
def add_user(user: CreateUser):
    return hs_add("user", user.model_dump(exclude_none=True))


@app.put("/user/{name}", tags=['User'])
def update_user(name: str, user: User):
    return hs_update("user", {"name": name}, user.model_dump(exclude_none=True))


@app.delete("/user/{name}", tags=['User'])
def delete_user(name: str):
    return hs_delete("user", {"name": name})

@app.get("/email/{localpart}@{domain}", tags=['Email'])
def get_email(domain: str, localpart : str = "") -> EmailOut:
    result = hs_search("emailaddress", {"localpart": localpart, "domain": domain})
    if not result:
        raise HTTPException(status_code=404, detail="E-Mail-Adresse nicht gefunden")
    return result[0]

@app.get("/email/search", tags=['Email'])
def search_email(domain: str = None, localpart : str = None, target : List[str] = None) -> List[EmailOut]:
    """Suche E-Mail-Adressen nach localpart oder Domain.
    Angegebene, aber leere Localparts suchen nach der Catch-all Adresse

    Vorsicht! Target muss EXAKT korrekt sein, auch die Reihenfolge der targets muss für einen Suchtreffer stimmen"""
    query = {}
    if domain is not None:
        query["domain"] = domain
    if localpart is not None:
        query["localpart"] = localpart
    if target is not None:
        # hs api expects comma separated string, not array, so we fix that
        query["target"] = ",".join(target)

    return hs_search("emailaddress", query)

@app.post("/email", tags=['Email'])
def create_email(mail: EmailIn):
    return hs_add("emailaddress", mail.model_dump())


@app.put("/email/{localpart}@{domain}", tags=['Email'])
def update_email(domain: str, update : EmailUpdate, localpart: str = "") -> List[EmailOut]:
    """Update von targets bei einer bestimmten Mailadresse"""
    return hs_update("emailaddress", {"localpart": localpart, "domain": domain}, update.model_dump())

@app.post("/email/{localpart}@{domain}/target", tags=['Email'])
def add_email_target(domain: str, update : EmailUpdate, localpart: str = "") -> List[EmailOut]:
    """Adds a (list of) email targets to the list"""
    search_result = hs_search("emailaddress", {"localpart": localpart, "domain": domain})
    mail = search_result[0]
    new_target = mail["target"] + update.target
    return hs_update("emailaddress", where={"localpart": localpart, "domain": domain}, set={"target": new_target})

@app.delete("/email/{localpart}@{domain}/target", tags=['Email'])
def add_email_target(response: Response, domain: str, update : EmailUpdate, localpart: str = "", ) -> List[EmailOut]:
    """Removes a (list of) email targets from the list
    if there is a target left the Email-Address is returned
    if there is no target left the Email-Address is deleted and status 204 is returned
    """
    search_result = hs_search("emailaddress", {"localpart": localpart, "domain": domain})
    mail = search_result[0]
    new_target = list(set(mail["target"]) - set(update.target))
    if not new_target:
        # new target set is empty -> delete the mail
        hs_delete("emailaddress", where={"localpart": localpart, "domain": domain})
        response.status_code = 204
        return []
    else:
        # targets are not empty
        return hs_update("emailaddress", where={"localpart": localpart, "domain": domain}, set={"target": new_target})

@app.put("/email/bulk", tags=['Email'])
def update_email(update : EmailUpdate, domain: str = None, localpart: str = None) -> List[EmailOut]:
    """Massenupdate von targets bei potentiell mehreren Mails. Gut um bspw. alle abuse@ oder alle @example.com Mails neu umzuleiten"""
    where = {}
    if domain is not None:
        where['domain'] = domain
    if localpart is not None:
        where['localpart'] = localpart
    return hs_update("emailaddress", where, update.model_dump())


@app.delete("/email/{localpart}@{domain}", tags=['Email'])
def delete_email(localpart: str, domain: str):
    return hs_delete("emailaddress", {"localpart": localpart, "domain": domain})


@app.get("/mysql/users/{name}", tags=['Mysql'])
def get_mysql_user(name: str):
    res = hs_search("mysqluser", {"name": name})
    if not res:
        raise HTTPException(status_code=404, detail="MySQL user not found")
    return res[0]

@app.post("/mysql/users", tags=['Mysql'])
def create_mysql_user(user: MySQLUserBase):
    return hs_add("mysqluser", user.model_dump())

@app.put("/mysql/users/{name}", tags=['Mysql'])
def update_mysql_user(name: str, user: MySQLUserUpdate):
    if not user.model_dump(exclude_none=True):
        raise HTTPException(status_code=400, detail="No fields to update provided")
    return hs_update("mysqluser", {"name": name}, user.model_dump(exclude_none=True))

@app.delete("/mysql/users/{name}", tags=['Mysql'])
def delete_mysql_user(name: str):
    return hs_delete("mysqluser", {"name": name})


@app.get("/mysql/dbs/{name}", tags=['Mysql'])
def get_mysql_db(name: str):
    res = hs_search("mysqldb", {"name": name})
    if not res:
        raise HTTPException(status_code=404, detail="MySQL database not found")
    return res[0]

@app.post("/mysql/dbs", tags=['Mysql'])
def create_mysql_db(db: MySQLDBBase):
    return hs_add("mysqldb", db.model_dump())

@app.put("/mysql/dbs/{name}", tags=['Mysql'])
def update_mysql_db(name: str, db: MySQLDBUpdate):
    if not db.model_dump(exclude_none=True):
        raise HTTPException(status_code=400, detail="No fields to update provided")
    return hs_update("mysqldb", {"name": name}, db.model_dump(exclude_none=True))

@app.delete("/mysql/dbs/{name}", tags=['Mysql'])
def delete_mysql_db(name: str):
    return hs_delete("mysqldb", {"name": name})

@app.get("/pg/users/{name}", tags=['Pgsql'])
def get_pg_user(name: str):
    res = hs_search("pguser", {"name": name})
    if not res:
        raise HTTPException(status_code=404, detail="Postgres user not found")
    return res[0]

@app.post("/pg/users", tags=['Pgsql'])
def create_pg_user(user: PGUserBase):
    return hs_add("pguser", user.model_dump())

@app.put("/pg/users/{name}", tags=['Pgsql'])
def update_pg_user(name: str, user: PGUserUpdate):
    if not user.model_dump(exclude_none=True):
        raise HTTPException(status_code=400, detail="No fields to update provided")
    return hs_update("pguser", {"name": name}, user.model_dump(exclude_none=True))

@app.delete("/pg/users/{name}", tags=['Pgsql'])
def delete_pg_user(name: str):
    return hs_delete("pguser", {"name": name})


@app.get("/pg/dbs/{name}", tags=['Pgsql'])
def get_pg_db(name: str):
    res = hs_search("pgdb", {"name": name})
    if not res:
        raise HTTPException(status_code=404, detail="Postgres database not found")
    return res[0]

@app.post("/pg/dbs", tags=['Pgsql'])
def create_pg_db(db: PGDBBase):
    return hs_add("pgdb", db.model_dump())

@app.put("/pg/dbs/{name}", tags=['Pgsql'])
def update_pg_db(name: str, db: PGDBUpdate):
    try:
        if not db.model_dump(exclude_none=True):
            raise HTTPException(status_code=400, detail="No fields to update provided")
        return hs_update("pgdb", {"name": name}, db.model_dump(exclude_none=True))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/pg/dbs/{name}", tags=['Pgsql'])
def delete_pg_db(name: str):
    try:
        return hs_delete("pgdb", {"name": name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
