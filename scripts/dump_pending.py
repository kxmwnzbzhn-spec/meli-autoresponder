import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
SELLER=me["id"]
ITEM="MLM2967318097"
import datetime as dt
since=(dt.datetime.utcnow()-dt.timedelta(days=60)).strftime("%Y-%m-%dT00:00:00.000Z")
orders=[]; offset=0
while offset<5000:
    rr=requests.get(f"{API}/orders/search",headers=H,params={
        "seller":SELLER,"item":ITEM,"order.date_created.from":since,
        "limit":50,"offset":offset,"sort":"date_desc"},timeout=20).json()
    res=rr.get("results") or []
    orders.extend(res)
    if len(res)<50: break
    offset+=50

SENT={"2000016726783822","2000016715330888"}
out=[]
for o in orders:
    if o.get("status")!="paid": continue
    items=o.get("order_items") or []
    if not any((i.get("item") or {}).get("id")==ITEM for i in items): continue
    oid=str(o.get("id"))
    if oid in SENT: continue
    buyer=o.get("buyer") or {}
    pack=o.get("pack_id") or o.get("id")
    out.append({
        "order_id":oid,
        "pack_id":str(pack),
        "buyer_id":buyer.get("id"),
        "buyer_nick":buyer.get("nickname"),
        "date":(o.get("date_created") or "")[:10],
    })
print(f"COUNT:{len(out)}")
print("JSONSTART")
print(json.dumps(out, ensure_ascii=False))
print("JSONEND")
