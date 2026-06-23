import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Refresh the claim to confirm available actions NOW
for cid in [5530358522,5530353540]:
  c=requests.get(f"{API}/post-purchase/v1/claims/{cid}",headers=HJ,timeout=20).json()
  print(f"\n=== CLAIM {cid} ===")
  print("stage:",c.get("stage"),"status:",c.get("status"),"sub:",c.get("status_detail"))
  resp=None
  for p in c.get("players",[]):
    if p.get("role")=="respondent":
      resp=p
  print("respondent actions:",[a.get("action") for a in (resp.get("available_actions",[]) if resp else [])])

  # Try return_review_unified_fail (newer) first
  motive="content_mismatch"
  reason="El paquete devuelto NO corresponde con el producto que despachamos. El envío original salió completo, original y sellado de fábrica; el peso registrado por la paquetería al despacho coincide con el peso real producto+empaque. Detectamos patrón fraudulento: el mismo comprador (KARLOS1986) abrió dos reclamos simultáneos (Mandarin Quetzal y Templo Oscuro) sobre dos compras entregadas el mismo día 18-jun-2026 a la misma hora 17:30 hrs, alegando inconvenientes distintos (caja dañada vs falta de holograma). Rechazamos la devolución y solicitamos al mediador su revisión."

  # Endpoint variants for return_review_unified_fail / return_review_fail
  for action,payload in [
    ("return_review_unified_fail",{"reason_code":motive,"description":reason}),
    ("return_review_fail",{"reason_code":motive,"description":reason}),
    ("return_review_unified_fail",{"reason":motive,"comment":reason}),
    ("return_review_fail",{"reason":motive,"comment":reason}),
  ]:
    url=f"{API}/post-purchase/v1/claims/{cid}/actions/{action}"
    rr=requests.post(url,headers=HJ,json=payload,timeout=25)
    print(f"  {action} [{list(payload.keys())[0]}] {rr.status_code} {rr.text[:300]}")
    if rr.status_code in (200,201,204):
      print("  *** SUCCESS ***")
      break
