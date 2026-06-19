"""Endpoint correcto: marketplace/v2/claims/{id}/actions/send-message"""
import os, requests, json
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

def send_message(AT, claim_id, receiver_role, message):
    H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
    payload={"receiver_role":receiver_role,"message":message,"attachments":[]}
    r=requests.post(f"{API}/marketplace/v2/claims/{claim_id}/actions/send-message",headers=H,json=payload,timeout=25)
    return r.status_code, r.text[:500]

# Mensajes por tipo de reason
TPL_NOT_WORKING=("Hola, mediador. El producto fue probado y empaquetado en óptimas condiciones antes del envío. "
  "Solicitamos al comprador que realice la devolución del producto a través del proceso oficial de MercadoLibre. "
  "Una vez recibido el producto en nuestras instalaciones y validado el estado reportado, procesaremos el reembolso "
  "correspondiente. Esta es nuestra política estándar para reclamos por defecto. "
  "Quedamos atentos a la coordinación del envío de retorno. Saludos cordiales — Elite Market.")
TPL_BROKEN=("Hola, mediador. El producto fue empacado correctamente con material de protección antes del envío. "
  "Solicitamos que el comprador devuelva el producto para inspeccionar el daño reportado. Una vez recibido y "
  "validado el estado procesaremos reembolso completo. Saludos cordiales — Elite Market.")
TPL_REPENTANT=("Hola, mediador. El producto entregado coincide exactamente con la descripción, fotografías, modelo "
  "y características publicadas. Aceptamos devolución por arrepentimiento siempre que el producto regrese en "
  "condiciones de venta nueva (caja original sellada, sin uso). Una vez recibido y verificado procesamos el "
  "reembolso. Saludos cordiales — Elite Market.")
TPL_COLOR=("Hola, mediador. El producto entregado corresponde al modelo, color y características publicadas. "
  "Solicitamos al comprador devolución para verificación. Una vez recibido procesaremos el reembolso. "
  "Saludos cordiales — Elite Market.")

# 8 claims actionables
TASKS=[
  ("CLARIBEL",5529820798,"JBL Go 3","mediator",TPL_NOT_WORKING),
  ("CLARIBEL",5529258594,"JBL Clip 5","mediator",TPL_NOT_WORKING),
  ("WILBERT",5524649191,"JBL Charge 6","mediator",TPL_REPENTANT),
  ("WILBERT",5522260719,"JBL Charge 6","mediator",TPL_REPENTANT),
  ("CLARIBEL",5530383971,"JBL Go 4","mediator",TPL_BROKEN),
  ("ASVA",5530591691,"Bocina IP67","mediator",TPL_NOT_WORKING),
  ("AH",5530747987,"Sony XB100","complainant",TPL_NOT_WORKING),
  ("ASVA",5530689643,"Buds 2","complainant",TPL_NOT_WORKING),
]

for acct,cid,prod,role,msg in TASKS:
  AT=TOKENS[acct]
  print(f"\n--- {acct} {cid} {prod} → {role} ---")
  code,body=send_message(AT,cid,role,msg)
  status="✅ SENT" if 200<=code<300 else "❌ FAIL"
  print(f"  {status} HTTP {code} {body[:300]}")
