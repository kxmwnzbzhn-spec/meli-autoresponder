#!/usr/bin/env python3
"""DIDER: keep one unit visible while enforcing ten real units per listing."""
import os, time, requests

API="https://api.mercadolibre.com"
SELLER_ID=3654003391
TIMEOUT=30
TICK=30
DURATION=int(os.environ.get("RUN_DURATION_SEC","19800"))
LIMITS={
    "MLM3442582695":10,
    "MLM3442582711":10,
    "MLM3442595743":10,
    "MLM3442595765":10,
    "MLM3442595771":10,
}

r=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_DIDER"],
},timeout=TIMEOUT)
r.raise_for_status()
tok=r.json()
with open("/tmp/dider_rotated_token","w") as h:
    h.write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
HJ={**H,"Content-Type":"application/json"}

me=requests.get(f"{API}/users/me",headers=H,timeout=TIMEOUT)
me.raise_for_status()
if int(me.json().get("id") or 0)!=SELLER_ID:
    raise RuntimeError(f"Cuenta incorrecta: {me.json().get('id')}")

def item(iid):
    q=requests.get(f"{API}/items/{iid}",headers=H,timeout=TIMEOUT)
    q.raise_for_status()
    d=q.json()
    if int(d.get("seller_id") or 0)!=SELLER_ID:
        raise RuntimeError(f"{iid}: seller inesperado")
    return d

def paid_units(iid):
    total=offset=0
    while True:
        q=requests.get(f"{API}/orders/search",headers=H,params={
            "seller":SELLER_ID,"q":iid,"limit":50,"offset":offset,"sort":"date_asc"
        },timeout=TIMEOUT)
        q.raise_for_status()
        body=q.json(); rows=body.get("results") or []
        for order in rows:
            if order.get("status") in {"cancelled","invalid"}:
                continue
            tags=set(order.get("tags") or [])
            approved=any(p.get("status")=="approved" for p in (order.get("payments") or []))
            if order.get("status") not in {"paid","partially_refunded"} and "paid" not in tags and not approved:
                continue
            for line in order.get("order_items") or []:
                if (line.get("item") or {}).get("id")==iid:
                    total+=int(line.get("quantity") or 0)
        offset+=len(rows)
        if not rows or offset>=int((body.get("paging") or {}).get("total") or 0):
            break
    return total

def enforce(iid,initial=False):
    sold=paid_units(iid)
    remaining=max(0,LIMITS[iid]-sold)
    d=item(iid)
    status=d.get("status"); qty=int(d.get("available_quantity") or 0)
    if initial or remaining<=2:
        print(f"[STOCK] {iid} initial=10 sold={sold} remaining={remaining} status={status} qty={qty}",flush=True)
    if remaining<=0:
        if status=="active":
            u=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=TIMEOUT)
            if u.status_code not in (200,201):
                raise RuntimeError(f"{iid}: pause HTTP {u.status_code} {u.text[:400]}")
        print(f"[PAUSED-EXHAUSTED] {iid}",flush=True)
        return
    if status=="active" and qty==1:
        return
    if status not in {"active","paused"}:
        print(f"[POLICY-SKIP] {iid} status={status} sub={d.get('sub_status')}",flush=True)
        return
    body={"available_quantity":1}
    if status=="paused":
        body["status"]="active"
    u=requests.put(f"{API}/items/{iid}",headers=HJ,json=body,timeout=TIMEOUT)
    if u.status_code not in (200,201):
        raise RuntimeError(f"{iid}: replenish HTTP {u.status_code} {u.text[:500]}")
    final=item(iid)
    if final.get("status")!="active" or int(final.get("available_quantity") or 0)!=1:
        raise RuntimeError(f"{iid}: verification status={final.get('status')} qty={final.get('available_quantity')}")
    print(f"[REPLENISHED] {iid} remaining={remaining} qty=1",flush=True)

for iid in LIMITS:
    enforce(iid,initial=True)
started=time.time(); cycles=0
while time.time()-started<DURATION:
    cycles+=1; cycle=time.time()
    for iid in LIMITS:
        try: enforce(iid)
        except Exception as exc: print(f"[ERROR] {iid}: {exc}",flush=True)
    time.sleep(max(0,TICK-(time.time()-cycle)))
print(f"[END] cycles={cycles}",flush=True)
