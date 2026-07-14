import os, requests
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}"}
for iid in ["MLM3129625691","MLM3130262123","MLM3129626365","MLM5705924478","MLM5705924474","MLM5705924452","MLM3129625715"]:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,price,status,title",headers=H,timeout=10).json()
    print(f"  {iid} ${g.get('price')} {g.get('status')} | {(g.get('title') or '?')[:50]}",flush=True)
