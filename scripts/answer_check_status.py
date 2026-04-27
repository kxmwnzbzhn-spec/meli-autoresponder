"""Check status de items con Qs fallidas en ASVA."""
import os, requests
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}

CLARIBEL_RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
r2=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":CLARIBEL_RT}).json()
H2={"Authorization":f"Bearer {r2['access_token']}"}

ASVA_ITEMS = ["MLM3849902442","MLM4320509906","MLM2605081655","MLM2534736037","MLM4299103248","MLM4299195226"]
CLARIBEL_ITEMS = ["MLM5245716860"]

print("=== ASVA ===")
for iid in ASVA_ITEMS:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status,sub_status,title",headers=H,timeout=10).json()
    print(f"  {iid} status={g.get('status')} sub_status={g.get('sub_status')} title='{(g.get('title','') or '')[:60]}'")

print("\n=== CLARIBEL ===")
for iid in CLARIBEL_ITEMS:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status,sub_status,title",headers=H2,timeout=10).json()
    print(f"  {iid} status={g.get('status')} sub_status={g.get('sub_status')} title='{(g.get('title','') or '')[:60]}'")
