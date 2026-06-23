import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

cpid="MLM52129273"
p=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15).json()
print("=== CPID ===")
print("name:",p.get("name"))
print("status:",p.get("status"),"domain:",p.get("domain_id"),"cat:",p.get("category_id"))
print("brand:",[a for a in (p.get("attributes") or []) if a.get("id") in ("BRAND","MODEL","LINE","FAMILY_NAME","GTIN")])
print("buy_box_winner:",p.get("buy_box_winner"))
print("lowest_price:",p.get("lowest_price"))

# Check if ASVA already has this CPID
search=requests.get(f"{API}/users/me",headers=H,timeout=15).json()
print("\nuser_id:",search.get("id"),"nickname:",search.get("nickname"))
sid=search.get("id")
ex=requests.get(f"{API}/users/{sid}/items/search?catalog_product_id={cpid}",headers=H,timeout=15).json()
print("existing in ASVA:",ex.get("results",[])[:5])
