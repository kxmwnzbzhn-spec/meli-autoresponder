import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_LIGIA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_LIGIA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

for iid in ["MLM3152563611","MLM5745385304"]:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status,sub_status,available_quantity,last_updated",headers=H,timeout=10).json()
    print(f"\n{iid} status={g.get('status')} qty={g.get('available_quantity')} sub={g.get('sub_status')} last_upd={g.get('last_updated')}",flush=True)
    
    # Force pause NOW regardless of current state
    if g.get("status")=="active":
        pr=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=15).json()
        print(f"  FORCE PAUSED: status={pr.get('status')} err={pr.get('message','')}",flush=True)
    else:
        print(f"  ya está {g.get('status')}, no PUT",flush=True)
    time.sleep(1)
