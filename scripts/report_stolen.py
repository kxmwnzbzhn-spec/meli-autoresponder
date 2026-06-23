import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

PAIRS=[(5530358522,143755516,"Perfume Mandarin Quetzal"),(5530353540,150143661,"Perfume Templo Oscuro")]

reason_base=("El producto devuelto NO corresponde con el que despachamos: el envio original salio completo, "
"sellado y original. El peso registrado por la paqueteria al despacho coincide con el peso real del producto "
"con embalaje. Patron de fraude detectado: el mismo comprador KARLOS1986 abrio DOS reclamos simultaneos "
"(Mandarin Quetzal y Templo Oscuro) sobre dos compras entregadas el mismo dia 18-jun-2026 a la misma hora "
"17:30 hrs, alegando inconvenientes distintos. Rechazamos la devolucion y defendemos firmemente que el envio "
"salio completo y original.")

for cid,rid,name in PAIRS:
  print(f"\n=== CLAIM {cid} / RETURN {rid} ({name}) ===")
  # Inspect return resource for available actions
  ret=requests.get(f"{API}/marketplace/v2/returns/{rid}",headers=HJ,timeout=15)
  print(f"  GET return {ret.status_code}")
  if ret.status_code==200:
    rj=ret.json()
    print("  return keys:",list(rj.keys())[:30])
    print("  status:",rj.get("status"),"sub:",rj.get("status_detail"))
    print("  available_actions:",rj.get("available_actions"))
  
  # Try multiple endpoint shapes for review fail
  variants=[
    ("POST",f"/marketplace/v2/returns/{rid}/review",{"status":"failed","reason":"content_mismatch","comments":reason_base}),
    ("POST",f"/marketplace/v2/returns/{rid}/review",{"status":"failed","comments":reason_base}),
    ("POST",f"/marketplace/v2/returns/{rid}/review",{"review_status":"failed","comments":reason_base}),
    ("POST",f"/marketplace/v2/returns/{rid}/actions/review_fail",{"comments":reason_base}),
    ("POST",f"/marketplace/v2/returns/{rid}/reviews",{"status":"failed","comments":reason_base}),
    ("POST",f"/post-purchase/v1/returns/{rid}/review",{"status":"failed","comments":reason_base}),
    ("POST",f"/post-purchase/v2/returns/{rid}/review",{"status":"failed","comments":reason_base}),
    ("PUT",f"/marketplace/v2/returns/{rid}/review",{"status":"failed","comments":reason_base}),
    ("POST",f"/marketplace/v2/claims/{cid}/returns/{rid}/review",{"status":"failed","comments":reason_base}),
  ]
  for meth,p,body in variants:
    rr=requests.request(meth,f"{API}{p}",headers=HJ,json=body,timeout=20)
    if rr.status_code!=404:
      print(f"  {meth} {p} {rr.status_code} {rr.text[:280]}")
      if rr.status_code in (200,201,204):
        print("  *** SUCCESS ***"); break
