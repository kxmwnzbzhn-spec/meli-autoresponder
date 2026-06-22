import os, sys, requests, json
sys.path.insert(0, "scripts")
import meli_token
API="https://api.mercadolibre.com"
AT=meli_token.get_access_token("ASVA")
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# PUT MODEL correcto
SID="MLM3037687139"
ATTRS=[
 {"id":"BRAND","values":[{"name":"The Alchemia Lab"}]},
 {"id":"MODEL","values":[{"name":"Flor de Nopal 100ml"}]},
 {"id":"ITEM_CONDITION","values":[{"name":"Nuevo"}]},
]
r=requests.put(f"{API}/catalog_suggestions/{SID}",headers=HJ,json={"attributes":ATTRS},timeout=20)
print(f"PUT MODEL: {r.status_code}")
print(r.text[:600])
