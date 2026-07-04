"""V4 - see ALL order statuses + full breakdown + returns via /post-purchase/v2/returns"""
import os, requests, time, json
from collections import Counter
APP_ID=os.environ["MELI_APP_ID"]; APP_SEC=os.environ["MELI_APP_SECRET"]

def auth(rt):
    return requests.post("https://api.mercadolibre.com/oauth/token",data={
      "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SEC,"refresh_token":rt},timeout=20).json()["access_token"]

AT_AH=auth(os.environ["MELI_REFRESH_TOKEN_AH"])
AT_MC=auth(os.environ["MELI_REFRESH_TOKEN_MAYRELY"])

ACCOUNTS={
  "Adrián":  {"token":AT_AH,"seller_id":3417664339,"items":["MLM5526819898","MLM5526806736"]},
  "Mayrely": {"token":AT_MC,"seller_id":3419500448,"items":["MLM3045612883","MLM5569443994","MLM5569443364"]},
}

def orders_by_item(seller_id, item_id, token):
    orders=[]; seen=set()
    H={"Authorization":f"Bearer {token}"}
    p={"seller":seller_id,"limit":50,"q":item_id}
    offset=0
    while offset<10000:
        p["offset"]=offset
        r=requests.get("https://api.mercadolibre.com/orders/search",headers=H,params=p,timeout=25)
        if r.status_code!=200: break
        j=r.json()
        data=j.get("results",[])
        if not data: break
        for o in data:
            oid=o.get("id")
            if oid in seen: continue
            if any(oi.get("item",{}).get("id")==item_id for oi in o.get("order_items",[])):
                seen.add(oid); orders.append(o)
        total=j.get("paging",{}).get("total",0)
        offset+=50
        if offset>=total: break
        time.sleep(0.06)
    return orders

for acc, cfg in ACCOUNTS.items():
    print(f"\n=========== {acc} ===========",flush=True)
    for iid in cfg["items"]:
        print(f"\n--- {iid} ---",flush=True)
        item=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,sold_quantity",
            headers={"Authorization":f"Bearer {cfg['token']}"},timeout=10).json()
        sold_qty=item.get("sold_quantity",0)
        print(f"  MELI sold_quantity={sold_qty}",flush=True)
        
        orders=orders_by_item(cfg["seller_id"], iid, cfg["token"])
        print(f"  Orders fetched: {len(orders)}",flush=True)
        
        # Group by status
        by_status=Counter()
        gross_by_status={}
        units_by_status={}
        for o in orders:
            st=o.get("status") or "unknown"
            by_status[st]+=1
            q=0; up=0
            for oi in o.get("order_items",[]):
                if oi.get("item",{}).get("id")==iid:
                    q+=oi.get("quantity",1); up=oi.get("unit_price",0)
            gross_by_status[st]=gross_by_status.get(st,0)+q*up
            units_by_status[st]=units_by_status.get(st,0)+q
        
        for st,cnt in by_status.most_common():
            g=gross_by_status.get(st,0); u=units_by_status.get(st,0)
            print(f"    status={st}: orders={cnt} units={u} gross=${g:,.0f}",flush=True)
        
        # Total "revenue-generating" (paid + confirmed)
        rev_orders=by_status.get("paid",0)+by_status.get("confirmed",0)
        rev_gross=gross_by_status.get("paid",0)+gross_by_status.get("confirmed",0)
        print(f"  → revenue orders (paid+confirmed): {rev_orders}, gross=${rev_gross:,.0f}",flush=True)
