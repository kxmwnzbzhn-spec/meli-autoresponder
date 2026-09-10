import os,json,requests
API="https://api.mercadolibre.com"
IDS=["MLM3457517131","MLM3457517073","MLM3457506141","MLM6178069636","MLM3457506137","MLM3457506149","MLM6178069536"]
rt=os.environ["MELI_REFRESH_TOKEN_ROSA_MARIA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=30)
r.raise_for_status(); tok=r.json()
open("/tmp/rot","w").write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
for iid in IDS:
 g=requests.get(f"{API}/items/{iid}?attributes=id,title,status,sub_status,available_quantity,sold_quantity,initial_quantity",headers=H,timeout=20).json()
 print(json.dumps({"iid":iid,"status":g.get("status"),"sub":g.get("sub_status"),"qty":g.get("available_quantity"),"sold":g.get("sold_quantity"),"initial":g.get("initial_quantity"),"title":g.get("title")[:50]},ensure_ascii=False))
