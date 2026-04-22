import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

with open("stock_config.json") as f: sc=json.load(f)

# Actualizar Go 4 catalogos con stock total por color
GO4_UPDATES=[
    ("MLM2880898041","Go 4","Azul",499),       # antes 0
    ("MLM2880766117","Go 4","Negra",200),      # antes 25
    ("MLM2880762615","Go 4","Camuflaje",537),  # antes 12 (pending)
    ("MLM2880877631","Go 4","Rosa",128),       # sin cambio
]

print("=== Go 4 actualizado ===")
for iid,m,c,stock in GO4_UPDATES:
    old=sc.get(iid,{}).get("real_stock","?")
    sc[iid]={
        "real_stock": stock,
        "sku": f"CAT-NEW-Go4-{c.upper()}",
        "label": f"Catalog NEW {m} {c}",
        "auto_replenish": stock>0,
        "replenish_quantity": 1,
        "min_visible_stock": 1,
        "deleted": False,
        "source":"bodega_electronica"
    }
    print(f"  {iid} [{m} {c}] {old} -> {stock}")

# MELI: visible = 1 si hay stock
for iid,m,c,stock in GO4_UPDATES:
    visible = 1 if stock>0 else 0
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    if it.get("status") in ("active","paused"):
        cur=it.get("available_quantity",0)
        if cur!=visible:
            rr=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"available_quantity":visible},timeout=20)
            print(f"  {iid}: visible {cur}->{visible} {rr.status_code}")
            # reactivar si estaba pausado por out_of_stock
            if it.get("status")=="paused" and stock>0:
                rr2=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"active"},timeout=20)
                print(f"    activar: {rr2.status_code}")

with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print("OK")
