import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
SID=me.get("id")
print(f"ASVA user_id: {SID}")

# Try multiple endpoints + formats
for ORD in ["2000013543063645","2000013543121015"]:
  print(f"\n=== {ORD} ===")
  for ep,label in [
    (f"/orders/{ORD}","GET /orders/{}"),
    (f"/orders/{ORD}?include=archived","with archived"),
    (f"/packs/{ORD}","/packs/{}"),
    (f"/shipments/{ORD}","/shipments/{}"),
    (f"/marketplace/orders/{ORD}","/marketplace/orders/{}"),
    (f"/post-purchase/v1/orders/{ORD}","/post-purchase/v1/orders/{}"),
    (f"/orders/search?seller={SID}&q={ORD}","search by seller+q"),
  ]:
    try:
      r=requests.get(f"{API}{ep}",headers=H,timeout=12)
      if r.status_code<400:
        body=r.text[:500]
        print(f"  ✓ {label}: {r.status_code}")
        print(f"    {body}")
      else:
        print(f"  {label}: {r.status_code}")
    except Exception as e: print(f"  {label}: err {e}")

# Search orders by date around when these might have been
print("\n=== Search orders ASVA latest 50 ===")
sr=requests.get(f"{API}/orders/search?seller={SID}&sort=date_desc&limit=50",headers=H,timeout=15)
print(f"search: {sr.status_code}")
if sr.status_code==200:
  for o in sr.json().get("results",[])[:5]:
    print(f"  {o.get('id')} {o.get('date_created')} ${o.get('total_amount')} {o.get('status')}")

# Try /orders/search?seller={SID}&order.id={ORD}
for ORD in ["2000013543063645","2000013543121015"]:
  sr=requests.get(f"{API}/orders/search?seller={SID}&order.id={ORD}",headers=H,timeout=15)
  print(f"\nsearch order.id={ORD}: {sr.status_code}")
  if sr.status_code==200:
    res=sr.json().get("results",[])
    print(f"  found: {len(res)}")
