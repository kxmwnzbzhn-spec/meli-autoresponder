import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

def refresh(k):
    RT=os.environ[k]
    r=requests.post("https://api.mercadolibre.com/oauth/token",
      data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
    return r["access_token"], r["refresh_token"]

AT_K, RT_K = refresh("MELI_REFRESH_TOKEN_KARIME")
AT_L, RT_L = refresh("MELI_REFRESH_TOKEN_LIGIA")
print(f"NEW_RT_KARIME: {RT_K}",flush=True)
print(f"NEW_RT_LIGIA: {RT_L}",flush=True)

for iid, acct, AT in [("MLM5667423614","KARIME",AT_K),("MLM5666904468","LIGIA",AT_L)]:
    H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status,available_quantity,title",headers=H,timeout=10).json()
    before=g.get("status")
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=10).json()
    after=r.get("status")
    err=r.get("error","")
    print(f"{acct} {iid} {before} -> {after} err={err}",flush=True)
