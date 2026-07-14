import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}"}

# Include 5705924452 as candidate for the truncated "57059244"
ITEMS=["MLM3129625691","MLM3130262123","MLM3129626365","MLM5705924478","MLM5705924474","MLM5705924452"]

for iid in ITEMS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,catalog_product_id,category_id,price,status,sub_status",headers=H,timeout=10).json()
    if g.get("error"):
        print(f"{iid} ERR: {g.get('message','?')[:60]}",flush=True)
        continue
    print(f"{iid} | status={g.get('status')} sub={g.get('sub_status')} | cpid={g.get('catalog_product_id')} | price=${g.get('price')} | {(g.get('title') or '?')[:50]}",flush=True)
