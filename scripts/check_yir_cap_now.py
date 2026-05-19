import os,requests,datetime as dt
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
today=dt.date.today().isoformat()
date_from=f"{today}T00:00:00.000-06:00"
sold=0; off=0
while True:
    r=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&limit=50&offset={off}",headers=H).json()
    res=r.get("results",[])
    if not res: break
    for o in res:
        if o.get("status") in ("cancelled","invalid"): continue
        for it in (o.get("order_items") or []):
            sold+=int(it.get("quantity",0) or 0)
    off+=50
    if off>=r.get("paging",{}).get("total",0): break
print(f"Ventas Yiriam hoy ({today}): {sold}")

# Listar active items
ids=[]
off=0
while True:
    r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=active&limit=100&offset={off}",headers=H).json()
    res=r.get("results",[])
    if not res: break
    ids+=res; off+=100
    if off>=r.get("paging",{}).get("total",0): break
print(f"Active items: {len(ids)}")
