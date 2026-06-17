import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Try multiple variations and dump full response
for q in ["calcetines","tobilleras","medias hombre","socks tommy"]:
  s=requests.get(f"{API}/sites/MLM/search?q={requests.utils.quote(q)}&limit=20",headers=H,timeout=15)
  print(f"\nQ:'{q}' status={s.status_code}")
  if s.status_code==200:
    j=s.json()
    print(f"  total={j.get('paging',{}).get('total')}")
    results=j.get("results",[])
    print(f"  result count={len(results)}")
    cats={}
    for r2 in results:
      c=r2.get("category_id")
      if c: cats[c]=cats.get(c,0)+1
    for c,n in sorted(cats.items(),key=lambda x:-x[1])[:5]:
      cn=requests.get(f"{API}/categories/{c}",headers=H,timeout=10).json().get("name","?")
      print(f"  {c}: n={n} '{cn}'")

# Try /sites/MLM/categories tree
tree=requests.get(f"{API}/sites/MLM/categories",headers=H,timeout=15).json()
print(f"\n=== top MLM cats ===")
for t in tree[:15]: print(f"  {t['id']} - {t['name']}")
