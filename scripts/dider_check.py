import os, json, requests
API="https://api.mercadolibre.com"
IDS=["MLM6164209204","MLM6164209208","MLM6164209186","MLM6164171572"]
r=requests.post(f"{API}/oauth/token",data={
 "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
 "client_secret":os.environ["MELI_APP_SECRET"],
 "refresh_token":os.environ["MELI_REFRESH_TOKEN_DIDER"],
},timeout=30)
r.raise_for_status(); tok=r.json()
with open("/tmp/dider_rot","w") as f: f.write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
for iid in IDS:
 g=requests.get(f"{API}/items/{iid}?attributes=id,price,base_price,original_price,catalog_product_id,status,sale_terms,deal_ids,promotions,price_reference",headers=H,timeout=20).json()
 # tambien pricing endpoint
 pr=requests.get(f"{API}/items/{iid}/prices",headers=H,timeout=20)
 pj=pr.json() if pr.status_code==200 else {"err":pr.text[:200]}
 print(json.dumps({"iid":iid,"item":g,"prices":pj},ensure_ascii=False))
