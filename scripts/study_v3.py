"""Estudio Charge 6 v3 — usando order.status + q= para captura completa"""
import os, requests, time, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SEC=os.environ["MELI_APP_SECRET"]

def auth(rt):
    return requests.post("https://api.mercadolibre.com/oauth/token",data={
      "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SEC,"refresh_token":rt},timeout=20).json()["access_token"]

AT_AH=auth(os.environ["MELI_REFRESH_TOKEN_AH"])
AT_MC=auth(os.environ["MELI_REFRESH_TOKEN_MAYRELY"])

ACCOUNTS={
  "Adrián":  {"token":AT_AH,"seller_id":3417664339,"items":["MLM5526819898","MLM5526806736","MLM3034025531"]},
  "Mayrely": {"token":AT_MC,"seller_id":3419500448,"items":["MLM3045612883","MLM5569443994","MLM5569443364"]},
}

PRODUCT_COST=500
COMMISSION_PCT=0.13
SHIPPING_COST=70

def orders_by_item(seller_id, item_id, token, order_status=None):
    """Pull orders filtering by item_id via q= (item title)"""
    orders=[]
    seen=set()
    H={"Authorization":f"Bearer {token}"}
    # Use q=item_id which some MELI APIs support
    params_base={"seller":seller_id,"limit":50}
    if order_status:
        params_base["order.status"]=order_status
    # Try /orders/search with item.id filter as suffix
    for extra_param in [{"q":item_id},{"tags":item_id}]:
        p=dict(params_base)
        p.update(extra_param)
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
                    seen.add(oid)
                    orders.append(o)
            total=j.get("paging",{}).get("total",0)
            offset+=50
            if offset>=total: break
            time.sleep(0.08)
        if orders: break  # if q= worked, use it
    return orders

def all_orders_paginated(seller_id, item_id, token):
    """Fallback: brute force all orders paginating up to 20000"""
    orders=[]
    seen=set()
    H={"Authorization":f"Bearer {token}"}
    for status in ["paid","cancelled"]:
        offset=0
        while offset<15000:
            r=requests.get("https://api.mercadolibre.com/orders/search",headers=H,
                params={"seller":seller_id,"order.status":status,"limit":50,"offset":offset,"sort":"date_desc"},timeout=25)
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

TOT={}
for acc, cfg in ACCOUNTS.items():
    print(f"\n=========== {acc} ===========",flush=True)
    TOT[acc]={}
    for iid in cfg["items"]:
        print(f"\n--- {iid} ---",flush=True)
        item=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,price,sold_quantity",
            headers={"Authorization":f"Bearer {cfg['token']}"},timeout=10).json()
        sold_qty=item.get("sold_quantity",0)
        title=(item.get("title") or "")[:60]
        print(f"  {title[:50]} sold_qty={sold_qty}",flush=True)
        
        # First try q= method
        orders=orders_by_item(cfg["seller_id"], iid, cfg["token"])
        print(f"  via q=: {len(orders)}",flush=True)
        # If less than sold_qty, fall back to brute force
        if len(orders)<sold_qty*0.8:
            print(f"  fallback to brute force paginate...",flush=True)
            orders_bf=all_orders_paginated(cfg["seller_id"], iid, cfg["token"])
            if len(orders_bf)>len(orders):
                orders=orders_bf
                print(f"  via brute force: {len(orders)}",flush=True)
        
        paid_count=0; paid_units=0; paid_gross=0
        cancelled_count=0; cancelled_units=0
        for o in orders:
            st=o.get("status")
            q=0; up=0
            for oi in o.get("order_items",[]):
                if oi.get("item",{}).get("id")==iid:
                    q+=oi.get("quantity",1)
                    up=oi.get("unit_price",0)
            if st=="paid":
                paid_count+=1; paid_units+=q; paid_gross+=q*up
            elif st=="cancelled":
                cancelled_count+=1; cancelled_units+=q
        
        TOT[acc][iid]={
          "sold_quantity":sold_qty,"orders_fetched":len(orders),
          "paid_orders":paid_count,"paid_units":paid_units,"paid_gross":round(paid_gross,2),
          "cancelled_orders":cancelled_count,
        }
        print(f"  paid: {paid_count} orders / {paid_units}u / ${paid_gross:,.0f}",flush=True)
        print(f"  cancelled: {cancelled_count}",flush=True)

print("\n\n========== RESUMEN v3 ==========",flush=True)
print(json.dumps(TOT,indent=2,ensure_ascii=False),flush=True)

for acc, items in TOT.items():
    tu=sum(v["paid_units"] for v in items.values())
    tg=sum(v["paid_gross"] for v in items.values())
    prod_cost=PRODUCT_COST*tu
    commission=tg*COMMISSION_PCT
    shipping=SHIPPING_COST*tu
    net=tg - prod_cost - commission - shipping
    print(f"\n{acc}: paid_units={tu} gross=${tg:,.0f} prod=${prod_cost:,.0f} comm=${commission:,.0f} ship=${shipping:,.0f} → NET=${net:,.0f}",flush=True)
