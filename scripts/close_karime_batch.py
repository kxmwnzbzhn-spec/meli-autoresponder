import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

for iid in ["MLM3129626365","MLM5705924478"]:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status,sub_status,last_updated",headers=H,timeout=10).json()
    st=g.get("status"); last=g.get("last_updated")
    print(f"\n{iid} status={st} sub={g.get('sub_status')} last_upd={last}",flush=True)
    if st=="active":
        pr=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=10).json()
        print(f"  FORCE PAUSED: {pr.get('status')} err={pr.get('message','')}",flush=True)
    else:
        print(f"  already {st}",flush=True)
    time.sleep(0.5)

# Verify final
print(f"\n=== VERIFY FINAL ===",flush=True)
for iid in ["MLM3129626365","MLM5705924478"]:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status",headers=H,timeout=10).json()
    print(f"  {iid}: {g.get('status')}",flush=True)
