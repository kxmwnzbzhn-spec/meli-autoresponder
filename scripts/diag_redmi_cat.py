import os,requests
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json().get("access_token")
H={"Authorization":f"Bearer {T}"}

# Method 1: get product details with full info
p=requests.get("https://api.mercadolibre.com/products/MLM40336571?include_attributes=all",headers=H).json()
print("keys:",list(p.keys())[:30])
print("category_id:",p.get("category_id"))
print("settings.category:",p.get("settings",{}).get("category"))
# Search for other listings of this same CPID to see their category
r=requests.get("https://api.mercadolibre.com/products/MLM40336571/items?limit=3",headers=H).json()
for it in r.get("results",[])[:3]:
    print(f"  listing {it.get('id')} cat={it.get('category_id')}")

# Method 2: category predictor
import urllib.parse
q=urllib.parse.quote("Auriculares Xiaomi Redmi Buds 4 Lite Bluetooth 5.3 In Ear Negro")
pred=requests.get(f"https://api.mercadolibre.com/sites/MLM/category_predictor/predict?title={q}").json()
print("\npredictor:",pred)
