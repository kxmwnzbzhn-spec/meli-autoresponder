"""Find buyers of MLM2967318097 (Claribel) with pending orders for substitution offer."""
import os, requests, json, time
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_CLARIBEL={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me["id"]; print(f"seller={uid}")

ITEM="MLM2967318097"
# Look at orders within last 60 days
import datetime as dt
since=(dt.datetime.utcnow()-dt.timedelta(days=60)).strftime("%Y-%m-%dT00:00:00.000Z")
print(f"\nSearching orders since {since} for item={ITEM}")

orders=[]
offset=0
while offset<5000:
    params={
        "seller":uid,
        "item":ITEM,
        "order.date_created.from":since,
        "limit":50,"offset":offset,
        "sort":"date_desc",
    }
    rr=requests.get(f"{API}/orders/search",headers=H,params=params,timeout=20).json()
    res=rr.get("results") or []
    print(f"  offset={offset} got={len(res)}")
    orders.extend(res)
    if len(res)<50: break
    offset+=50

print(f"\nTotal orders found: {len(orders)}")
# Group by status
by_status={}
buyers_unique={}
relevant=[]
for o in orders:
    st=o.get("status")
    by_status[st]=by_status.get(st,0)+1
    # Buyer info
    buyer=o.get("buyer") or {}
    buyer_id=buyer.get("id")
    # Shipping/pack
    shipping=o.get("shipping") or {}
    sid=shipping.get("id")
    pack=o.get("pack_id") or o.get("id")
    # Order items
    items=o.get("order_items") or []
    item_ids=[(i.get("item") or {}).get("id") for i in items]
    if ITEM not in item_ids: continue
    # Relevant statuses: paid (haven't shipped) or confirmed/pending
    if st in ("paid","confirmed","pending"):
        relevant.append({
            "order_id":o.get("id"),
            "pack_id":pack,
            "buyer_id":buyer_id,
            "buyer_nick":buyer.get("nickname"),
            "status":st,
            "shipping_id":sid,
            "shipping_status":(shipping.get("status") or "?"),
            "date_created":o.get("date_created"),
            "qty":sum((i.get("quantity") or 0) for i in items if (i.get("item") or {}).get("id")==ITEM),
        })

print("\nBy status:")
for k,v in by_status.items(): print(f"  {k}: {v}")
print(f"\nRelevant (paid/confirmed/pending): {len(relevant)}")
for r in relevant[:35]:
    print(f"  order={r['order_id']} pack={r['pack_id']} buyer={r['buyer_id']} ({r['buyer_nick']}) | status={r['status']} ship={r['shipping_status']} | {r['date_created']} | qty={r['qty']}")

# Persist
with open("/tmp/buyers.json","w") as f:
    json.dump(relevant, f, indent=2)
print(f"\nSaved {len(relevant)} buyers to /tmp/buyers.json")
