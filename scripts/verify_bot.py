"""Verify bot priority reactivation on the 3 Alchemia items."""
import os, requests, time
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ASVA={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

ITEMS=["MLM2967805809","MLM3849137034","MLM2378087893"]

# Set them all to qty=0 paused (simulate full sale)
print("\n=== SET qty=0 + paused (simulate sale) ===")
for iid in ITEMS:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    print(f"[T0] {iid} qty={g.get('available_quantity')} status={g.get('status')}")
    r1=requests.put(f"{API}/items/{iid}",headers=HJ,json={"available_quantity":0,"status":"paused"},timeout=15)
    print(f"  SET 0 paused → HTTP {r1.status_code}")

# Poll every 10s up to 90s
for tick in range(9):
    time.sleep(10)
    print(f"\n[t+{(tick+1)*10}s]")
    all_revived=True
    for iid in ITEMS:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        qty=g.get("available_quantity"); st=g.get("status")
        revived=(st=="active" and (qty or 0)>=1)
        status="✅" if revived else "❌"
        print(f"  {status} {iid} qty={qty} status={st}")
        if not revived: all_revived=False
    if all_revived:
        print(f"\n🎯 BOT FUNCIONA — los 3 reactivados en t+{(tick+1)*10}s")
        break
else:
    print(f"\n💥 BOT NO REACTIVÓ en 90s — investigar")
