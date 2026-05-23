import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
NINE=["MLM5363034838","MLM2940662359","MLM5364336572","MLM2950790167","MLM2950790175",
"MLM2950801625","MLM2950801633","MLM2950827383","MLM2950827387"]
for iid in NINE:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    cur=g.get("price")
    if cur is None: print(f"  {iid}: {g.get('status')}"); continue
    if cur>799:
        r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":799},timeout=15)
        print(f"  {iid} ${cur}→$799 http={r.status_code}")
    else:
        print(f"  {iid} cur=${cur} <= $799, sin cambio")
    time.sleep(0.3)
