import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Try different catalog search endpoints
for url in [
  f"{API}/products/search?q=JBL%20Go%204&status=active&site_id=MLM",
  f"{API}/products/search?q=JBL%20Go%204",
  f"{API}/sites/MLM/search?q=JBL%20Go%204%20Negro&condition=new&limit=10",
  f"{API}/products/search?q=JBL+Go+4&site_id=MLM",
  f"{API}/catalog_listings/search?q=JBL+Go+4&site_id=MLM",
]:
  r=requests.get(url,headers=H,timeout=15)
  print(f"\n--- {url[:80]} ---")
  print(f"  {r.status_code} {r.text[:400]}")
