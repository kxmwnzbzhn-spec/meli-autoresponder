import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

for IID in ["MLM5705924452","MLM5705934160"]:
    print(f"\n=== {IID} ===",flush=True)
    g=requests.get(f"https://api.mercadolibre.com/items/{IID}?attributes=id,status,sub_status,title",headers=H,timeout=10).json()
    st=g.get("status")
    sub=g.get("sub_status")
    print(f"  before: status={st} sub={sub} title={g.get('title','?')[:60]}",flush=True)
    
    # Try to pause first (works on under_review)
    pr=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"status":"paused"},timeout=10).json()
    print(f"  paused: status={pr.get('status')} err={pr.get('message','')}",flush=True)
    
    time.sleep(1)
    # Try to close
    cr=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"status":"closed"},timeout=10).json()
    print(f"  closed: status={cr.get('status')} err={cr.get('message','')}",flush=True)
    
    # If still can't close (under_review), at least ensure it's paused
    g2=requests.get(f"https://api.mercadolibre.com/items/{IID}?attributes=id,status",headers=H,timeout=10).json()
    print(f"  FINAL: status={g2.get('status')}",flush=True)
