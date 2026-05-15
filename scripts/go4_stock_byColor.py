import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

# AGOTADOS (Negro, Azul Marino) — pause confirm
AGOTADOS=["MLM2910880717","MLM2910457937","MLM2910457933","MLM2910768379","MLM2910768375"]
for iid in AGOTADOS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
    if g.get("status")=="active":
        r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"})
        print(f"PAUSE {iid} http={r.status_code}")
    else:
        print(f"{iid} already {g.get('status')}")

# CON STOCK (Rojo, Rosa, Celeste, Camuflaje) — ensure active + qty 1
CON_STOCK=["MLM2910806817","MLM2914422351","MLM2910768369","MLM2910768325","MLM2910768335","MLM2910457917","MLM5351937060"]
for iid in CON_STOCK:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
    print(f"{iid} current: st={g.get('status')} qty={g.get('available_quantity')}")
    if g.get("status")!="active":
        r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"active","available_quantity":1})
        print(f"  ACTIVATE http={r.status_code}")

# Retry pause MLM2911241939 that failed earlier
r=requests.put(f"https://api.mercadolibre.com/items/MLM2911241939",headers=H,json={"status":"paused"})
print(f"\nPAUSE MLM2911241939 retry http={r.status_code} {r.text[:200]}")
