import os, json, time, requests
API="https://api.mercadolibre.com"
TARGETS=[("MLM6164209204",699),("MLM6164209208",699),("MLM6164209186",699),("MLM6164171572",449)]
r=requests.post(f"{API}/oauth/token",data={
 "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
 "client_secret":os.environ["MELI_APP_SECRET"],
 "refresh_token":os.environ["MELI_REFRESH_TOKEN_DIDER"],
},timeout=30)
r.raise_for_status(); tok=r.json()
with open("/tmp/dider_rot","w") as f: f.write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}

# 1) Apps autorizadas
apps=requests.get(f"{API}/users/me/applications",headers=H,timeout=20)
print("[apps]",apps.status_code, apps.text[:600])

# 2) Promociones activas del seller
promo=requests.get(f"{API}/seller-promotions/users/3654003391",headers=H,timeout=20)
print("[promo]",promo.status_code, promo.text[:400])

# 3) Re-PUT y observar 3 min
print("\n=== RE-PUT + WATCH ===")
for iid,tp in TARGETS:
 p=requests.put(f"{API}/items/{iid}",headers={**H,"Content-Type":"application/json"},json={"price":tp},timeout=30)
 print(f"[PUT {iid}] {p.status_code}")

for delay in [10,30,60,120,180,240]:
 time.sleep(delay if delay<=60 else 60)
 real_delay = delay
 print(f"\n--- t≈{delay}s ---")
 for iid,tp in TARGETS:
  vp=requests.get(f"{API}/items/{iid}/prices",headers=H,timeout=20).json()
  pr=vp["prices"][0]
  print(f"{iid} amount={pr['amount']} last_updated={pr['last_updated']}")
