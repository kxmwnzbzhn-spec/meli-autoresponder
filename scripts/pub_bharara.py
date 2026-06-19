import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM3031473511"

# Try products/search for all Armaf Iconic candidates
pr=requests.get(f"{API}/products/search?status=active&site_id=MLM&q=Armaf+Iconic",headers=H,timeout=15).json()
print(f"products found: {len(pr.get('results',[]))}")
pic_urls=[]
for r2 in pr.get("results",[])[:8]:
  pid=r2.get("id")
  cp=requests.get(f"{API}/products/{pid}",headers=H,timeout=10).json()
  print(f"  {pid} {cp.get('name','')[:60]} pics={len(cp.get('pictures',[]))}")
  for p in cp.get("pictures",[])[:6]:
    u=p.get("url")
    if u and u not in pic_urls: pic_urls.append(u)

# Also try search Armaf Club de Nuit
pr2=requests.get(f"{API}/products/search?status=active&site_id=MLM&q=Armaf+Club+Nuit",headers=H,timeout=15).json()
for r2 in pr2.get("results",[])[:5]:
  pid=r2.get("id")
  cp=requests.get(f"{API}/products/{pid}",headers=H,timeout=10).json()
  if "iconic" in (cp.get("name","").lower()):
    for p in cp.get("pictures",[])[:6]:
      u=p.get("url")
      if u and u not in pic_urls: pic_urls.append(u)

print(f"\ntotal unique pic urls: {len(pic_urls)}")

# Get current pics on item
g=requests.get(f"{API}/items/{IID}?attributes=pictures",headers=H,timeout=15).json()
current_ids=[p.get("id") for p in g.get("pictures",[])]
print(f"current pics on item: {len(current_ids)}")

# Upload new pics, append to current
new_pics=list(current_ids)
for url in pic_urls[:8]:
  if len(new_pics)>=8: break
  try:
    rr=requests.get(url.replace("-O.jpg","-F.jpg"),timeout=30)
    if rr.status_code!=200 or len(rr.content)<10000:
      rr=requests.get(url,timeout=30)
    if rr.status_code==200 and len(rr.content)>10000:
      up=requests.post(f"{API}/pictures/items/upload",
        headers={"Authorization":f"Bearer {AT}"},
        files={"file":(f"armaf_{len(new_pics)}.jpg",rr.content,"image/jpeg")},timeout=60)
      if up.status_code in (200,201):
        pid=up.json().get("id")
        if pid and pid not in new_pics:
          new_pics.append(pid); print(f"  + {pid}")
  except Exception as e: print(f"err: {e}")

print(f"\nfinal pics to set: {len(new_pics)}")
p=requests.put(f"{API}/items/{IID}",headers=HJ,json={"pictures":[{"id":x} for x in new_pics]},timeout=30)
print(f"PUT pics: {p.status_code} {p.text[:300]}")
