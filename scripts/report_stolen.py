import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# 1) First probe - search catalog products for JBL Go 4
# Endpoint: /products/search
queries=["JBL Go 4 Negro","JBL Go 4 Negra","JBL Go 4 Celeste","JBL Go 4 Rosa","JBL Go 4 Camuflaje","JBL Go 4 Verde","Bocina JBL Go 4"]
all_cpids={}
for q in queries:
  url=f"{API}/products/search?status=active&site_id=MLM&q={q.replace(' ','%20')}&domain_id=MLM-PORTABLE_SPEAKERS"
  r=requests.get(url,headers=H,timeout=15)
  if r.status_code!=200:
    print(f"  ERR {q}: {r.status_code} {r.text[:150]}")
    continue
  d=r.json()
  results=d.get("results",[])
  print(f"\n=== {q}: {len(results)} ===")
  for it in results[:30]:
    cpid=it.get("id")
    if cpid in all_cpids: continue
    name=it.get("name","")
    # Get full details to get sold_quantity
    p=requests.get(f"{API}/products/{cpid}",headers=H,timeout=12).json()
    sold=None
    # check various places
    bbw=p.get("buy_box_winner") or {}
    sold=p.get("sold_quantity") or bbw.get("sold_quantity")
    # color
    color=None
    for a in (p.get("attributes") or []):
      if a.get("id") in ("COLOR","MAIN_COLOR"):
        color=a.get("value_name"); break
    all_cpids[cpid]={"name":name,"color":color,"sold":sold}
    print(f"  {cpid} | color={color} | sold={sold} | {name[:60]}")

print(f"\n\nTotal CPIDs unicos: {len(all_cpids)}")
