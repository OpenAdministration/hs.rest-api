from collections.abc import Generator
from contextlib import contextmanager
import datetime
import re
import threading
import xmlrpc.client
from xmlrpc.client import Fault

import requests
import yaml
from cachetools import cached, Cache
from fastapi import HTTPException, Request

# Load credentials from .env
CAS_URL = "https://login.hostsharing.net/cas/v1/tickets"
SERVICE = "https://config.hostsharing.net:443/hsar/backend"
BACKEND = "https://config.hostsharing.net:443/hsar/xmlrpc/hsadmin"

class GrantPools:
    """
    A grant can only have one active ticket at a time. If you fetch a new ticket old tickets become invalid. So if we want to handle multiple requests concurently we need to reserve the grant for the duration of the request.

    To help, this class handles one pool of grants for each username/password combination. The acquire Method provides an exclusive grant.
    """
    def __init__(self) -> None:
        self.pools = dict[(str, str), list[tuple[str, datetime.datetime]]]()
        self.lock = threading.Lock()
    
    @contextmanager
    def acquire(self, username: str, password: str) -> Generator[str]:
        """
        Use with a with statement to temporarily acquire a grant. The grant will be automatically returned on leaving the block. E.g. after the request
        """
        key = (username, password)
        (grant, validity) = self._try_get_grant(key)
        if grant is None:
            grant = get_ticket_grant(username, password)
            validity = datetime.datetime.now() + datetime.timedelta(seconds=3000)
        try:
            yield grant
        finally:
            self._put_grant(key, (grant, validity))
    

    def _try_get_grant(self, key) -> tuple[str, datetime.datetime] | tuple[None, None]:
        with self.lock:
            if key not in self.pools:
                self.pools[key] = []
            grants = self.pools[key]
            while len(grants) > 0:
                (grant, validity) = grants.pop(0)
                if validity > datetime.datetime.now():
                    return grant, validity
        return None, None
    
    def _put_grant(self, key, grant):
        with self.lock:
            if key not in self.pools:
                self.pools[key] = []
            self.pools[key].append(grant)

grantPools = GrantPools()

@cached(Cache(maxsize=float("inf")))
def get_credentials(api_key : str) -> dict[str,str]:
    with open("env.yaml", "r") as file:
        data = yaml.safe_load(file)
        api_entries = list(api for api in data['api'] if api['key'] == api_key)
        if len(api_entries) != 1:
            raise HTTPException(500, "API Key not found")
        allowed_pacs = api_entries[0]["pacs"]
        if isinstance(allowed_pacs, str):
            allowed_pacs = allowed_pacs.split(',')
        filtered_creds = {pac: data["pacs"][pac] for pac in allowed_pacs if pac in data["pacs"]}
        return filtered_creds


def get_ticket_grant(username: str, password: str) -> str:
    # Ticket-Granting Ticket (TGT) holen
    resp = requests.post(
        CAS_URL,
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    tgt_match = re.search(r'action="([^"]+)"', resp.text)
    if not tgt_match:
        raise RuntimeError("TGT nicht gefunden")
    tgt_url = tgt_match.group(1)
    return tgt_url

# ---------- Step 1+2: CAS Authentication ----------
def get_service_ticket(grant: str) -> str:
    # Service-Ticket holen
    resp = requests.post(
        grant,
        data={"service": SERVICE},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return resp.text.strip()

# ---------- Step 3: XML-RPC Call ----------
def hs_call(request: Request, method: str, param1, param2=None) -> list:

    headers = request.headers
    api_key = headers.get("Authorization")
    credentials = get_credentials(api_key)
    if len(credentials) == 1:
        # pac not given, but only one pac configured
        username = list(credentials.keys())[0]
    elif headers.get("PAC") in credentials:
        username = headers.get("PAC")
    else:
        raise HTTPException(400, f"PAC {headers.get("PAC")} is not configured in this API, please check your credentials.yaml file")
    with grantPools.acquire(username, credentials[username]) as grant:
        service_ticket = get_service_ticket(grant)
        server = xmlrpc.client.ServerProxy(BACKEND)
        remote = getattr(server, method)

        if param2:
            return remote(username, service_ticket, param1, param2)
        else:
            return remote(username, service_ticket, param1)



def hs_search(request: Request, module: str, where : dict) -> list:
    method = module + ".search"
    return hs_call(request, method, where)

def hs_update(request: Request, module: str, where : dict, set: dict):
    method = module + ".update"
    return hs_call(request, method, set, where)

def hs_delete(request: Request, module: str, where : dict) -> list:
    method = module + ".delete"
    return hs_call(request, method, where)

def hs_add(request: Request, module: str, set : dict) -> list:
    try:
        method = module + ".add"
        return hs_call(request, method, set)
    except Fault as e:
        print(e)
        raise HTTPException(status_code=400, detail="Fehlerhafte Eingaben")

def hs_api(request: Request):
    return hs_call(request, 'property.search', {})
