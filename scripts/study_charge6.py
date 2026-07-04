"""
Estudio Charge 6: Adrián (AH) vs Mayrely (MC)
- Pull all orders per item + status
- Classify: sold_paid, refunded, returned, claimed
- Compute NET revenue: gross - product_cost - MELI_fees - shipping
"""
import os, requests, time, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SEC=os.environ["MELI_APP_SECRET"]

def auth(rt):
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={
      "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SEC,"refresh_token":rt},timeout=20).json()
    return r["access_token"]

AT_AH=auth(os.environ["MELI_REFRESH_TOKEN_AH"])
AT_MC=auth(os.environ["MELI_REFRESH_TOKEN_MAYRELY"])

ACCOUNTS={
  "Adrián":  {"token":AT_AH,"seller_id":3417664339,"items":["MLM5526819898","MLM5526806736","MLM3034025531"]},
  "Mayrely": {"token":AT_MC,"seller_id":3419500448,"items":["MLM3045612883","MLM5569443994","MLM5569443364"]},
}

PRODUCT_COST=500
COMMISSION_PCT=0.13  # gold_pro bocinas ~13%
SHIPPING_COST=70     # aprox por orden con envío MELI

def orders_of_item(seller_id, item_id, token):
    orders=[]
    offset=0
    while offset<3000:
        H={"Authorization":f"Bearer {token}"}
        r=requests.get(f"https://api.mercadolibre.com/orders/search",
            headers=H,params={"seller":seller_id,"limit":50,"offset":offset,"sort":"date_desc"},timeout=20).json()
        results=r.get("results",[])
        if not results: break
        for o in results:
            # Filter by item
            for oi in o.get("order_items",[]):
                if oi.get("item",{}).get("id")==item_id:
                    orders.append(o)
                    break
        total=r.get("paging",{}).get("total",0)
        if offset>=total: break
        offset+=50
        time.sleep(0.15)
    return orders

def claims_of_item(seller_id, item_id, token):
    """Count claims by item"""
    claims=[]
    off=0
    while off<500:
        r=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search",
            headers={"Authorization":f"Bearer {token}"},
            params={"related_item_id":item_id,"limit":50,"offset":off},timeout=20).json()
        data=r.get("data",[])
        if not data: break
        claims.extend(data)
        if len(data)<50: break
        off+=50
    return claims

TOT={"Adrián":{},"Mayrely":{}}
grand={"units":0,"gross":0,"refunds":0,"net_units":0,"claims":0,"returns":0}

for acc, cfg in ACCOUNTS.items():
    print(f"\n=========== {acc} ===========",flush=True)
    for iid in cfg["items"]:
        print(f"\n--- {iid} ---",flush=True)
        item=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,price,sold_quantity,status",
            headers={"Authorization":f"Bearer {cfg['token']}"},timeout=10).json()
        title=(item.get("title") or "")[:60]
        sold_qty=item.get("sold_quantity",0)
        price=item.get("price",0)
        print(f"  title: {title}",flush=True)
        print(f"  sold_quantity: {sold_qty}, price: ${price}",flush=True)
        
        # Pull orders — cap to 500 to not blow timeout
        orders=orders_of_item(cfg["seller_id"], iid, cfg["token"])
        print(f"  orders fetched: {len(orders)}",flush=True)
        
        # Classify
        paid=0; refunded=0; cancelled=0; gross=0; refund_amt=0; units=0
        for o in orders:
            for oi in o.get("order_items",[]):
                if oi.get("item",{}).get("id")==iid:
                    q=oi.get("quantity",1)
                    up=oi.get("unit_price",0)
                    units+=q
                    st=o.get("status")
                    if st=="paid":
                        paid+=1
                        gross+=q*up
                    elif st=="cancelled":
                        cancelled+=1
                        refunded+=1
                        refund_amt+=q*up
                    else:
                        # partially paid or invalid
                        pass
        
        # Claims
        claims=claims_of_item(cfg["seller_id"], iid, cfg["token"])
        cl_total=len(claims)
        cl_open=sum(1 for c in claims if c.get("status")=="opened")
        cl_closed=sum(1 for c in claims if c.get("status")=="closed")
        cl_returns=sum(1 for c in claims if c.get("type")=="returns")
        
        # Actual returns (claims that resulted in return)
        # For simplicity, count return-type claims as "returns processed"
        returns=cl_returns
        
        result={
            "title":title,
            "sold_quantity":sold_qty,
            "orders_paid":paid,
            "orders_cancelled":cancelled,
            "units_ordered":units,
            "gross":gross,
            "refunded_amt":refund_amt,
            "claims_total":cl_total,
            "claims_open":cl_open,
            "claims_closed":cl_closed,
            "claims_return_type":cl_returns,
            "returns":returns,
        }
        TOT[acc][iid]=result
        print(f"  paid orders: {paid} ({units}u) gross=${gross:,.0f}",flush=True)
        print(f"  cancelled/refunded: {cancelled} = ${refund_amt:,.0f}",flush=True)
        print(f"  claims: {cl_total} (returns:{cl_returns} open:{cl_open} closed:{cl_closed})",flush=True)
        
        grand["units"]+=units
        grand["gross"]+=gross
        grand["refunds"]+=refund_amt
        grand["claims"]+=cl_total
        grand["returns"]+=returns

print("\n\n========== RESUMEN GLOBAL ==========",flush=True)
print(json.dumps(TOT,indent=2,ensure_ascii=False),flush=True)

# Compute net for each account
for acc, items in TOT.items():
    total_units=sum(v["units_ordered"] for v in items.values())
    total_gross=sum(v["gross"] for v in items.values())
    total_refund=sum(v["refunded_amt"] for v in items.values())
    total_returns=sum(v["returns"] for v in items.values())
    total_claims=sum(v["claims_total"] for v in items.values())
    net_sold_units=total_units - total_returns  # kept by customer
    revenue_after_refunds=total_gross - total_refund
    product_cost=PRODUCT_COST * total_units
    commission=revenue_after_refunds * COMMISSION_PCT
    shipping=SHIPPING_COST * total_units
    net_profit=revenue_after_refunds - product_cost - commission - shipping
    print(f"\n{acc}:",flush=True)
    print(f"  Unidades vendidas totales: {total_units}",flush=True)
    print(f"  Reclamos: {total_claims}",flush=True)
    print(f"  Devoluciones (return claims): {total_returns}",flush=True)
    print(f"  Se quedaron los clientes: {net_sold_units}",flush=True)
    print(f"  Gross revenue: ${total_gross:,.0f}",flush=True)
    print(f"  Refunds/cancelaciones: -${total_refund:,.0f}",flush=True)
    print(f"  Revenue neto: ${revenue_after_refunds:,.0f}",flush=True)
    print(f"  Costo producto (${PRODUCT_COST}/u): -${product_cost:,.0f}",flush=True)
    print(f"  Comisión MELI ({int(COMMISSION_PCT*100)}%): -${commission:,.0f}",flush=True)
    print(f"  Envío (${SHIPPING_COST}/u): -${shipping:,.0f}",flush=True)
    print(f"  UTILIDAD NETA: ${net_profit:,.0f}",flush=True)
