import os,requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM5575746082"
cur=requests.get(f"{API}/items/{IID}",headers=HJ,timeout=15).json()
print(f"item: {cur.get('title')[:60]} status={cur.get('status')} cond={cur.get('condition')} price={cur.get('price')}")
old=requests.get(f"{API}/items/{IID}/description",headers=HJ,timeout=10).json().get("plain_text","")
print(f"old desc bytes: {len(old)}")

AVISO="""=== AVISO IMPORTANTE ===
Esta bocina NO ES COMPATIBLE con la aplicación oficial JBL Portable.
Al comprar este producto, el comprador acepta haber leído y está conforme con esta limitante.
Funciones de la app (ecualizador, party boost, control remoto) NO estarán disponibles.
El producto funciona perfectamente vía Bluetooth de manera estándar.
========================"""
new_desc = AVISO + "\n\n" + old if old else AVISO

# Try PUT first, fallback to POST
r2=requests.put(f"{API}/items/{IID}/description",headers=HJ,json={"plain_text":new_desc},timeout=15)
print(f"PUT desc: {r2.status_code}")
if r2.status_code>=400:
  r3=requests.post(f"{API}/items/{IID}/description",headers=HJ,json={"plain_text":new_desc},timeout=15)
  print(f"POST desc: {r3.status_code}")
  if r3.status_code>=400: print(r3.text[:400])

ver=requests.get(f"{API}/items/{IID}/description",headers=HJ,timeout=10).json()
print(f"verified bytes: {len(ver.get('plain_text',''))}")
print(ver.get("plain_text","")[:200])
