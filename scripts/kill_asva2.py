import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Full top tree
tree=requests.get(f"{API}/sites/MLM/categories",headers=H,timeout=15).json()
print(f"top cats: {len(tree)}")
for t in tree:
  print(f"  {t['id']} - {t['name']}")
  # Find Otras categorías or Esoterismo
  if "otra" in t['name'].lower() or "esot" in t['name'].lower():
    print(f"    → DRILLING")
    ci=requests.get(f"{API}/categories/{t['id']}",headers=H,timeout=10).json()
    for ch in ci.get("children_categories",[]):
      print(f"    {ch['id']} - {ch['name']}")
      if "esot" in ch['name'].lower():
        # Drill more
        ci2=requests.get(f"{API}/categories/{ch['id']}",headers=H,timeout=10).json()
        for ch2 in ci2.get("children_categories",[]):
          print(f"      {ch2['id']} - {ch2['name']}")
          if "perfu" in ch2['name'].lower():
            print(f"        ★★★ LEAF? {ch2['id']}")
