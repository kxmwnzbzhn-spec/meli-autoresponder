import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM5347901578"

NEW_DESC = """BOCINA BLUETOOTH PORTATIL CHARGE 6 - CALIDAD ESPEJO 1:1
Producto NUEVO de excelente calidad. No es original JBL.

ESPECIFICACIONES TECNICAS:
- Conexion Bluetooth 5.3 de largo alcance (hasta 12 metros)
- Resistencia IP67: sumergible y a prueba de polvo
- Bateria recargable de 28 horas de reproduccion continua
- Potencia total 40W RMS - graves profundos y agudos cristalinos
- Puerto de carga USB-C de alta velocidad
- Diseno robusto con correa de transporte
- Funcion power bank para cargar otros dispositivos
- Compatible con asistentes de voz vinculados al telefono

CONTENIDO DEL EMPAQUE:
- 1 bocina bluetooth portatil
- 1 cable USB-C de carga
- 1 manual de usuario
- Empaque protector

AVISO IMPORTANTE PARA EL COMPRADOR:
- Producto CALIDAD ESPEJO 1:1: replica fiel del modelo original
- NO es producto original de la marca JBL
- NO es compatible con la aplicacion JBL Portable
- Condicion: NUEVO en empaque cerrado
- Calidad de sonido y construccion equivalentes al original
- Acabados premium en todos los detalles

GARANTIA Y SERVICIO:
- Garantia del vendedor por 30 dias contra defectos de fabrica
- Soporte al cliente personalizado via mensajes Mercado Libre
- Devoluciones aceptadas segun politicas Mercado Libre

USOS RECOMENDADOS:
Ideal para fiestas, reuniones, playa, alberca, ducha, camping, gimnasio, oficina, viajes, regalos. Compatible con cualquier dispositivo con Bluetooth: celulares Android, iPhone, tabletas, laptops Windows, Mac, Smart TVs.

ENVIO GRATIS a todo Mexico via Mercado Envios. Despacho en 24 a 48 horas habiles desde nuestro almacen en Mexico.

Bocina Bluetooth, Bocina Portatil, Speaker Portatil, Altavoz, Charge Bluetooth, Bocina Inalambrica, Bluetooth Speaker, Altavoz Resistente al Agua, IP67, 40W, Sumergible, Bocina Recargable, Charge 6, Bocina Charge"""

r=requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":NEW_DESC})
print(f"PUT plain_text: http={r.status_code} {r.text[:200]}")
g=requests.get(f"https://api.mercadolibre.com/items/{iid}/description",headers=H).json()
print(f"VERIFY len={len(g.get('plain_text') or '')}")
print(f"preview: {(g.get('plain_text') or '')[:120]!r}")
