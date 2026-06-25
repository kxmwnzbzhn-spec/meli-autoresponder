import os,requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM3048812083"
old=requests.get(f"{API}/items/{IID}/description",headers=HJ,timeout=10).json().get("plain_text","")
AVISO="""=== AVISO IMPORTANTE ===
Esta bocina NO ES COMPATIBLE con la aplicación oficial JBL Portable.
Al comprar este producto, el comprador acepta haber leído y está conforme con esta limitante.
Funciones de la app (ecualizador, party boost, control remoto) NO estarán disponibles.
El producto funciona perfectamente vía Bluetooth de manera estándar.
========================"""
new_desc = AVISO + "\n\n" + old if old else AVISO
r2=requests.put(f"{API}/items/{IID}/description",headers=HJ,json={"plain_text":new_desc},timeout=15)
print(f"PUT desc: {r2.status_code}")
if r2.status_code>=400: print(r2.text[:400])
# Verify
verif=requests.get(f"{API}/items/{IID}/description",headers=HJ,timeout=10).json()
print(f"verified bytes: {len(verif.get('plain_text',''))}")
print(verif.get("plain_text","")[:300])
