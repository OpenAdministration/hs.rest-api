import os
import re
import xmlrpc.client
from xmlrpc.client import Fault

import requests
import yaml
from cachetools import cached, TTLCache, Cache
from fastapi import HTTPException, Request

# Load credentials from .env
CAS_URL = "https://login.hostsharing.net/cas/v1/tickets"
SERVICE = "https://config.hostsharing.net:443/hsar/backend"
BACKEND = "https://config.hostsharing.net:443/hsar/xmlrpc/hsadmin"

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


@cached(cache=TTLCache(maxsize=1024, ttl=3000))
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
def get_service_ticket(pac: str, password : str) -> str:
    # Service-Ticket holen
    resp = requests.post(
        get_ticket_grant(pac, password),
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
    service_ticket = get_service_ticket(username, credentials[username])
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

#print(hs_add('user', {'name':'oad02-mustermann', 'comment': 'Max Mustermann','password':'!1?2-3aBcasdasd','shell':'/bin/bash'}))
#print(hs_update('user', {'name' : 'oad02-mustermann'},{'password' : 'Glompf-123'}))
#print(hs_search('user', {'name': 'oad02-mustermann'}))
#print(hs_delete('user', {'name': 'oad02-mustermann'}))