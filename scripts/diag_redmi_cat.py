import os,requests,urllib.parse
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json().get("access_token")
H={"Authorization":f"Bearer {T}"}

# Get catalog product details — incluye category_id
p=requests.get("https://api.mercadolibre.com/products/MLM40336571",headers=H).json()
print("category_id (from product):",p.get("category_id"))
print("domain:",p.get("domain_id"))
print("children of MLM1276:")
c=requests.get("https://api.mercadolibre.com/categories/MLM1276").json()
for ch in c.get("children_categories",[])[:20]:
    print(f"  {ch.get('id')} - {ch.get('name')}")

# Category predictor
q=urllib.parse.quote("Auriculares Xiaomi Redmi Buds 4 Lite Bluetooth 5.3 In Ear Negro")
pred=requests.get(f"https://api.mercadolibre.com/sites/MLM/domain_discovery/search?limit=5&q={q}").json()
print("\nDomain discovery:")
for x in pred[:5]: print(f"  {x.get('category_id')} {x.get('domain_id')} - {x.get('category_name','')}")
