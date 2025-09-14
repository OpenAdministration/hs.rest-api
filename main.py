from fastapi import FastAPI, HTTPException
from typing import List, Optional, Annotated

from hs_client import hs_search, hs_add, hs_update, hs_delete, hs_api

from Models.domain import DomainCreate, DomainUpdate, DomainOut
from Models.mysql import MySQLDBBase,MySQLUserBase, MySQLUserUpdate, MySQLDBUpdate
from Models.psql import PGDBUpdate, PGDBBase, PGUserBase, PGUserUpdate
from Models.user import UpdateUser, CreateUser, User
from Models.mail import EmailIn, EmailOut, EmailUpdate

app = FastAPI(title="Hostsharing HS-Admin API", version="1.0.0")

# -----------------------------
# Endpoints
# -----------------------------

@app.get("/hsapi")
def properties_search():
    return hs_api()

@app.get("/domain/{name}", tags=['Domain'])
def get_domain(name: str) -> DomainOut:
    try:
        result = hs_search("domain",  {'name': name})
        if not result:
            raise HTTPException(status_code=404, detail="Domain not found")
        return result[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/domain", tags=['Domain'], response_model=DomainOut)
def create_domain(dom: DomainCreate):
    try:
        params = {"name": dom.name, "user": dom.user}
        return hs_add("domain", params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/domain/{name}", tags=['Domain'])
def update_domain(name: str, dom: DomainUpdate):
    try:
        return hs_update("domain", {"name": name }, dom.model_dump(exclude_none=True))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/domain/{name}", tags=['Domain'], status_code=204)
def delete_domain(name: str):
    try:
        return hs_delete("domain", {"name": name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{name}", response_model=User, tags=['User'])
def get_user(name: str) :
    try:
        result = hs_search("user",  {'name': name})
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return result[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users", response_model=List[User], tags=['User'])
def all_users():
    try:
        return hs_search("user", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/user", tags=['User'])
def add_user(user: CreateUser):
    try:
        params = {"name": user.name, "password": user.password, "shell": user.shell}
        return hs_add("user", params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/user/{name}", tags=['User'])
def update_user(name: str, user: User):
    try:
        set_params = user.parameters
        if not set_params:
            raise HTTPException(status_code=400, detail="No fields to update provided")

        return hs_update("user", {"name": name}, set_params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/user/{name}", tags=['User'])
def delete_user(name: str):
    try:
        return hs_delete("user", {"name": name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/email/{localpart}@{domain}", tags=['Email'])
def get_email(domain: str, localpart : str = "") -> EmailOut:
    try:
        result = hs_search("emailaddress", {"localpart": localpart, "domain": domain})
        if not result:
            raise HTTPException(status_code=404, detail="E-Mail-Adresse nicht gefunden")
        return result[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/email/search", tags=['Email'])
def search_email(search : EmailIn) -> List[EmailOut]:
    """Suche E-Mail-Adressen nach localpart oder Domain.
    Angegebene, aber leere Localparts suchen nach der Catch-all Adresse

    Vorsicht! Target muss EXAKT korrekt sein, auch die Reihenfolge der targets muss für einen Suchtreffer stimmen"""
    try:
        model = search.model_dump(exclude_none=True)
        if "target" in model:
            # hs api expects comma separated string, not array, so we fix that
            model['target'] = ",".join(model["target"])
        return hs_search("emailaddress", model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/email", tags=['Email'])
def create_email(mail: EmailIn):
    try:
        return hs_add("emailaddress", mail.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/email/{localpart}@{domain}", tags=['Email'])
def update_email(domain: str, update : EmailUpdate, localpart: str = "") -> List[EmailOut]:
    """Update von targets bei einer bestimmten Mailadresse"""
    try:
        return hs_update("emailaddress", {"localpart": localpart, "domain": domain}, update.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/email/bulk", tags=['Email'])
def update_email(update : EmailUpdate, domain: str = None, localpart: str = None) -> List[EmailOut]:
    """Massenupdate von targets bei potentiell mehreren Mails. Gut um bspw. alle abuse@ oder alle @example.com Mails neu umzuleiten"""
    try:
        where = {}
        if domain is not None:
            where['domain'] = domain
        if localpart is not None:
            where['localpart'] = localpart
        return hs_update("emailaddress", where, update.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/email/{localpart}@{domain}", tags=['Email'])
def delete_email(localpart: str, domain: str):
    try:
        return hs_delete("emailaddress", {"localpart": localpart, "domain": domain})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mysql/users/{name}", tags=['Mysql'])
def get_mysql_user(name: str):
    try:
        res = hs_search("mysqluser", {"name": name})
        if not res:
            raise HTTPException(status_code=404, detail="MySQL user not found")
        return res[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mysql/users", tags=['Mysql'])
def create_mysql_user(user: MySQLUserBase):
    try:
        return hs_add("mysqluser", user.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/mysql/users/{name}", tags=['Mysql'])
def update_mysql_user(name: str, user: MySQLUserUpdate):
    try:
        if not user.dict(exclude_none=True):
            raise HTTPException(status_code=400, detail="No fields to update provided")
        return hs_update("mysqluser", {"name": name}, user.dict(exclude_none=True))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/mysql/users/{name}", tags=['Mysql'])
def delete_mysql_user(name: str):
    try:
        return hs_delete("mysqluser", {"name": name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mysql/dbs/{name}", tags=['Mysql'])
def get_mysql_db(name: str):
    try:
        res = hs_search("mysqldb", {"name": name})
        if not res:
            raise HTTPException(status_code=404, detail="MySQL database not found")
        return res[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mysql/dbs", tags=['Mysql'])
def create_mysql_db(db: MySQLDBBase):
    try:
        return hs_add("mysqldb", db.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/mysql/dbs/{name}", tags=['Mysql'])
def update_mysql_db(name: str, db: MySQLDBUpdate):
    try:
        if not db.dict(exclude_none=True):
            raise HTTPException(status_code=400, detail="No fields to update provided")
        return hs_update("mysqldb", {"name": name}, db.dict(exclude_none=True))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/mysql/dbs/{name}", tags=['Mysql'])
def delete_mysql_db(name: str):
    try:
        return hs_delete("mysqldb", {"name": name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pg/users/{name}", tags=['Pgsql'])
def get_pg_user(name: str):
    try:
        res = hs_search("pguser", {"name": name})
        if not res:
            raise HTTPException(status_code=404, detail="Postgres user not found")
        return res[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pg/users", tags=['Pgsql'])
def create_pg_user(user: PGUserBase):
    try:
        return hs_add("pguser", user.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/pg/users/{name}", tags=['Pgsql'])
def update_pg_user(name: str, user: PGUserUpdate):
    try:
        if not user.dict(exclude_none=True):
            raise HTTPException(status_code=400, detail="No fields to update provided")
        return hs_update("pguser", {"name": name}, user.dict(exclude_none=True))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/pg/users/{name}", tags=['Pgsql'])
def delete_pg_user(name: str):
    try:
        return hs_delete("pguser", {"name": name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pg/dbs/{name}", tags=['Pgsql'])
def get_pg_db(name: str):
    try:
        res = hs_search("pgdb", {"name": name})
        if not res:
            raise HTTPException(status_code=404, detail="Postgres database not found")
        return res[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pg/dbs", tags=['Pgsql'])
def create_pg_db(db: PGDBBase):
    try:
        return hs_add("pgdb", db.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/pg/dbs/{name}", tags=['Pgsql'])
def update_pg_db(name: str, db: PGDBUpdate):
    try:
        if not db.dict(exclude_none=True):
            raise HTTPException(status_code=400, detail="No fields to update provided")
        return hs_update("pgdb", {"name": name}, db.dict(exclude_none=True))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/pg/dbs/{name}", tags=['Pgsql'])
def delete_pg_db(name: str):
    try:
        return hs_delete("pgdb", {"name": name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
