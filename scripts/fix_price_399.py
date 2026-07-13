import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

ITEMS=[
  ("MLM3129467021","Negra"),
  ("MLM3129476473","Rosa"),
  ("MLM3129467131","Roja"),
  ("MLM3129476561","Celeste"),
]

for iid, cname in ITEMS:
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":399},timeout=15).json()
    if r.get("error"):
        print(f"  {iid} ({cname}) err: {r.get('message','?')}",flush=True)
    else:
        print(f"  {iid} ({cname}) price -> ${r.get('price')}",flush=True)
