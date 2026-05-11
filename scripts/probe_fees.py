import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]; RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]

# Get a recent paid order
o=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.status=paid&limit=3&sort=date_desc",headers=H).json()
results=o.get("results",[])
print(f"Got {len(results)} orders\n")

for ord in results[:2]:
    oid=ord.get("id")
    pid=(ord.get("payments") or [{}])[0].get("id") if ord.get("payments") else None
    print(f"\n=== ORDER {oid} ===")
    print(f"total_amount: {ord.get('total_amount')}")
    print(f"paid_amount: {ord.get('paid_amount')}")
    
    # Detail order
    full=requests.get(f"https://api.mercadolibre.com/orders/{oid}",headers=H).json()
    
    # Order items
    for it in full.get("order_items",[]):
        print(f"  item: ${it.get('unit_price')} x {it.get('quantity')} | sale_fee={it.get('sale_fee')}")
    
    # Payments con TODOS los fields
    for p in full.get("payments",[]):
        print(f"\n  PAYMENT {p.get('id')}:")
        for k,v in p.items():
            if k=="fee_details": 
                print(f"    fee_details:")
                for fd in v or []:
                    print(f"      {fd}")
            elif k in ("transaction_amount","taxes_amount","marketplace_fee","shipping_cost","installment_amount","total_paid_amount","transaction_amount_refunded","status","status_detail","reason","payment_type","date_approved"):
                print(f"    {k}: {v}")
    
    # Payment detalle directo
    if pid:
        pay=requests.get(f"https://api.mercadolibre.com/payments/{pid}",headers=H,timeout=15)
        print(f"\n  /payments/{pid}: status={pay.status_code}")
        if pay.status_code==200:
            j=pay.json()
            for k in ("transaction_amount","taxes_amount","marketplace_fee","shipping_cost","total_paid_amount","fee_details","charges_details","accounts_info","collector_id","transaction_details"):
                if k in j: print(f"    {k}: {json.dumps(j[k],ensure_ascii=False)[:300]}")
