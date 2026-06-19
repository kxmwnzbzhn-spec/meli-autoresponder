import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

ACC={"ASVA":"MELI_REFRESH_TOKEN_ASVA","CLARIBEL":"MELI_REFRESH_TOKEN_CLARIBEL","WILBERT":"MELI_REFRESH_TOKEN_WILBERT","AH":"MELI_REFRESH_TOKEN_AH"}
TOKENS={}
for a,k in ACC.items():
  rt=os.environ.get(k)
  if not rt: continue
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=20)
  if r.status_code<400: TOKENS[a]=r.json()["access_token"]
print(f"tokens: {list(TOKENS.keys())}")

# PHASE 1: ACCEPT RETURN on claims in 'claim' stage
ACCEPT_RETURN=[
  ("AH",5530747987,"Sony XB100",599),
  ("ASVA",5530689643,"Buds 2",149),
]
print("\n=== PHASE 1: ACCEPT RETURN (refund_with_return) ===")
for acct,cid,prod,amt in ACCEPT_RETURN:
  AT=TOKENS[acct]
  H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
  print(f"\n--- {acct} claim {cid} {prod} ${amt} ---")
  # Try expected-resolutions endpoint
  body={"type":"refund_with_return"}
  r=requests.post(f"{API}/post-purchase/v1/claims/{cid}/expected-resolutions",headers=H,json=body,timeout=20)
  print(f"  POST expected-resolutions: {r.status_code} {r.text[:400]}")
  if r.status_code>=400:
    # Try actions endpoint
    r2=requests.post(f"{API}/post-purchase/v1/claims/{cid}/actions/refund_with_return",headers=H,json={},timeout=20)
    print(f"  POST actions/refund_with_return: {r2.status_code} {r2.text[:400]}")
    if r2.status_code>=400:
      # Try with body
      r3=requests.post(f"{API}/post-purchase/v1/claims/{cid}/actions",headers=H,json={"action":"refund_with_return"},timeout=20)
      print(f"  POST actions {{action:refund_with_return}}: {r3.status_code} {r3.text[:400]}")

# PHASE 2: Mensaje al mediador en disputas
DISPUTES=[
  ("CLARIBEL",5529820798,"JBL Go 3 Negro",398,"not_working_item"),
  ("CLARIBEL",5529258594,"JBL Clip 5 Azul",799,"not_working_item"),
  ("WILBERT",5524649191,"JBL Charge 6",1999,"repentant_buyer"),
  ("WILBERT",5522260719,"JBL Charge 6",1999,"repentant_buyer"),
  ("CLARIBEL",5530383971,"JBL Go 4 Camuflaje",555,"broken_item"),
  ("ASVA",5530591691,"Bocina IP67 Morado",498,"not_working_item"),
]
print("\n\n=== PHASE 2: MENSAJE AL MEDIADOR ===")

TEMPLATES={
  "not_working_item": (
    "Hola, mediador. Solicitamos que el comprador realice la devolución del producto para que nuestro equipo técnico "
    "verifique el reclamo de funcionamiento. El producto fue probado y empaquetado en condiciones óptimas antes del envío. "
    "Estamos dispuestos a procesar el reembolso una vez recibamos el producto de vuelta y se confirme el estado reportado. "
    "Esta es la práctica estándar para reclamos por defectos. Quedamos atentos a la coordinación del envío de retorno. "
    "Saludos cordiales — Elite Market."
  ),
  "broken_item": (
    "Hola, mediador. El producto fue empacado correctamente con material de protección antes del envío. Solicitamos que "
    "el comprador devuelva el producto para inspeccionar el daño reportado y confirmar si corresponde a transporte o uso. "
    "Estamos dispuestos a procesar reembolso completo una vez recibido el producto y validado el daño. Quedamos atentos. "
    "Saludos cordiales — Elite Market."
  ),
  "repentant_buyer": (
    "Hola, mediador. El producto entregado coincide exactamente con la descripción, fotografías, modelo y características "
    "publicadas. No existe defecto ni discrepancia con la publicación. Como política, aceptamos devolución por arrepentimiento "
    "siempre que el producto regrese en condiciones de venta nueva (caja original sellada, sin uso). Una vez recibido y "
    "verificado, procesamos el reembolso. Saludos cordiales — Elite Market."
  ),
  "different_color_or_size": (
    "Hola, mediador. El producto entregado corresponde al modelo, color y características publicadas en el anuncio. "
    "Solicitamos al comprador que realice devolución para verificación. Una vez recibido y confirmada la coincidencia "
    "con lo descrito, procesaremos el reembolso correspondiente. Saludos cordiales — Elite Market."
  ),
}

for acct,cid,prod,amt,reason in DISPUTES:
  AT=TOKENS[acct]
  H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
  msg=TEMPLATES.get(reason, TEMPLATES["not_working_item"])
  print(f"\n--- {acct} {cid} {prod} ${amt} ({reason}) ---")
  body={"receiver_role":"mediator","message":msg}
  r=requests.post(f"{API}/post-purchase/v1/claims/{cid}/messages",headers=H,json=body,timeout=20)
  print(f"  POST message: {r.status_code} {r.text[:300]}")
  if r.status_code>=400:
    # alt: send-message endpoint
    r2=requests.post(f"{API}/post-purchase/v1/claims/{cid}/send-message",headers=H,json=body,timeout=20)
    print(f"  POST send-message: {r2.status_code} {r2.text[:300]}")

print("\n=== DONE ===")
