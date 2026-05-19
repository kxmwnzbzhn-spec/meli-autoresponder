import os, requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
# Restaurar a $542
r=requests.put(f"{API}/items/MLM2916942827",headers=H,json={"price":542},timeout=15)
print(f"MLM2916942827 → $542 http={r.status_code}")
# Verificar ptw
H2={"Authorization":f"Bearer {T}"}
import time; time.sleep(1)
p=requests.get(f"{API}/items/MLM2916942827/price_to_win?version=v2",headers=H2,timeout=10).json()
print(f"PTW post: status={p.get('status')} price_to_win={p.get('price_to_win')}")
