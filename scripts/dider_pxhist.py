import os, json, requests
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
 "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
 "client_secret":os.environ["MELI_APP_SECRET"],
 "refresh_token":os.environ["MELI_REFRESH_TOKEN_DIDER"],
},timeout=30)
r.raise_for_status(); tok=r.json()
with open("/tmp/dider_rot","w") as f: f.write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
for iid in ["MLM6164209204","MLM6164209208","MLM6164209186","MLM6164171572"]:
 print("=== "+iid+" ===")
 # price history
 h=requests.get(f"{API}/items/{iid}/price_history",headers=H,timeout=20)
 print("hist:", h.status_code, (h.text[:600] if h.status_code!=200 else json.dumps(h.json(),ensure_ascii=False)[:800]))
 # competition / price_to_win
 pw=requests.get(f"{API}/items/{iid}/price_to_win",headers=H,timeout=20)
 print("p2w:", pw.status_code, pw.text[:400])
 # Chequear si hay pricing suggestion / competition_status
 c=requests.get(f"{API}/items/{iid}/competition_status",headers=H,timeout=20)
 print("comp:", c.status_code, c.text[:400])
 # Full item para app_id / user_product_id / etc
 g=requests.get(f"{API}/items/{iid}",headers=H,timeout=20)
 gj=g.json() if g.status_code==200 else {"err":g.text[:200]}
 # print solo los campos interesantes
 keys=["last_updated","date_created","seller_custom_field","user_product_id","catalog_listing","price","base_price","original_price","initial_quantity"]
 print("meta:", {k:gj.get(k) for k in keys})
