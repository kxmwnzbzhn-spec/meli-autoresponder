#!/usr/bin/env python3
import json, os, requests
API="https://api.mercadolibre.com"
ITEMS=["MLM6042921636","MLM6043044650","MLM6042920630","MLM6042920954","MLM6042921184","MLM3376191333","MLM6061828546","MLM6061793358","MLM6061831150","MLM6061856108","MLM6061793370"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],"client_secret":os.environ["MELI_APP_SECRET_NEW"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_EDILBERTO"]},timeout=20)
r.raise_for_status(); tok=r.json()
with open("/tmp/edilberto_verify_rotated_token","w") as f:f.write(tok.get("refresh_token",""))
h={"Authorization":f"Bearer {tok['access_token']}"}
rows=[]
for iid in ITEMS:
 x=requests.get(f"{API}/items/{iid}",headers=h,timeout=15); x.raise_for_status(); item=x.json()
 row={"item_id":iid,"title":item.get("title"),"status":item.get("status"),"sub_status":item.get("sub_status"),"available_quantity":item.get("available_quantity"),"user_product_id":item.get("user_product_id")}
 upid=item.get("user_product_id")
 if upid:
  s=requests.get(f"{API}/user-products/{upid}/stock",headers=h,timeout=15)
  row["stock_http"]=s.status_code
  if s.status_code==200:
   row["editable_stock"]=sum(int(loc.get("quantity") or 0) for loc in (s.json().get("locations") or []) if loc.get("type")!="meli_facility")
 rows.append(row)
print("EDILBERTO_STOCK_VERIFY="+json.dumps(rows,ensure_ascii=False),flush=True)
