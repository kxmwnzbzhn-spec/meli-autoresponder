import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

for q in ["calcetines tommy hilfiger hombre","calcetines hombre pack","tobilleras hombre"]:
  s=requests.get(f"{API}/sites/MLM/search?q={requests.utils.quote(q)}&limit=10",headers=H,timeout=15).json()
  cats={}
  for r2 in s.get("results",[])[:10]:
    c=r2.get("category_id")
    if c: cats[c]=cats.get(c,0)+1
  print(f"\nQ: {q}")
  for c,n in sorted(cats.items(),key=lambda x:-x[1])[:5]:
    cn=requests.get(f"{API}/categories/{c}",headers=H,timeout=10).json().get("name","?")
    print(f"  {c}: n={n} '{cn}'")
