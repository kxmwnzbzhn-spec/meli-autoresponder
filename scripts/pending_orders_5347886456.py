import os,requests,json
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
TARGET="MLM5347886456"
# Get orders for this item — recent paid
off=0; orders=[]
while True:
    r=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.status=paid&sort=date_desc&limit=50&offset={off}",headers=H).json()
    res=r.get("results",[])
    if not res: break
    for o in res:
        for it in (o.get("order_items") or []):
            if it.get("item",{}).get("id")==TARGET:
                orders.append(o)
                break
    off+=50
    if off>=r.get("paging",{}).get("total",0) or len(orders)>30: break

print(f"Total paid orders found for {TARGET}: {len(orders)}\n")
# For each, check shipping status
pending=[]
shipped=[]
for o in orders:
    oid=o.get("id")
    buyer=o.get("buyer",{}).get("nickname","?")
    date=o.get("date_created","")[:10]
    qty=sum(it.get("quantity",0) for it in (o.get("order_items") or []) if it.get("item",{}).get("id")==TARGET)
    ship_id=o.get("shipping",{}).get("id")
    ship_status="?"
    ship_sub="?"
    if ship_id:
        s=requests.get(f"https://api.mercadolibre.com/shipments/{ship_id}",headers=H).json()
        ship_status=s.get("status","?")
        ship_sub=s.get("substatus","?")
    row={"oid":oid,"buyer":buyer,"date":date,"qty":qty,"ship_status":ship_status,"ship_sub":ship_sub}
    if ship_status in ("ready_to_ship","pending","handling") and ship_sub in ("ready_to_print","printed","invoice_pending","ready_to_ship",None,"in_hub","in_packing_list"):
        pending.append(row)
    else:
        shipped.append(row)
print(f"PENDING (ready_to_ship / sin enviar): {len(pending)}")
for r in pending[:30]:
    print(f"  {r['oid']} {r['date']} qty={r['qty']} buyer={r['buyer'][:20]} ship={r['ship_status']}/{r['ship_sub']}")
print(f"\nALREADY SHIPPED / DELIVERED: {len(shipped)}")
for r in shipped[:30]:
    print(f"  {r['oid']} {r['date']} qty={r['qty']} ship={r['ship_status']}/{r['ship_sub']}")
