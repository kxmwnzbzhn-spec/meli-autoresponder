import os,requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

reason="Rechazo de devolucion por fraude. Comprador KARLOS1986. Patron: doble compra 18-jun 17:30, dos motivos distintos. Envio salio completo."

# Test with return shipment id and various action paths
shipments=[(47334583132,143755516,5530358522),(47334514958,150143661,5530353540)]
for sid,rid,cid in shipments:
  print(f"\n=== SHIP {sid} / RET {rid} / CLAIM {cid} ===")
  for p in [
    f"/shipments/{sid}/seller_review",
    f"/shipments/{sid}/actions/review_fail",
    f"/shipments/{sid}/return_review",
    f"/post-purchase/v1/shipments/{sid}/review",
    f"/marketplace/v2/shipments/{sid}/review",
    f"/marketplace/v2/returns/{rid}/shipments/{sid}/review",
  ]:
    rr=requests.post(f"{API}{p}",headers=HJ,json={"status":"failed","description":reason},timeout=12)
    if rr.status_code not in (404,):
      print(f"  POST {p} -> {rr.status_code} {rr.text[:200]}")

# Also try /caseworkflow or /mediations 
for cid in [5530358522]:
  for p in [
    f"/mediations/{cid}",
    f"/mediations/{cid}/messages",
    f"/post-purchase/v1/mediations/{cid}/messages",
    f"/post-purchase/v2/mediations/{cid}/messages",
  ]:
    rr=requests.post(f"{API}{p}",headers=HJ,json={"message":reason,"receiver_role":"mediator"},timeout=12)
    if rr.status_code not in (404,):
      print(f"  POST {p} -> {rr.status_code} {rr.text[:200]}")
    gg=requests.get(f"{API}{p}",headers=HJ,timeout=12)
    if gg.status_code==200:
      print(f"  GET {p} -> {gg.status_code} {gg.text[:300]}")
