import os,requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

reason="Patron fraude KARLOS1986 doble compra simultanea 18-jun 17:30 (Mandarin Quetzal + Templo Oscuro) con motivos distintos. Envio salio completo y original. Rechazamos devolucion."

# Try POST review with various URL paths and explicit application/json
for cid,rid in [(5530358522,143755516),(5530353540,150143661)]:
  print(f"\n=== RETURN {rid} ===")
  for meth,p,body in [
    ("POST",f"/post-purchase/v1/returns/{rid}/reviews",{"status":"failed","reason_code":"NOT_DELIVERED","description":reason}),
    ("POST",f"/post-purchase/v2/returns/{rid}/reviews",{"status":"failed","reason_code":"NOT_DELIVERED","description":reason}),
    ("POST",f"/post-purchase/v1/returns/{rid}/seller-review",{"status":"failed","description":reason}),
    ("POST",f"/post-purchase/v1/returns/{rid}/reviewing",{"status":"failed","description":reason}),
    ("POST",f"/marketplace/v2/returns/{rid}",{"action":"return_review_fail","description":reason}),
    ("POST",f"/post-purchase/v2/claims/{cid}/returns/{rid}/review",{"status":"failed","description":reason}),
    ("POST",f"/post-purchase/v1/claims/{cid}/returns/{rid}/review",{"status":"failed","description":reason}),
    ("POST",f"/post-purchase/v1/claims/{cid}/returns/{rid}/reviews",{"status":"failed","description":reason}),
    ("POST",f"/post-purchase/v2/claims/{cid}/returns/{rid}/reviews",{"status":"failed","description":reason}),
    ("POST",f"/marketplace/v1/claims/{cid}/returns/{rid}/review",{"status":"failed","description":reason}),
    ("PUT",f"/post-purchase/v1/returns/{rid}/review",{"status":"failed","description":reason}),
    ("PUT",f"/post-purchase/v1/returns/{rid}",{"review":{"status":"failed","description":reason}}),
    ("POST",f"/post-purchase/v1/claims/{cid}/players/respondent/actions",{"action":"return_review_fail","description":reason}),
    ("POST",f"/marketplace/v2/claims/{cid}/players/respondent/actions",{"action":"return_review_fail","description":reason}),
    ("POST",f"/marketplace/v2/claims/{cid}/actions/return_review_fail",{"description":reason}),
    ("POST",f"/marketplace/v2/claims/{cid}/actions/return_review_unified_fail",{"description":reason}),
  ]:
    rr=requests.request(meth,f"{API}{p}",headers=HJ,json=body,timeout=15)
    if rr.status_code!=404:
      print(f"  {meth} {p} -> {rr.status_code} {rr.text[:240]}")
      if rr.status_code in (200,201,204):
        print("  *** WIN ***"); break
