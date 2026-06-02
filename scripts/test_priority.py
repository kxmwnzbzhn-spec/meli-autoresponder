"""Verification: set qty=0 on MLM3849137034, then wait 70s, then check qty.
Expect: priority bot should force qty back to 1 within one tick (~30s).
"""
import os, requests, time
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ASVA={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
ITEM="MLM3849137034"

g0=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"[T0] qty={g0.get('available_quantity')} status={g0.get('status')}")

# Set qty to 0 (simulate sale)
r0=requests.put(f"{API}/items/{ITEM}",headers=HJ,json={"available_quantity":0,"status":"paused"},timeout=15)
print(f"[SET 0] HTTP {r0.status_code}")

# Poll every 10s for 90s
for i in range(10):
    time.sleep(10)
    g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
    print(f"[+{(i+1)*10}s] qty={g.get('available_quantity')} status={g.get('status')} sub={g.get('sub_status')}")
    if g.get("status")=="active" and (g.get("available_quantity") or 0)>=1:
        print(f"\n✅ PRIORITY BOT WORKING: revived at t+{(i+1)*10}s")
        break
else:
    print(f"\n❌ NOT REVIVED in 90s — bot priority section not effective")
