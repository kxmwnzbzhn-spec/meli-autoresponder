import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
IDS=["MLM2958333247","MLM2958320639","MLM2958320635"]
for sid in IDS:
    g=requests.get(f"{API}/items/{sid}",headers=H,timeout=30).json()
    print(f"\n=== {sid} === BEFORE: status={g.get('status')} title='{(g.get('title') or '')[:60]}'")
    if g.get("status")=="active":
        rp=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"paused"},timeout=30)
        print(f"  pause: {rp.status_code}")
        time.sleep(1)
    # close
    rc=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"closed"},timeout=30)
    print(f"  close: {rc.status_code} {rc.text[:200] if rc.status_code>=400 else 'OK'}")
    time.sleep(1)
    # mark deleted (soft delete)
    rd=requests.put(f"{API}/items/{sid}",headers=HJ,json={"deleted":"true"},timeout=30)
    print(f"  delete: {rd.status_code} {rd.text[:200] if rd.status_code>=400 else 'OK'}")
    time.sleep(1)
    g2=requests.get(f"{API}/items/{sid}",headers=H,timeout=30).json()
    print(f"  AFTER: status={g2.get('status')} deleted={g2.get('deleted')}")
