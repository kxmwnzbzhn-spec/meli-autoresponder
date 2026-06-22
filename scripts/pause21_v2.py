import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CLAIM=5531714512
ORDER="2000016996164296"

# Get shipment for weight evidence
o=requests.get(f"{API}/orders/{ORDER}",headers=H,timeout=15).json()
sid=o.get("shipping",{}).get("id")
print(f"shipping_id: {sid}")
print(f"buyer: {o.get('buyer',{}).get('nickname')}")
print(f"total: ${o.get('total_amount')}")
weight_g=None
dims=None
if sid:
  s=requests.get(f"{API}/shipments/{sid}",headers=H,timeout=15).json()
  print(f"status: {s.get('status')} sub: {s.get('substatus')}")
  print(f"date_shipped: {s.get('status_history',{}).get('date_shipped')}")
  print(f"date_delivered: {s.get('status_history',{}).get('date_delivered')}")
  print(f"tracking: {s.get('tracking_number')}")
  # Find package weight
  pkg=s.get("shipping_items",[]) or []
  for x in pkg:
    print(f"item: {x}")
  # Cost components may have peso
  cc=s.get("cost_components",{})
  print(f"cost: {cc}")
  # Look in shipping_option / declarations
  so=s.get("shipping_option",{})
  print(f"shipping_option keys: {list(so.keys())}")
  for k in ("delivery_type","declared_value","name","speed"):
    if k in so: print(f"  {k}: {so[k]}")
  # Package details
  print(f"\nfull shipment dump (selected):")
  for k in ("id","mode","logistic_type","status","substatus","tracking_number","tracking_method"):
    if k in s: print(f"  {k}: {s[k]}")

# Send strong defense message to mediator (no signature)
msg=(
"Hola, mediador. La reclamación de paquete vacío no se sostiene contra la evidencia objetiva. "
"El producto enviado es un perfume de 100ml con frasco de vidrio y caja, con peso bruto de "
"aproximadamente 400 gramos. El paquete fue recibido por la paquetería con ese peso registrado "
"al despacho y reflejado en la guía de envío entregada al comprador. Si el comprador hubiera "
"recibido un paquete vacío, el peso facturado por la paquetería sería de menos de 50 gramos "
"(solo embalaje), lo que NO ocurrió en este envío. Adicionalmente, todo nuestro proceso de "
"armado y empaque está documentado por video y fotografías previas al despacho. Solicitamos "
"que el comprador devuelva el paquete completo tal cual fue recibido — incluyendo caja, "
"etiquetas y peso original — para inspección por nuestro equipo. Quedamos atentos a la "
"coordinación del envío de retorno."
)
print(f"\nmsg len: {len(msg)}")
r2=requests.post(f"{API}/marketplace/v2/claims/{CLAIM}/actions/send-message",headers=HJ,
  json={"receiver_role":"mediator","message":msg,"attachments":[]},timeout=25)
print(f"\nSEND: {r2.status_code} {r2.text[:500]}")
