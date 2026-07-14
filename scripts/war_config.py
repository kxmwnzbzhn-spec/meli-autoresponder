import os, requests
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}"}
g=requests.get("https://api.mercadolibre.com/items/MLM3129625715?attributes=id,title,catalog_product_id,category_id,price,status",headers=H,timeout=10).json()
print(f"MLM3129625715 | status={g.get('status')} | cpid={g.get('catalog_product_id')} | price=${g.get('price')} | {(g.get('title') or '?')[:60]}",flush=True)
