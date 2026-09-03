import os, json, requests
API="https://api.mercadolibre.com"
TARGETS=[
 # (item_id, user_product_id, target_price)
 ("MLM6164209204","MLMU5071438719",699),
 ("MLM6164209208","MLMU5071435033",699),
 ("MLM6164209186","MLMU5071427661",699),
 ("MLM6164171572","MLMU5071434885",449),
]
r=requests.post(f"{API}/oauth/token",data={
 "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
 "client_secret":os.environ["MELI_APP_SECRET"],
 "refresh_token":os.environ["MELI_REFRESH_TOKEN_DIDER"],
},timeout=30)
r.raise_for_status(); tok=r.json()
with open("/tmp/dider_rot","w") as f: f.write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
for iid,upid,tp in TARGETS:
 print(f"\n=== {iid} / {upid} target=${tp} ===")
 # 1) GET user-product actual
 g=requests.get(f"{API}/user-products/{upid}",headers=H,timeout=20)
 print(f"GET up {g.status_code}:", (g.text[:400] if g.status_code!=200 else json.dumps(g.json(),ensure_ascii=False)[:400]))
 # 2) PUT user-product price
 p=requests.put(f"{API}/user-products/{upid}",headers={**H,"Content-Type":"application/json"},json={"price":tp,"currency_id":"MXN"},timeout=30)
 print(f"PUT up {p.status_code}:", p.text[:400])
 # verificar item price
 v=requests.get(f"{API}/items/{iid}?attributes=id,price,base_price,user_product_id",headers=H,timeout=20)
 print(f"GET item {v.status_code}:", v.text[:250])
