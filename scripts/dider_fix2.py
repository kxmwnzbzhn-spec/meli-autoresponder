import os, json, requests, time
API="https://api.mercadolibre.com"
# (item_id, target_price)
TARGETS=[("MLM6164209204",699),("MLM6164209208",699),("MLM6164209186",699),("MLM6164171572",449)]
r=requests.post(f"{API}/oauth/token",data={
 "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
 "client_secret":os.environ["MELI_APP_SECRET"],
 "refresh_token":os.environ["MELI_REFRESH_TOKEN_DIDER"],
},timeout=30)
r.raise_for_status(); tok=r.json()
with open("/tmp/dider_rot","w") as f: f.write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
for iid,tp in TARGETS:
 print(f"\n### {iid} → ${tp}")
 pr=requests.get(f"{API}/items/{iid}/prices",headers=H,timeout=20).json()
 pid=pr["prices"][0]["id"]
 print(f"price_id={pid} current={pr['prices'][0]['amount']}")
 # Prueba 1: PUT /items/{id}/prices con array
 payload={"prices":[{"id":pid,"type":"standard","amount":tp,"currency_id":"MXN","conditions":{"context_restrictions":[],"start_time":None,"end_time":None}}]}
 t1=requests.put(f"{API}/items/{iid}/prices",headers={**H,"Content-Type":"application/json"},json=payload,timeout=30)
 print(f"[T1 PUT /prices]  {t1.status_code}: {t1.text[:200]}")
 # Prueba 2: PUT /items/{id}/prices/{price_id}
 t2=requests.put(f"{API}/items/{iid}/prices/{pid}",headers={**H,"Content-Type":"application/json"},json={"amount":tp,"currency_id":"MXN","type":"standard"},timeout=30)
 print(f"[T2 PUT /prices/{pid}]  {t2.status_code}: {t2.text[:200]}")
 # Prueba 3: POST /items/{id}/prices con nuevo price
 t3=requests.post(f"{API}/items/{iid}/prices",headers={**H,"Content-Type":"application/json"},json={"amount":tp,"currency_id":"MXN","type":"standard"},timeout=30)
 print(f"[T3 POST /prices]  {t3.status_code}: {t3.text[:200]}")
 time.sleep(2)
 v=requests.get(f"{API}/items/{iid}?attributes=price,base_price",headers=H,timeout=20).json()
 vp=requests.get(f"{API}/items/{iid}/prices",headers=H,timeout=20).json()
 print(f"AFTER item.price={v.get('price')} base={v.get('base_price')} prices={vp.get('prices')}")
