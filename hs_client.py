import os
import re
import requests
import xmlrpc.client

from cachetools import cached, TTLCache
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()
HS_USER = os.getenv("HS_PAC_USER")
HS_PASS = os.getenv("HS_PAC_PASS")

CAS_URL = "https://login.hostsharing.net/cas/v1/tickets"
SERVICE = "https://config.hostsharing.net:443/hsar/backend"
BACKEND = "https://config.hostsharing.net:443/hsar/xmlrpc/hsadmin"


@cached(cache=TTLCache(maxsize=1024, ttl=3000))
def get_ticket_grant() -> str:
    # Ticket-Granting Ticket (TGT) holen
    resp = requests.post(
        CAS_URL,
        data={"username": HS_USER, "password": HS_PASS},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    tgt_match = re.search(r'action="([^"]+)"', resp.text)
    if not tgt_match:
        raise RuntimeError("TGT nicht gefunden")
    tgt_url = tgt_match.group(1)
    return tgt_url

# ---------- Step 1+2: CAS Authentication ----------
def get_service_ticket() -> str:
    # Service-Ticket holen
    resp = requests.post(
        get_ticket_grant(),
        data={"service": SERVICE},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return resp.text.strip()

# ---------- Step 3: XML-RPC Call ----------
def hs_call(method: str, param1, param2 = None) -> list:
    service_ticket = get_service_ticket()
    server = xmlrpc.client.ServerProxy(BACKEND)
    remote = getattr(server, method)
    if param2:
        return remote(HS_USER, service_ticket, param1, param2)
    else:
        return remote(HS_USER, service_ticket, param1)

def hs_search(module: str, where : dict) -> list:
    method = module + ".search"
    return hs_call(method, where)

def hs_update(module: str, where : dict, set: dict):
    method = module + ".update"
    return hs_call(method, set, where)

def hs_delete(module: str, where : dict) -> list:
    method = module + ".delete"
    return hs_call(method, where)

def hs_add(module: str, set : dict) -> list:
    method = module + ".add"
    return hs_call(method, set)

def hs_api():
    return hs_call('property.search', {})

#print(hs_add('user', {'name':'oad02-mustermann', 'comment': 'Max Mustermann','password':'!1?2-3aBcasdasd','shell':'/bin/bash'}))
#print(hs_update('user', {'name' : 'oad02-mustermann'},{'password' : 'Glompf-123'}))
#print(hs_search('user', {'name': 'oad02-mustermann'}))
#print(hs_delete('user', {'name': 'oad02-mustermann'}))