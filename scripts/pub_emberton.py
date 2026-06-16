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
"⚠️ AVISO IMPORTANTE — LEE ANTES DE COMPRAR\n"
"================================================\n"
"Esta bocina Marshall Emberton REACONDICIONADA NO ES COMPATIBLE con la "
"aplicación oficial de Marshall (Marshall Bluetooth App). Al confirmar la "
"compra, el cliente declara haber leído y estar conforme con esta limitante "
"y NO podrá presentarla como motivo de devolución, reclamo o cancelación.\n\n"
"El funcionamiento Bluetooth es 100% normal y se empareja directamente con "
"cualquier dispositivo (celular, tablet, laptop). Solo se pierde el acceso a "
"la app oficial de Marshall (ecualizador y firmware).\n"
"================================================\n\n"
"PRODUCTO REACONDICIONADO / REMANUFACTURADO\n\n"
"Bocina Marshall Emberton Bluetooth portátil, color negro. "
"Reacondicionada de fábrica: probada, limpia y certificada en funcionamiento óptimo. "
"Puede presentar mínimos detalles cosméticos por uso previo. "
"Funcionamiento al 100%. Batería recargable. Sonido potente. "
"Incluye cable de carga.\n\n"
"CARACTERÍSTICAS\n"
"• Conectividad: Bluetooth\n"
"• App oficial Marshall: NO COMPATIBLE\n"
"• Batería: recargable, larga duración\n"
"• Sonido: potente, 360°\n"
"• Color: negro\n"
"• Estado: reacondicionado funcional\n\n"
"GARANTÍA\n"
"30 días del vendedor contra defectos de funcionamiento. "
"NO aplica a: incompatibilidad con app Marshall (declarada en este aviso), "
"detalles cosméticos menores propios del producto reacondicionado.\n\n"
"Al comprar este artículo, el cliente acepta expresamente lo anterior."
)
dr=requests.put(f"{API}/items/{IID}/description",headers=HJ,json={"plain_text":desc},timeout=25)
print(f"PUT desc {IID}: {dr.status_code}")
print(dr.text[:500])
g=requests.get(f"{API}/items/{IID}/description",headers=H,timeout=15).json()
print(f"\nlen guardada: {len(g.get('plain_text',''))} chars")
print(g.get('plain_text','')[:400])
