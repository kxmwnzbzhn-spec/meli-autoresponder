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

def close_one(sid, attempts=4):
    backoff=2
    for k in range(attempts):
        g=requests.get(f"{API}/items/{sid}",headers=H,timeout=15)
        if g.status_code!=200:
            return "ERR-GET",g.status_code
        st=g.json().get("status")
        if st in ("closed","inactive"): return "ALREADY",st
        if st in ("active","under_review","paused","programmed"):
            rp=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"paused"},timeout=20)
            if rp.status_code==429:
                time.sleep(backoff); backoff*=2; continue
            time.sleep(0.6)
        rc=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"closed"},timeout=20)
        if rc.status_code==429:
            time.sleep(backoff); backoff*=2; continue
        if rc.status_code in (200,201):
            rd=requests.put(f"{API}/items/{sid}",headers=HJ,json={"deleted":"true"},timeout=20)
            return "OK", rc.status_code
        return "ERR-CLOSE", f"{rc.status_code} {rc.text[:100]}"
    return "ERR-RATE", "exhausted retries"

# pass 1: scan all statuses
def all_ids():
    ids=set()
    for st in ["active","paused","under_review","programmed","inactive","closed"]:
        scroll=None
        while True:
            p={"search_type":"scan","limit":100,"status":st}
            if scroll: p["scroll_id"]=scroll
            r=requests.get(f"{API}/users/{UID}/items/search",headers=H,params=p,timeout=30).json()
            ids.update(r.get("results",[]))
            scroll=r.get("scroll_id")
            if not scroll or not r.get("results"): break
    # legacy paging without status filter
    r=requests.get(f"{API}/users/{UID}/items/search",headers=H,params={"limit":50,"offset":0},timeout=30).json()
    ids.update(r.get("results",[]))
    tot=r.get("paging",{}).get("total",0)
    for off in range(50,min(tot,2000),50):
        r=requests.get(f"{API}/users/{UID}/items/search",headers=H,params={"limit":50,"offset":off},timeout=30).json()
        ids.update(r.get("results",[]))
    return ids

# do up to 3 passes (catches stragglers + 429 retry)
for pass_n in (1,2,3):
    ids=sorted(all_ids())
    open_ids=[]
    # quick GET to skip already-closed
    for i in range(0, len(ids), 20):
        batch=",".join(ids[i:i+20])
        r=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,status"},timeout=30).json()
        for x in r:
            if x.get("code")==200 and x["body"].get("status") not in ("closed","inactive"):
                open_ids.append(x["body"]["id"])
    print(f"\n=== PASS {pass_n}: {len(ids)} total / {len(open_ids)} aún abiertos ===")
    if not open_ids:
        print("✓ Angel limpio.")
        break
    ok=err=0
    for i,sid in enumerate(open_ids,1):
        res,detail=close_one(sid)
        if res=="OK": ok+=1
        else: err+=1
        print(f"  [{i}/{len(open_ids)}] {sid} -> {res} {detail}")
        time.sleep(0.5)
    print(f"  pass{pass_n} done: ok={ok} err={err}")
    time.sleep(3)

# Final verification
ids=sorted(all_ids())
still_open=[]
for i in range(0, len(ids), 20):
    batch=",".join(ids[i:i+20])
    r=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,status"},timeout=30).json()
    for x in r:
        if x.get("code")==200 and x["body"].get("status") not in ("closed","inactive"):
            still_open.append((x["body"]["id"], x["body"].get("status")))
print(f"\n=== FINAL ===")
print(f"total_items={len(ids)} still_open={len(still_open)}")
for s,st in still_open[:10]:
    print(f"  remaining: {s} {st}")
