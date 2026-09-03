#!/usr/bin/env python3
import os, json, requests
API="https://api.mercadolibre.com"
# lista (item_id, target_price)
TARGETS=[
 ("MLM6164209204", 699),
 ("MLM6164209208", 699),
 ("MLM6164209186", 699),
 ("MLM6164171572", 449),
]
r=requests.post(f"{API}/oauth/token",data={
 "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
 "client_secret":os.environ["MELI_APP_SECRET"],
 "refresh_token":os.environ["MELI_REFRESH_TOKEN_DIDER"],
},timeout=30)
r.raise_for_status(); tok=r.json()
with open("/tmp/dider_rot","w") as f: f.write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=20).json()
print(f"[auth] uid={me.get('id')} nick={me.get('nickname')}")
out=[]
for iid,tp in TARGETS:
 g=requests.get(f"{API}/items/{iid}?attributes=id,title,price,catalog_product_id,status,available_quantity,seller_id",headers=H,timeout=20)
 before=g.json() if g.status_code==200 else {"error":g.text[:200],"http":g.status_code}
 p=requests.put(f"{API}/items/{iid}",headers={**H,"Content-Type":"application/json"},json={"price":tp},timeout=30)
 put_ok=(p.status_code==200)
 put_body=p.json() if p.headers.get("content-type","").startswith("application/json") else {"raw":p.text[:300]}
 a=requests.get(f"{API}/items/{iid}?attributes=id,price,catalog_product_id,status",headers=H,timeout=20)
 after=a.json() if a.status_code==200 else {"error":a.text[:200],"http":a.status_code}
 row={"item":iid,"target":tp,
      "before":{"price":before.get("price"),"cpid":before.get("catalog_product_id"),"title":before.get("title"),"status":before.get("status")},
      "put":{"http":p.status_code,"ok":put_ok,"err":None if put_ok else put_body},
      "after":{"price":after.get("price"),"cpid":after.get("catalog_product_id"),"status":after.get("status")}}
 out.append(row)
 print(json.dumps(row,ensure_ascii=False))
with open("dider_pin_result.json","w") as f: json.dump(out,f,indent=2,ensure_ascii=False)
