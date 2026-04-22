import os,requests,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
IDS=["MLM2880754185","MLM2880758743","MLM2880865907","MLM2880898001"]
for iid in IDS:
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    old=it.get("price")
    st=it.get("status"); ss=it.get("sub_status")
    rr=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":899},timeout=20)
    print(f"{iid} [{st}/{ss}] ${old} -> $899 | {rr.status_code} {rr.text[:100] if rr.status_code>=400 else ''}")
    time.sleep(0.5)
