import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Single item check
for iid in ["MLM5557390784","MLM2982368123"]:
  r=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
  print(f"\n=== {iid} ===")
  for k in ("id","status","title","price","sold_quantity","available_quantity","initial_quantity"):
    print(f"  {k}: {r.get(k)}")

# Try /reviews/item/{cpid} for a catalog product as a sales proxy
print("\n=== /reviews/item/MLM44715070 ===")
rv=requests.get(f"{API}/reviews/item/MLM44715070",headers=H,timeout=10)
print(f"  HTTP {rv.status_code}: {rv.text[:400]}")

# Try MELI product visit info
print("\n=== /visits/items?ids=MLM5557390784 ===")
v=requests.get(f"{API}/visits/items?ids=MLM5557390784",headers=H,timeout=10)
print(f"  HTTP {v.status_code}: {v.text[:300]}")

# Try public HTML scrape for sales
print("\n=== HTML scrape ===")
url="https://www.mercadolibre.com.mx/p/MLM44715070"
h=requests.get(url,headers={"User-Agent":"Mozilla/5.0 (Mac)"},timeout=15)
print(f"  HTTP {h.status_code} bytes={len(h.text)}")
# search for "vendido" text
import re
m=re.findall(r"(\d+(?:,\d{3})*(?:\.\d+)?[+ ]*vendid\w+)",h.text,re.I)
print(f"  matches: {m[:20]}")
