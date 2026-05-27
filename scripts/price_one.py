import os, requests
API="https://api.mercadolibre.com"
# Map seller_id -> (label, secret env var)
SELLERS={
    3009687392:("ANGEL","MELI_REFRESH_TOKEN_ANGEL"),
    3348766821:("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
    3338633403:("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
    3417664339:("ADRIAN","MELI_REFRESH_TOKEN_ADRIAN"),
}
SID="MLM2886030837"
# First probe: read with Wilbert token (any token reads any item)
def tok(rt):
    return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=20).json()

# probe with each available account in order
candidates=["WILBERT","YC_NEW","JUAN","ASVA","BREN","MILDRED","DILCIE","MG20260424","CLARIBEL","RAYMUNDO","ANGEL","ADRIAN"]
seller_id=None
for c in candidates:
    sec=f"MELI_REFRESH_TOKEN_{c}"
    if sec not in os.environ: continue
    rt=os.environ[sec]
    t=tok(rt)
    if "access_token" not in t: continue
    H={"Authorization":f"Bearer {t['access_token']}"}
    r=requests.get(f"{API}/items/{SID}",headers=H,timeout=20)
    if r.status_code==200:
        d=r.json()
        seller_id=d.get("seller_id")
        print(f"probe with {c} -> seller_id={seller_id} status={d.get('status')} price={d.get('price')} title='{(d.get('title') or '')[:70]}'")
        break

if not seller_id:
    print("Could not read item with any available token.")
    raise SystemExit(1)

# Map to which account owns it
if seller_id not in SELLERS:
    print(f"seller_id={seller_id} no está en mi mapa de cuentas conocidas. No tengo un secret asignado para esa cuenta.")
    raise SystemExit(1)
label,sec=SELLERS[seller_id]
if sec not in os.environ:
    print(f"Owner is {label} but secret {sec} not in env. Add it to the workflow.")
    raise SystemExit(1)

print(f"\nOwner: {label}")
t=tok(os.environ[sec])
T=t["access_token"]
print(f"NEW_RT_{label}={t.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
g=requests.get(f"{API}/items/{SID}",headers=H,timeout=20).json()
print(f"BEFORE: status={g.get('status')} price={g.get('price')} qty={g.get('available_quantity')}")
r=requests.put(f"{API}/items/{SID}",headers=HJ,json={"price":199},timeout=30)
print(f"PUT price=199: {r.status_code} {r.text[:200] if r.status_code>=400 else 'OK'}")
g2=requests.get(f"{API}/items/{SID}",headers=H,timeout=20).json()
print(f"AFTER: status={g2.get('status')} price={g2.get('price')}")
