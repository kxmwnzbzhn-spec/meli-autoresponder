import os,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
ids=[]; off=0
while True:
    r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=active&limit=100&offset={off}",headers=H).json()
    res=r.get("results",[])
    if not res: break
    ids+=res; off+=100
    if off>=r.get("paging",{}).get("total",0): break
print(f"PAUSANDO {len(ids)} items active Yiriam")
ok=0
for iid in ids:
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15)
    if r.status_code<300: ok+=1
    else: print(f"  ✗ {iid} http={r.status_code}")
print(f"✓ PAUSADAS {ok}/{len(ids)}")
