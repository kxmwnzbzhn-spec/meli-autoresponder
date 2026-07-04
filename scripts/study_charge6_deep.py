"""
Estudio a fondo Charge 6: Adrián (AH) vs Mayrely (MC)
- Pull ALL orders (paid + cancelled) por item
- Pull ALL claims per account (all statuses+types)
- Match order_id → claim para clasificar
- Cuenta: devoluciones reales, reclamos abiertos, ordenes conflictivas
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
COMMISSION_PCT=0.13
SHIPPING_COST=70

def all_orders_of_item(seller_id, item_id, token):
    """Pull ALL orders for an item"""
    orders=[]
    offset=0
    H={"Authorization":f"Bearer {token}"}
    while True:
        r=requests.get(f"https://api.mercadolibre.com/orders/search",headers=H,
            params={"seller":seller_id,"item":item_id,"limit":50,"offset":offset},timeout=25).json()
        results=r.get("results",[])
        if not results: break
        # If MELI didn't accept 'item' filter, we must filter manually
        filtered=[o for o in results if any(oi.get("item",{}).get("id")==item_id for oi in o.get("order_items",[]))]
        orders.extend(filtered)
        total=r.get("paging",{}).get("total",0)
        offset+=50
        if offset>=total: break
        if offset>=5000: break
        time.sleep(0.1)
    return orders

def all_claims(token):
    """Pull ALL claims regardless of status/type"""
    all_c=[]
    H={"Authorization":f"Bearer {token}"}
    for stage in ["claim","dispute"]:
      for status in ["opened","closed"]:
        offset=0
        while offset<2000:
          r=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search",
              headers=H,params={"stage":stage,"status":status,"limit":50,"offset":offset},timeout=25).json()
          data=r.get("data",[])
          if not data: break
          all_c.extend(data)
          if len(data)<50: break
          offset+=50
          time.sleep(0.1)
    return all_c

print("Pulling claims...",flush=True)
CLAIMS_AH=all_claims(AT_AH)
CLAIMS_MC=all_claims(AT_MC)
print(f"Total claims: Adrián={len(CLAIMS_AH)} Mayrely={len(CLAIMS_MC)}",flush=True)

# Map claim by order_id
def index_claims(claims):
    idx={}
    for c in claims:
        rid=c.get("resource_id")
        if rid:
            idx.setdefault(str(rid),[]).append(c)
    return idx

CLAIMS_IDX={"Adrián":index_claims(CLAIMS_AH), "Mayrely":index_claims(CLAIMS_MC)}

TOT={}
for acc, cfg in ACCOUNTS.items():
    print(f"\n=========== {acc} ===========",flush=True)
    TOT[acc]={}
    for iid in cfg["items"]:
        print(f"\n--- {iid} ---",flush=True)
        item=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,price,sold_quantity",
            headers={"Authorization":f"Bearer {cfg['token']}"},timeout=10).json()
        title=(item.get("title") or "")[:60]
        sold_qty=item.get("sold_quantity",0)
        print(f"  {title[:50]} sold={sold_qty}",flush=True)
        
        orders=all_orders_of_item(cfg["seller_id"], iid, cfg["token"])
        print(f"  orders fetched: {len(orders)}",flush=True)
        
        paid_count=0; paid_units=0; paid_gross=0
        cancelled_count=0; cancelled_units=0
        claim_count=0; claim_return=0; claim_open=0; claim_closed=0; claim_mediation=0
        real_returns=0  # claims that resulted in refund/return execution
        
        for o in orders:
            st=o.get("status")
            oid=str(o.get("id"))
            # Get units + revenue for this item in this order
            q=0; up=0
            for oi in o.get("order_items",[]):
                if oi.get("item",{}).get("id")==iid:
                    q+=oi.get("quantity",1)
                    up=oi.get("unit_price",0)
            
            if st=="paid":
                paid_count+=1; paid_units+=q; paid_gross+=q*up
            elif st=="cancelled":
                cancelled_count+=1; cancelled_units+=q
            
            # Check claims for this order
            claims_here=CLAIMS_IDX[acc].get(oid,[])
            if claims_here:
                claim_count+=len(claims_here)
                for c in claims_here:
                    if c.get("type")=="returns": claim_return+=1
                    if c.get("type")=="mediations": claim_mediation+=1
                    if c.get("status")=="opened": claim_open+=1
                    else: claim_closed+=1
                    # Check if there's a resolution (refund/return completed)
                    res=c.get("resolution")
                    if res and (res.get("closed_by") or res.get("decision")):
                        real_returns+=1
        
        TOT[acc][iid]={
          "title":title,"sold_quantity":sold_qty,
          "paid_orders":paid_count,"paid_units":paid_units,"paid_gross":round(paid_gross,2),
          "cancelled_orders":cancelled_count,"cancelled_units":cancelled_units,
          "claims_total":claim_count,"claims_return_type":claim_return,"claims_mediation":claim_mediation,
          "claims_open":claim_open,"claims_closed":claim_closed,"real_returns":real_returns,
          "customers_kept":paid_units-real_returns,
        }
        print(f"  paid: {paid_count} orders / {paid_units}u / ${paid_gross:,.0f}",flush=True)
        print(f"  cancelled: {cancelled_count} orders",flush=True)
        print(f"  claims total: {claim_count} (return={claim_return} mediation={claim_mediation} open={claim_open} closed={claim_closed})",flush=True)
        print(f"  real returns/refunds executed: {real_returns}",flush=True)

print("\n\n========== RESUMEN ==========",flush=True)
print(json.dumps(TOT,indent=2,ensure_ascii=False),flush=True)

for acc, items in TOT.items():
    tu=sum(v["paid_units"] for v in items.values())
    tg=sum(v["paid_gross"] for v in items.values())
    tc=sum(v["claims_total"] for v in items.values())
    tret=sum(v["claims_return_type"] for v in items.values())
    trr=sum(v["real_returns"] for v in items.values())
    kept=tu-trr
    revenue_net=tg  # No estamos restando refunds acá, real refunds los quitamos abajo
    # Ajuste: unidades devueltas → restar sus ingresos
    avg_price=tg/tu if tu else 0
    refund_amount=avg_price*trr
    revenue_after_returns=tg-refund_amount
    prod_cost=PRODUCT_COST*kept
    commission=revenue_after_returns*COMMISSION_PCT
    shipping=SHIPPING_COST*tu  # se pagó envío por todas las órdenes, incluso las devueltas
    net=revenue_after_returns - prod_cost - commission - shipping
    print(f"\n{acc}:",flush=True)
    print(f"  Vendidas (paid): {tu}",flush=True)
    print(f"  Reclamos totales: {tc}",flush=True)
    print(f"    - tipo returns: {tret}",flush=True)
    print(f"    - devoluciones ejecutadas: {trr}",flush=True)
    print(f"  Se quedaron con el producto: {kept}",flush=True)
    print(f"  Gross paid: ${tg:,.0f}",flush=True)
    print(f"  Refund por devoluciones ({trr} × ${avg_price:,.0f}): -${refund_amount:,.0f}",flush=True)
    print(f"  Revenue neto: ${revenue_after_returns:,.0f}",flush=True)
    print(f"  Costo producto ({kept} × ${PRODUCT_COST}): -${prod_cost:,.0f}",flush=True)
    print(f"  Comisión MELI (13%): -${commission:,.0f}",flush=True)
    print(f"  Envío ({tu} × ${SHIPPING_COST}): -${shipping:,.0f}",flush=True)
    print(f"  UTILIDAD NETA: ${net:,.0f}",flush=True)
