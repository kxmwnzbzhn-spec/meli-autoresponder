import os,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
FIX={"MLM2909183147":543,"MLM5353056250":445,"MLM2940673601":973}
for iid,target in FIX.items():
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"price":target},timeout=15)
    print(f"  {iid} → ${target} http={r.status_code}")
    time.sleep(0.5)
