import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_ANGEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_ANGEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
UID=3009687392

# Collect ALL ids across all statuses (paged + scroll fallback)
ids=set()
for st in ["active","paused","under_review","inactive","closed","programmed"]:
    scroll=None
    while True:
        p={"search_type":"scan","limit":100,"status":st}
        if scroll: p["scroll_id"]=scroll
        r=requests.get(f"{API}/users/{UID}/items/search",headers=H,params=p,timeout=30).json()
        ids.update(r.get("results",[]))
        scroll=r.get("scroll_id")
        if not scroll or not r.get("results"): break
# also legacy paging without status
r=requests.get(f"{API}/users/{UID}/items/search",headers=H,params={"limit":50,"offset":0},timeout=30).json()
ids.update(r.get("results",[]))
total=r.get("paging",{}).get("total",0)
for off in range(50,min(total,2000),50):
    r=requests.get(f"{API}/users/{UID}/items/search",headers=H,params={"limit":50,"offset":off},timeout=30).json()
    ids.update(r.get("results",[]))

ids=list(ids)
print(f"TOTAL items to finalize: {len(ids)}")

ok=err=skip=0
for i,sid in enumerate(ids,1):
    g=requests.get(f"{API}/items/{sid}",headers=H,timeout=15).json()
    st=g.get("status")
    if st in ("closed","inactive"):
        skip+=1
        print(f"  [{i}/{len(ids)}] {sid} already {st}")
        continue
    # pause if active or under_review
    if st in ("active","under_review","paused","programmed"):
        rp=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"paused"},timeout=20)
        if rp.status_code>=400: print(f"    pause warn: {rp.status_code} {rp.text[:120]}")
    rc=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"closed"},timeout=20)
    rd=requests.put(f"{API}/items/{sid}",headers=HJ,json={"deleted":"true"},timeout=20)
    if rc.status_code in (200,201):
        ok+=1
        print(f"  [{i}/{len(ids)}] {sid} -> closed")
    else:
        err+=1
        print(f"  [{i}/{len(ids)}] {sid} ERR close {rc.status_code} {rc.text[:140]}")
    time.sleep(0.2)
print(f"\nFINALIZE DONE ok={ok} err={err} skip={skip}")
