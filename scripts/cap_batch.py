import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
TOPS={"MLM2950800589":1999,"MLM2950827331":1999,"MLM5353156204":2499}
for iid,tope in TOPS.items():
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    cur=g.get("price")
    if cur is None: print(f"  {iid}: {g.get('status')}"); continue
    if cur>tope:
        r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":tope},timeout=15)
        print(f"  {iid} ${cur}→${tope} http={r.status_code}")
    else:
        print(f"  {iid} cur=${cur} <= ${tope}, sin cambio")
    time.sleep(0.3)
