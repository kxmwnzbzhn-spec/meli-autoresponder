import os,requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM3048812083"

# Check current
cur=requests.get(f"{API}/items/{IID}",headers=HJ,timeout=15).json()
print(f"BEFORE: status={cur.get('status')} cond={cur.get('condition')} price={cur.get('price')} title={cur.get('title')[:60]}")

# Update price + condition
r1=requests.put(f"{API}/items/{IID}",headers=HJ,json={"price":499,"condition":"used"},timeout=20)
print(f"PUT price+cond: {r1.status_code}")
if r1.status_code>=400: print(r1.text[:400])

# Get existing description
desc_cur=requests.get(f"{API}/items/{IID}/description",headers=HJ,timeout=10).json()
old=desc_cur.get("plain_text","")
print(f"old desc bytes: {len(old)}")

AVISO="""\n\n=== AVISO IMPORTANTE ===
Esta bocina NO ES COMPATIBLE con la aplicación oficial JBL Portable.
Al comprar este producto, el comprador acepta haber leído y está conforme con esta limitante.
Funciones de la app (ecualizador, party boost, control remoto) NO estarán disponibles.
El producto funciona perfectamente vía Bluetooth de manera estándar."""

new_desc = AVISO + "\n\n" + old if old else AVISO
r2=requests.post(f"{API}/items/{IID}/description",headers=HJ,json={"plain_text":new_desc},timeout=15)
print(f"PUT desc: {r2.status_code}")
if r2.status_code>=400: print(r2.text[:400])

# Verify
cur2=requests.get(f"{API}/items/{IID}",headers=HJ,timeout=15).json()
print(f"AFTER: status={cur2.get('status')} cond={cur2.get('condition')} price={cur2.get('price')}")
