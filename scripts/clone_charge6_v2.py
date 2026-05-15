import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

SRC="MLM5347901578"
src=requests.get(f"https://api.mercadolibre.com/items/{SRC}",headers=H).json()
src_pics=src.get("pictures",[])
pic_ids=[{"id":p.get("id")} for p in src_pics]
print(f"Source pics: {len(pic_ids)}")

TITLE="Bocina Bluetooth Portátil 30W IP67 Acabado Espejo Bass Pro"
print(f"title len={len(TITLE)}")

DESC = """Subwoofer pasivo, BT 5.3, USB-C, 12h batería, modo TWS estéreo

🔊 BOCINA BLUETOOTH PREMIUM 30W — POTENCIA SIN COMPLICACIONES
Una bocina diseñada para los que no se conforman con poco volumen 
ni con productos frágiles. Acabado espejo metálico de alta gama, 
sonido envolvente de 30W reales, resistencia IP67 contra agua y 
polvo, y batería que dura todo el día.
═══════════════════════════════════════════
✅ CARACTERÍSTICAS DESTACADAS
🎵 Potencia: 30W RMS con subwoofer pasivo dual
🎵 Bluetooth: 5.3 — alcance hasta 15 metros
🎵 Resistencia: IP67 — sumergible 1 metro, 30 minutos
🎵 Batería: 12 horas continuas a volumen medio-alto
🎵 Carga rápida: USB-C, carga completa en 3 horas
🎵 Acabado: Espejo metálico premium antihuella
🎵 Modo TWS: Conecta dos bocinas para sonido estéreo amplificado
🎵 Compatibilidad: iPhone, Android, tablets, laptops, PC
🎵 Manos libres: Micrófono integrado para llamadas
═══════════════════════════════════════════
🔥 POR QUÉ ESTA BOCINA Y NO OTRA
- Más potencia que bocinas de marca al doble de precio
- Bass Pro con membrana subwoofer — el bajo se SIENTE, no solo se escucha
- IP67 certificado — alberca, regaderazo, playa, lluvia
- Carga ultra rápida con USB-C incluido
- Compacta y ligera — cabe en mochila, perfecta para viaje
- Conexión instantánea: enciende y suena en 3 segundos
- Diseño espejo que llama la atención donde sea
═══════════════════════════════════════════
📦 LA CAJA INCLUYE
- 1 Bocina Bluetooth 30W Acabado Espejo
- 1 Cable USB-C de carga rápida
- 1 Correa de transporte
- 1 Manual de usuario en español
- Empaque protector original
═══════════════════════════════════════════
🛡️ GARANTÍA Y POLÍTICAS
✓ Producto 100% NUEVO, sellado de fábrica
✓ Garantía del vendedor: 30 días por defecto de fabricación
✓ Devolución sin preguntas: 30 días Mercado Libre
✓ Soporte por mensajería Mercado Libre 24/7
✓ Compra protegida con Mercado Pago
✓ Disponible meses sin intereses según tu tarjeta
═══════════════════════════════════════════
🚚 ENVÍO
📦 Envío Full Mercado Libre cuando aplica
📦 Entrega en 1-3 días hábiles en zonas metropolitanas
📦 Resto del país: 3-7 días hábiles
📦 Empacado con material anti-golpes y tracking activo
═══════════════════════════════════════════
❓ PREGUNTAS FRECUENTES
¿Es realmente resistente al agua?
Sí, certificación IP67. Sumergible 1 metro durante 30 minutos. 
Apta para alberca, regaderazo, playa, lluvia y polvo.
¿Qué tan fuerte suena?
30W RMS con subwoofer pasivo dual. Cubre cómodamente espacios 
abiertos de hasta 50 m² o reuniones de hasta 20 personas.
¿Cuánto dura la batería?
12 horas a volumen medio-alto. A volumen máximo continuo dura 
aproximadamente 8 horas. Carga completa en 3 horas con USB-C.
¿Se puede conectar con otra bocina?
Sí, función TWS estéreo. Empareja dos bocinas idénticas para 
sonido envolvente con doble potencia.
¿Funciona con iPhone?
Sí, 100% compatible con iOS, Android, Windows, macOS y cualquier 
dispositivo con Bluetooth.
¿El acabado espejo se raya fácil?
No, el acabado tiene tratamiento antihuella y anti-rayón. 
Recomendamos limpiar con un paño suave seco.
¿Tiene micrófono?
Sí, micrófono integrado para llamadas manos libres con cancelación 
de ruido básica.
¿Trae caja original?
Sí, viene con empaque original sellado de fábrica.
═══════════════════════════════════════════
⚠️ INFORMACIÓN IMPORTANTE
- Stock limitado — pocas unidades disponibles a este precio
- Si tienes dudas técnicas, escríbenos antes de comprar — 
  respondemos en menos de 2 horas
- Vendedor verificado Mercado Libre con envío confiable
¡Aprovecha el precio promocional, compra ya antes de que suba!"""

SUBTITLE="Subwoofer pasivo, BT 5.3, USB-C, 12h batería, modo TWS estéreo"

body={
    "title": TITLE,
    
    "category_id": "MLM59800",
    "price": 899,
    "currency_id": "MXN",
    "available_quantity": 1,
    "buying_mode": "buy_it_now",
    "listing_type_id": "gold_pro",
    "condition": "new",
    "pictures": pic_ids,
    "attributes": [
        {"id":"BRAND","value_name":"Genérica"},
        {"id":"MODEL","value_name":"MX-30W-MIRROR"},
        {"id":"IS_BLUETOOTH","value_name":"Sí"},
        {"id":"WATER_RESISTANT","value_name":"IP67"},
        {"id":"POWER","value_name":"30 W"},
        {"id":"INPUT_OUTPUT_TYPE","value_name":"USB-C"},
        {"id":"BATTERY_LIFE","value_name":"12 h"},
        {"id":"BATTERY_TYPE","value_name":"Litio recargable"},
        {"id":"WITH_HANDS_FREE","value_name":"Sí"},
        {"id":"WITH_MICROPHONE","value_name":"Sí"}
    ],
    "shipping": {"mode":"me2","local_pick_up":False,"free_shipping":True,"logistic_type":"drop_off"},
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"}
    ]
}

print("--- POSTING ---")
r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body)
print(f"POST http={r.status_code}")
if r.status_code<300:
    new=r.json()
    nid=new.get("id")
    print(f"NEW_ID={nid} price=${new.get('price')} status={new.get('status')}")
    print(f"link=https://articulo.mercadolibre.com.mx/{nid}")
    d=requests.put(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":DESC})
    if d.status_code>=300:
        d=requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":DESC})
    print(f"DESC http={d.status_code} len_sent={len(DESC)}")
else:
    print(f"ERR: {r.text[:1500]}")
