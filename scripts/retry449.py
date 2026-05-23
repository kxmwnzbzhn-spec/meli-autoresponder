import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
for attempt in range(3):
    g=requests.get(f"{API}/items/MLM2950790151",headers=H,timeout=10).json()
    cur=g.get("price")
    if cur<=449:
        print(f"MLM2950790151 cur=${cur} ok"); break
    r=requests.put(f"{API}/items/MLM2950790151",headers=HJ,json={"price":449},timeout=15)
    print(f"  intento {attempt+1}: ${cur}→$449 http={r.status_code}")
    if r.status_code<300: break
    time.sleep(2)
