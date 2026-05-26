import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_RAY={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=20).json()
UID=me["id"]
print(f"seller={UID} nick={me.get('nickname')} email={me.get('email')}")

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
    return ids

def close_one(sid, attempts=4):
    backoff=2
    for k in range(attempts):
        g=requests.get(f"{API}/items/{sid}",headers=H,timeout=15)
        if g.status_code!=200: return "ERR-GET",g.status_code
        st=g.json().get("status")
        if st in ("closed","inactive"): return "ALREADY",st
        if st in ("active","under_review","paused","programmed"):
            rp=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"paused"},timeout=20)
            if rp.status_code==429: time.sleep(backoff); backoff*=2; continue
            time.sleep(0.4)
        rc=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"closed"},timeout=20)
        if rc.status_code==429: time.sleep(backoff); backoff*=2; continue
        if rc.status_code in (200,201):
            requests.put(f"{API}/items/{sid}",headers=HJ,json={"deleted":"true"},timeout=20)
            return "OK", rc.status_code
        return "ERR-CLOSE", f"{rc.status_code} {rc.text[:100]}"
    return "ERR-RATE","exhausted"

ids=sorted(all_ids())
print(f"\n=== AUDIT === total items (all statuses): {len(ids)}")
by_st={}; with_sales=0; tot_sold=0
for i in range(0, len(ids), 20):
    batch=",".join(ids[i:i+20])
    r=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,status,sold_quantity"},timeout=30).json()
    for x in r:
        if x.get("code")==200:
            b=x["body"]
            by_st[b.get("status")]=by_st.get(b.get("status"),0)+1
            sq=b.get("sold_quantity") or 0
            if sq>0: with_sales+=1
            tot_sold+=sq
for s,n in sorted(by_st.items(),key=lambda x:-x[1]):
    print(f"  {s}: {n}")
print(f"items con ventas>0: {with_sales}  total_sold_units={tot_sold}")

for pass_n in (1,2,3):
    ids=sorted(all_ids())
    open_ids=[]
    for i in range(0, len(ids), 20):
        batch=",".join(ids[i:i+20])
        r=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,status"},timeout=30).json()
        for x in r:
            if x.get("code")==200 and x["body"].get("status") not in ("closed","inactive"):
                open_ids.append(x["body"]["id"])
    print(f"\n=== PASS {pass_n}: scanned={len(ids)} pending_close={len(open_ids)} ===")
    if not open_ids:
        print("Raymundo limpio.")
        break
    ok=err=0
    for i,sid in enumerate(open_ids,1):
        res,detail=close_one(sid)
        if res=="OK": ok+=1
        else: err+=1
        if res!="OK" or i%50==0:
            print(f"  [{i}/{len(open_ids)}] {sid} -> {res} {detail}")
        time.sleep(0.35)
    print(f"  pass{pass_n} ok={ok} err={err}")
    time.sleep(3)

ids=sorted(all_ids())
still_open=[]
for i in range(0, len(ids), 20):
    batch=",".join(ids[i:i+20])
    r=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,status"},timeout=30).json()
    for x in r:
        if x.get("code")==200 and x["body"].get("status") not in ("closed","inactive"):
            still_open.append((x["body"]["id"], x["body"].get("status")))
print(f"\n=== FINAL === total={len(ids)} still_open={len(still_open)}")
for s,st in still_open[:20]:
    print(f"  remaining: {s} {st}")
