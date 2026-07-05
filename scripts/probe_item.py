import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}"}

for iid in ["MLM3059219021"]:
    print(f"\n--- {iid} ---",flush=True)
    for url in [
        f"https://api.mercadolibre.com/items/{iid}",
        f"https://api.mercadolibre.com/items?ids={iid}",
        f"https://api.mercadolibre.com/products/{iid}",
    ]:
        r=requests.get(url,headers=H,timeout=10)
        print(f"  {url}: {r.status_code} {r.text[:250]}",flush=True)
