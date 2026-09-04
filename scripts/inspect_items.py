import os,json,requests
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_DIDER"]},timeout=30)
r.raise_for_status(); tok=r.json()
open("/tmp/rot","w").write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
for iid in ["MLM6164209212","MLM6164209210"]:
 print(f"\n### {iid}")
 g=requests.get(f"{API}/items/{iid}",headers=H,timeout=20).json()
 print("title:", g.get("title"))
 print("catalog_product_id:", g.get("catalog_product_id"))
 print("user_product_id:", g.get("user_product_id"))
 print("family_name:", g.get("family_name"))
 # attributes relevantes
 attrs={a["id"]:a.get("value_name") for a in (g.get("attributes") or [])}
 for k in ["BRAND","MODEL","LINE","COLOR","MAIN_COLOR","COLOR_NAME"]:
  if k in attrs: print(f"  {k}: {attrs[k]}")
 # catalog product
 cp=g.get("catalog_product_id")
 if cp:
  p=requests.get(f"{API}/products/{cp}",headers=H,timeout=20).json()
  print("PRODUCT.name:", p.get("name"))
  pattrs={a["id"]:a.get("value_name") for a in (p.get("attributes") or [])}
  for k in ["BRAND","MODEL","LINE","COLOR","MAIN_COLOR"]:
   if k in pattrs: print(f"  P.{k}: {pattrs[k]}")
