import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Inspect MLM2967772751 - the Mandarin Quetzal item KARLOS1986 bought (the recipe)
it=requests.get(f"{API}/items/MLM2967772751",headers=H,timeout=15).json()
print("title:",it.get("title"))
print("family_name:",it.get("family_name"))
print("cat:",it.get("category_id"))
print("cpid:",it.get("catalog_product_id"))
print("price:",it.get("price"),"qty:",it.get("available_quantity"))
print("listing_type:",it.get("listing_type_id"),"condition:",it.get("condition"))
print("status:",it.get("status"),"sub:",it.get("sub_status"))
print("shipping mode:",it.get("shipping",{}).get("mode"),"free:",it.get("shipping",{}).get("free_shipping"))
print("sale_terms:",it.get("sale_terms"))
print("attributes:",[(a.get("id"),a.get("value_name")) for a in it.get("attributes",[])][:15])
print("pictures:",len(it.get("pictures",[])))
print("description...")
d=requests.get(f"{API}/items/MLM2967772751/description",headers=H,timeout=10).json()
print(d.get("plain_text","")[:500])

# Also verify MLM52129273 catalog availability for ASVA
print("\n=== MLM52129273 CPID details ===")
cp=requests.get(f"{API}/products/MLM52129273",headers=H,timeout=15).json()
print("name:",cp.get("name"))
print("status:",cp.get("status"))
print("domain:",cp.get("domain_id"))
print("attrs:",[(a.get("id"),a.get("value_name")) for a in (cp.get("attributes") or [])][:10])
