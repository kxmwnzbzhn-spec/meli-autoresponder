import os,requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

reason="El paquete devuelto NO corresponde con el producto que despachamos. El envío original salió completo, original y sellado de fábrica; el peso registrado por la paquetería al despacho coincide con peso real producto+empaque. Patrón fraude: comprador KARLOS1986 abrió dos reclamos simultáneos (Mandarin Quetzal + Templo Oscuro) sobre dos compras entregadas el mismo día 18-jun a la misma hora 17:30, con motivos distintos. Rechazamos la devolución."

for cid in [5530358522,5530353540]:
  print(f"\n=== CLAIM {cid} ===")
  for path in [
    f"/marketplace/v2/claims/{cid}/actions/return_review_unified_fail",
    f"/marketplace/v2/claims/{cid}/actions/return_review_fail",
    f"/post-purchase/v2/claims/{cid}/actions/return_review_unified_fail",
    f"/post-purchase/v2/claims/{cid}/actions/return_review_fail",
    f"/marketplace/v1/claims/{cid}/actions/return_review_unified_fail",
    f"/marketplace/v1/claims/{cid}/actions/return_review_fail",
  ]:
    for payload in [
      {"reason_code":"content_mismatch","description":reason},
      {"reason":"content_mismatch","description":reason},
      {"motive":"content_mismatch","description":reason},
      {"description":reason},
      {"reason_code":"DOES_NOT_BELONG_TO_PURCHASE","description":reason},
      {"reason_code":"INCONSISTENT_PRODUCT","description":reason},
    ]:
      rr=requests.post(f"{API}{path}",headers=HJ,json=payload,timeout=20)
      if rr.status_code not in (404,):
        print(f"  {path} {payload.get('reason_code',payload.get('reason',payload.get('motive','--')))} {rr.status_code} {rr.text[:250]}")
        if rr.status_code in (200,201,204):
          print("  *** SUCCESS ***")
          break
