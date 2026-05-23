import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
for iid in ["MLM5291774150","MLM2950790159"]:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    cur=g.get("price")
    r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":499},timeout=15)
    print(f"  {iid} ${cur}→$499 http={r.status_code} {('' if r.status_code<300 else r.text[:100])}")
    time.sleep(0.3)
