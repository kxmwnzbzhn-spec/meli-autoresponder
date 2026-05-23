import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
TOPS={"MLM5364336572":899,"MLM2950790151":449,"MLM2950801593":1999}
for iid,tope in TOPS.items():
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    cur=g.get("price")
    if cur is None:
        print(f"  {iid}: no existe/{g.get('status')}"); continue
    if cur>tope:
        r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":tope},timeout=15)
        print(f"  {iid} ${cur}→${tope} (cap) http={r.status_code}")
    else:
        print(f"  {iid} cur=${cur} <= tope ${tope}, sin cambio")
    time.sleep(0.3)
