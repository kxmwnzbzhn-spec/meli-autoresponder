import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=20).json()
UID=me["id"]
print(f"seller={UID} nick={me.get('nickname')}")

# scroll all active
ids=[]; scroll=None
while True:
    p={"search_type":"scan","limit":100,"status":"active"}
    if scroll: p["scroll_id"]=scroll
    r=requests.get(f"{API}/users/{UID}/items/search",headers=H,params=p,timeout=30).json()
    ids+=r.get("results",[])
    scroll=r.get("scroll_id")
    if not scroll or not r.get("results"): break
print(f"active_total={len(ids)}")

ok=err=0
for i,sid in enumerate(ids,1):
    r=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"paused"},timeout=30)
    if r.status_code in (200,201):
        ok+=1
        print(f"  [{i}/{len(ids)}] {sid} -> paused")
    else:
        err+=1
        print(f"  [{i}/{len(ids)}] {sid} -> {r.status_code} {r.text[:140]}")
    time.sleep(0.25)
print(f"\nDONE ok={ok} err={err}")
