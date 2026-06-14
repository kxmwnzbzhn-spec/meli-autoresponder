import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED RT CLB] {NEW_RT}")
H={"Authorization":f"Bearer {AT}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
UID=me["id"]; print(f"seller={UID}")

# Search all charts for this seller
for url in [
  f"{API}/catalog/charts/search?category_id=MLM194115&seller_id={UID}",
  f"{API}/users/{UID}/items/search?category=MLM194115&status=active&limit=5",
]:
  print(f"\n=== {url} ===")
  r=requests.get(url,headers=H,timeout=15)
  print(f"HTTP {r.status_code}")
  print(r.text[:1500])

# For each existing item, get SIZE_GRID_ID
ms=requests.get(f"{API}/users/{UID}/items/search?category=MLM194115&limit=20",headers=H,timeout=15)
if ms.status_code==200:
  ids=ms.json().get("results",[])
  print(f"\nClaribel has {len(ids)} items in MLM194115:")
  for iid in ids[:5]:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    grid=None
    for a in g.get("attributes",[]):
      if a.get("id")=="SIZE_GRID_ID":
        grid=a.get("value_name"); break
    print(f"  {iid} | grid={grid} | {g.get('title','')[:60]}")

# Try MELI's universal size charts endpoint
r2=requests.get(f"{API}/catalog/charts/search?domain_id=MLM-UNDERWEAR&site_id=MLM",headers=H,timeout=15)
print(f"\nUniversal charts: HTTP {r2.status_code}")
print(r2.text[:1500])
print(f"\nFINAL_ROTATED_TOKENS={json.dumps({'MELI_REFRESH_TOKEN_CLARIBEL':NEW_RT})}")
