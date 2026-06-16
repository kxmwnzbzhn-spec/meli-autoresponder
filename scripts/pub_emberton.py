import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM5516466768"
desc=(
"AVISO IMPORTANTE - LEE ANTES DE COMPRAR\n"
"==========================================\n"
"Esta bocina Marshall Emberton REACONDICIONADA NO ES COMPATIBLE con la "
"aplicacion oficial de Marshall (Marshall Bluetooth App). Al confirmar la "
"compra, el cliente declara haber leido y estar conforme con esta limitante "
"y NO podra presentarla como motivo de devolucion, reclamo o cancelacion.\n\n"
"El funcionamiento Bluetooth es 100% normal y se empareja directamente con "
"cualquier dispositivo (celular, tablet, laptop). Solo se pierde el acceso "
"a la app oficial de Marshall (ecualizador y firmware).\n"
"==========================================\n\n"
"PRODUCTO REACONDICIONADO / REMANUFACTURADO\n\n"
"Bocina Marshall Emberton Bluetooth portatil, color negro. Reacondicionada "
"de fabrica: probada, limpia y certificada en funcionamiento optimo. Puede "
"presentar minimos detalles cosmeticos por uso previo. Funcionamiento al "
"100%. Bateria recargable. Sonido potente. Incluye cable de carga.\n\n"
"CARACTERISTICAS\n"
"- Conectividad: Bluetooth\n"
"- App oficial Marshall: NO COMPATIBLE\n"
"- Bateria recargable, larga duracion\n"
"- Sonido potente, 360 grados\n"
"- Color: negro\n"
"- Estado: reacondicionado funcional\n\n"
"GARANTIA\n"
"30 dias del vendedor contra defectos de funcionamiento. NO aplica a: "
"incompatibilidad con app Marshall (declarada en este aviso), detalles "
"cosmeticos menores propios del producto reacondicionado.\n\n"
"Al comprar este articulo, el cliente acepta expresamente lo anterior."
)

# Check current desc state
g0=requests.get(f"{API}/items/{IID}/description",headers=H,timeout=15)
print("GET desc:",g0.status_code, g0.text[:200])

# Try POST (create) then PUT
po=requests.post(f"{API}/items/{IID}/description",headers=HJ,json={"plain_text":desc},timeout=20)
print("POST desc:",po.status_code, po.text[:300])

# Try plain_text key alternative
pu=requests.put(f"{API}/items/{IID}/description",headers=HJ,json={"plain_text":desc},timeout=20)
print("PUT desc:",pu.status_code, pu.text[:300])

# Confirm
g=requests.get(f"{API}/items/{IID}/description",headers=H,timeout=15).json()
print(f"\nfinal len: {len(g.get('plain_text',''))} chars")
print(g.get('plain_text','')[:400])
