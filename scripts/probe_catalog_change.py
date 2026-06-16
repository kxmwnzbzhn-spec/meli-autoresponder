import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
tk=r.json(); AT=tk["access_token"]
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
CPID="MLM48919985"

# Probe several endpoints
ENDPOINTS=[
  ("GET",f"{API}/products/{CPID}",None),
  ("POST",f"{API}/products/{CPID}/suggestions",{}),
  ("POST",f"{API}/products/{CPID}/proposals",{}),
  ("POST",f"{API}/products/{CPID}/edition_proposals",{}),
  ("POST",f"{API}/catalog/products/{CPID}/changes",{}),
  ("POST",f"{API}/catalog/products/{CPID}/improvements",{}),
  ("POST",f"{API}/catalog_quality/items/{CPID}/improvements",{}),
  ("POST",f"{API}/catalog/improvements",{"product_id":CPID,"changes":[]}),
  ("GET",f"{API}/catalog/products/{CPID}/improvements",None),
  ("GET",f"{API}/products/{CPID}/improvements",None),
  ("GET",f"{API}/products/{CPID}/proposals",None),
  ("GET",f"{API}/products/{CPID}/edition_proposals",None),
]
for method,url,body in ENDPOINTS:
  try:
    if method=="GET":
      r=requests.get(url,headers=H,timeout=10)
    else:
      r=requests.post(url,headers=H,json=body,timeout=10)
    print(f"{method} {url[40:]} -> {r.status_code}: {r.text[:200]}")
  except Exception as e:
    print(f"{method} {url[40:]} -> ERR {e}")
