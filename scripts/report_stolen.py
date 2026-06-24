import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

cp=requests.get(f"{API}/products/MLM44710240",headers=HJ,timeout=15).json()
cat=cp.get("category_id")
fname=cp.get("family_name") or cp.get("name") or "Bocina JBL Go 4 Negra"
print(f"CPID cat: {cat} family: {fname}")

# Look at parent_id and get its category
print("parent_id:",cp.get("parent_id"))
print("children_ids:",cp.get("children_ids"))

# Find a leaf category from MLM-SPEAKERS / portable speakers
# Use predict category endpoint
pred=requests.get(f"{API}/sites/MLM/category_predictor/predict?title=Bocina%20JBL%20Go%204%20portatil%20bluetooth%20waterproof%20negra",headers=HJ,timeout=15)
print(f"predict: {pred.status_code} {pred.text[:400]}")

# Also fetch typical Go 4 category via existing item search
sr=requests.get(f"{API}/sites/MLM/search?q=JBL%20Go%204%20Negro&condition=new&limit=5",headers=HJ,timeout=15)
if sr.status_code==200:
  for res in sr.json().get("results",[])[:5]:
    print(f"  item cat: {res.get('category_id')} title: {res.get('title')[:50]}")
