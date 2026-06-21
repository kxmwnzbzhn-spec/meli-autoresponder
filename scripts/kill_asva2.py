import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Probe known/suspected category IDs
CANDIDATES=["MLM3937","MLM179232","MLM179230","MLM5286","MLM1499","MLM1500","MLM1574","MLM2553","MLM2563","MLM45353","MLM423275","MLM5113"]
for c in CANDIDATES:
  try:
    r=requests.get(f"{API}/categories/{c}",headers=H,timeout=10).json()
    if r.get("name"):
      path=" > ".join(p.get("name") for p in r.get("path_from_root",[]))
      print(f"  {c}: {path}")
  except: pass

# Walk MLM1474 (Salud y Belleza?)
print("\n=== Walking ESO type cats ===")
# Try search via items endpoint (categories of items in similar listings)
# Actually let me just check by exploring deeper

# Try /domains/MLM-PERFUMES_BODY_SPLASH
for dom in ["MLM-PERFUMES_BODY_SPLASH","MLM-ESOTERIC_PERFUMES","MLM-PERFUMES_AMBIENT","MLM-PERFUMES","MLM-ESOTERIC","MLM-RITUAL_PRODUCTS"]:
  rd=requests.get(f"{API}/domains/{dom}",headers=H,timeout=10)
  print(f"\n/domains/{dom}: {rd.status_code} {rd.text[:300]}")

# Try one ASVA item that might be in esoteric cat
print("\n=== Other ASVA items category check ===")
# Search Mayrely/Asva for similar
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me.get("id")
si=requests.get(f"{API}/users/{uid}/items/search?q=esoterico&limit=10",headers=H,timeout=15)
print(f"search esoterico in ASVA items: {si.status_code}")
if si.status_code==200:
  ids=si.json().get("results",[])
  for i in ids[:5]:
    g=requests.get(f"{API}/items/{i}?attributes=id,title,category_id",headers=H,timeout=10).json()
    print(f"  {g.get('id')} cat={g.get('category_id')} - {(g.get('title') or '')[:60]}")
