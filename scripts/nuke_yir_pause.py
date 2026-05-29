import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_YC_NEW={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=15).json()
UID=me["id"]
print(f"seller={UID} nick={me.get('nickname')}")

def list_open():
    ids=set()
    for st in ["active","under_review","programmed"]:
        scroll=None
        while True:
            p={"search_type":"scan","limit":100,"status":st}
            if scroll: p["scroll_id"]=scroll
            r=requests.get(f"{API}/users/{UID}/items/search",headers=H,params=p,timeout=30).json()
            ids.update(r.get("results",[]))
            scroll=r.get("scroll_id")
            if not scroll or not r.get("results"): break
    return list(ids)

def pause_one(sid, attempts=4):
    bo=2
    for k in range(attempts):
        r=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"paused"},timeout=20)
        if r.status_code==429: time.sleep(bo); bo*=2; continue
        return r.status_code
    return 429

for pass_n in (1,2,3):
    ids=list_open()
    print(f"\n=== PASS {pass_n}: open={len(ids)} ===")
    if not ids:
        print("Yiriam todo pausado.")
        break
    ok=err=0
    for i,sid in enumerate(ids,1):
        sc=pause_one(sid)
        if sc in (200,201): ok+=1
        else: err+=1
        if i%50==0 or sc not in (200,201):
            print(f"  [{i}/{len(ids)}] {sid} -> {sc}")
        time.sleep(0.3)
    print(f"  pass{pass_n} ok={ok} err={err}")
    time.sleep(3)

final=list_open()
print(f"\n=== FINAL === still_open={len(final)}")
for sid in final[:20]: print(f"  remaining: {sid}")
