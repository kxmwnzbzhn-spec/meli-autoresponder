import os, requests
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}

ITEMS=["MLM2967318097","MLM2967318191","MLM2967317601","MLM2967305251","MLM2967317613","MLM2967292003",
       "MLM2967292013","MLM2967279337","MLM2967292049","MLM2967292015"]

for iid in ITEMS:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
    sku=g.get("seller_custom_field")
    cpid=g.get("catalog_product_id")
    last_mod=g.get("last_updated")
    print(f"{iid} | status={g.get('status')} sub={g.get('sub_status')} | price=${g.get('price')} | sku={sku} cpid={cpid} | last_upd={last_mod}")
