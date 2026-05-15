import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

# 1. Check MLM5351937060 (Go4 Camuflaje catalog clone)
print("=== MLM5351937060 (Camuflaje clone) ===")
g=requests.get(f"https://api.mercadolibre.com/items/MLM5351937060",headers=H).json()
print(f"  st={g.get('status')} sub={g.get('sub_status')} price=${g.get('price')} cpid={g.get('catalog_product_id')}")
print(f"  title={g.get('title','')[:65]}")
print(f"  cat_listing={g.get('catalog_listing')} permalink={g.get('permalink')}")
p=requests.get(f"https://api.mercadolibre.com/items/MLM5351937060/price_to_win?version=v2",headers=H).json()
print(f"  PTW={p.get('price_to_win')} cat_status={p.get('status')}")

# 2. Reacondicionadas: 10 negras, 10 rojas, 10 camuflaje
print("\n=== Reacondicionadas ===")
REAC={"MLM2911241921":"Negro","MLM2911205487":"Camuflaje","MLM2911241939":"Rojo"}
for iid,color in REAC.items():
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
    print(f"{iid} {color}: st={g.get('status')} sub={g.get('sub_status')} qty={g.get('available_quantity')}")
    if g.get("status") in ("paused","closed"):
        r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"active","available_quantity":1})
        print(f"  ACTIVATE http={r.status_code} {r.text[:200]}")
    elif g.get("status")=="under_review":
        print(f"  ⚠️ UNDER_REVIEW, no se puede modificar")
