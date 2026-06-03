"""Try harder revival: separate PUTs, wait, multiple attempts."""
import os, requests, time, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ASVA={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

ITEM="MLM5233454100"
g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"[T0] status={g.get('status')} sub={g.get('sub_status')} qty={g.get('available_quantity')} health={g.get('health')}")
print(f"     deals={g.get('deals')} listing_type={g.get('listing_type_id')} user_product_id={g.get('user_product_id')}")
print(f"     date_created={g.get('date_created')} last_updated={g.get('last_updated')} stop_time={g.get('stop_time')}")

# Try sequence
for attempt in [
    {"status":"active"},
    {"status":"active","sub_status":[]},
    {"status":"paused","sub_status":[]},  # closed→paused first
]:
    print(f"\nAttempt PUT {attempt}")
    rp=requests.put(f"{API}/items/{ITEM}",headers=HJ,json=attempt,timeout=15)
    print(f"  HTTP {rp.status_code}: {rp.text[:500]}")
    time.sleep(3)
    g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
    print(f"  → status={g.get('status')} sub={g.get('sub_status')}")
    if g.get("status")=="active":
        print(f"\n✅ REACTIVATED")
        break

# Try the user_product activation endpoint if all fail
upid=g.get("user_product_id")
if g.get("status")!="active" and upid:
    print(f"\nTry user-products/{upid} status active")
    rp=requests.put(f"{API}/user-products/{upid}",headers=HJ,json={"status":"active"},timeout=15)
    print(f"  HTTP {rp.status_code}: {rp.text[:400]}")
    time.sleep(2)
    g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
    print(f"  → status={g.get('status')} sub={g.get('sub_status')}")
