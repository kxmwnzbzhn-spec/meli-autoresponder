import os,json,requests
API="https://api.mercadolibre.com"
IDS=["MLM3457506231","MLM3457506229","MLM3457506223","MLM3457517095","MLM3457517089"]
rt=os.environ["MELI_REFRESH_TOKEN_ROSA_MARIA"]
tok=None
for app_e,sec_e in [("MELI_APP_ID","MELI_APP_SECRET"),("MELI_APP_ID_NEW","MELI_APP_SECRET_NEW")]:
 app=os.environ.get(app_e); sec=os.environ.get(sec_e)
 if not app or not sec: continue
 r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":app,"client_secret":sec,"refresh_token":rt},timeout=30)
 if r.status_code==200:
  tok=r.json(); print(f"[auth] OK con {app_e}"); break
if not tok: raise SystemExit("no auth")
open("/tmp/rot","w").write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=20).json()
print(f"[me] uid={me.get('id')} nick={me.get('nickname')}")
for iid in IDS:
 g=requests.get(f"{API}/items/{iid}?attributes=id,title,status,sub_status,available_quantity",headers=H,timeout=20).json()
 print(json.dumps({"iid":iid,**g},ensure_ascii=False))
 # Re-PUT paused + verify
 p=requests.put(f"{API}/items/{iid}",headers={**H,"Content-Type":"application/json"},json={"status":"paused"},timeout=30)
 v=requests.get(f"{API}/items/{iid}?attributes=id,status,sub_status",headers=H,timeout=20).json()
 print(f"[repaused] {iid} put={p.status_code} err={p.text[:200] if p.status_code>=300 else ''} after={v}")
