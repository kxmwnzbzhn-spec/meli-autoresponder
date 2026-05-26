import os, requests, time
import meli_token
KEEP="MLM5346655686"; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_WILBERT"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=15).json(); uid=me.get("id")
print("seller:",uid,me.get("nickname"))
ids=[]; off=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=20).json()
    res=r.get("results",[]); ids+=res; off+=50
    tot=r.get("paging",{}).get("total",0)
    if not res or off>=tot: break
print(f"activos: {len(ids)}")
paused=0; errs=0
for iid in ids:
    if iid==KEEP: continue
    r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=12)
    if r.status_code<300: paused+=1
    else: errs+=1
    if paused%50==0 and paused>0: print(f"  paused {paused}")
print(f"\nPAUSADOS: {paused} | ERR: {errs} | excluido KEEP: {KEEP}")
# verificar KEEP
k=requests.get(f"{API}/items/{KEEP}?attributes=status,available_quantity,title",headers=H,timeout=15).json()
print(f"KEEP {KEEP}: status={k.get('status')} qty={k.get('available_quantity')} '{k.get('title','')[:40]}'")
if k.get("status")!="active":
    body={"status":"active"}
    if (k.get("available_quantity") or 0)<1: body["available_quantity"]=1
    rk=requests.put(f"{API}/items/{KEEP}",headers=HJ,json=body,timeout=20)
    print(f"  reactivate -> {rk.status_code} {rk.text[:200] if rk.status_code>=300 else ''}")
print("DONE")
