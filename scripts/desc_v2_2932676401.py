import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM2932676401"

# Build HTML description preserving emojis
HTML = """<p><b>Subwoofer pasivo, BT 5.3, USB-C, 12h batería, modo TWS estéreo</b></p>

<p>🔊 <b>BOCINA BLUETOOTH PREMIUM 30W — POTENCIA SIN COMPLICACIONES</b><br>
Una bocina diseñada para los que no se conforman con poco volumen ni con productos frágiles. Acabado espejo metálico de alta gama, sonido envolvente de 30W reales, resistencia IP67 contra agua y polvo, y batería que dura todo el día.</p>

<p>═══════════════════════════════════════════<br>
✅ <b>CARACTERÍSTICAS DESTACADAS</b></p>
<p>🎵 Potencia: 30W RMS con subwoofer pasivo dual<br>
🎵 Bluetooth: 5.3 — alcance hasta 15 metros<br>
🎵 Resistencia: IP67 — sumergible 1 metro, 30 minutos<br>
🎵 Batería: 12 horas continuas a volumen medio-alto<br>
🎵 Carga rápida: USB-C, carga completa en 3 horas<br>
🎵 Acabado: Espejo metálico premium antihuella<br>
🎵 Modo TWS: Conecta dos bocinas para sonido estéreo amplificado<br>
🎵 Compatibilidad: iPhone, Android, tablets, laptops, PC<br>
🎵 Manos libres: Micrófono integrado para llamadas</p>

<p>═══════════════════════════════════════════<br>
🔥 <b>POR QUÉ ESTA BOCINA Y NO OTRA</b></p>
<p>- Más potencia que bocinas de marca al doble de precio<br>
- Bass Pro con membrana subwoofer — el bajo se SIENTE, no solo se escucha<br>
- IP67 certificado — alberca, regaderazo, playa, lluvia<br>
- Carga ultra rápida con USB-C incluido<br>
- Compacta y ligera — cabe en mochila, perfecta para viaje<br>
- Conexión instantánea: enciende y suena en 3 segundos<br>
- Diseño espejo que llama la atención donde sea</p>

<p>═══════════════════════════════════════════<br>
📦 <b>LA CAJA INCLUYE</b></p>
<p>- 1 Bocina Bluetooth 30W Acabado Espejo<br>
- 1 Cable USB-C de carga rápida<br>
- 1 Correa de transporte<br>
- 1 Manual de usuario en español<br>
- Empaque protector original</p>

<p>═══════════════════════════════════════════<br>
🛡️ <b>GARANTÍA Y POLÍTICAS</b></p>
<p>✓ Producto 100% NUEVO, sellado de fábrica<br>
✓ Garantía del vendedor: 30 días por defecto de fabricación<br>
✓ Devolución sin preguntas: 30 días Mercado Libre<br>
✓ Soporte por mensajería Mercado Libre 24/7<br>
✓ Compra protegida con Mercado Pago<br>
✓ Disponible meses sin intereses según tu tarjeta</p>

<p>═══════════════════════════════════════════<br>
🚚 <b>ENVÍO</b></p>
<p>📦 Envío Full Mercado Libre cuando aplica<br>
📦 Entrega en 1-3 días hábiles en zonas metropolitanas<br>
📦 Resto del país: 3-7 días hábiles<br>
📦 Empacado con material anti-golpes y tracking activo</p>

<p>═══════════════════════════════════════════<br>
❓ <b>PREGUNTAS FRECUENTES</b></p>

<p><b>¿Es realmente resistente al agua?</b><br>
Sí, certificación IP67. Sumergible 1 metro durante 30 minutos. Apta para alberca, regaderazo, playa, lluvia y polvo.</p>

<p><b>¿Qué tan fuerte suena?</b><br>
30W RMS con subwoofer pasivo dual. Cubre cómodamente espacios abiertos de hasta 50 m² o reuniones de hasta 20 personas.</p>

<p><b>¿Cuánto dura la batería?</b><br>
12 horas a volumen medio-alto. A volumen máximo continuo dura aproximadamente 8 horas. Carga completa en 3 horas con USB-C.</p>

<p><b>¿Se puede conectar con otra bocina?</b><br>
Sí, función TWS estéreo. Empareja dos bocinas idénticas para sonido envolvente con doble potencia.</p>

<p><b>¿Funciona con iPhone?</b><br>
Sí, 100% compatible con iOS, Android, Windows, macOS y cualquier dispositivo con Bluetooth.</p>

<p><b>¿El acabado espejo se raya fácil?</b><br>
No, el acabado tiene tratamiento antihuella y anti-rayón. Recomendamos limpiar con un paño suave seco.</p>

<p><b>¿Tiene micrófono?</b><br>
Sí, micrófono integrado para llamadas manos libres con cancelación de ruido básica.</p>

<p><b>¿Trae caja original?</b><br>
Sí, viene con empaque original sellado de fábrica.</p>

<p>═══════════════════════════════════════════<br>
⚠️ <b>INFORMACIÓN IMPORTANTE</b></p>
<p>- Stock limitado — pocas unidades disponibles a este precio<br>
- Si tienes dudas técnicas, escríbenos antes de comprar — respondemos en menos de 2 horas<br>
- Vendedor verificado Mercado Libre con envío confiable</p>

<p><b>¡Aprovecha el precio promocional, compra ya antes de que suba!</b></p>"""

for method,key in [("POST","text"),("PUT","text")]:
    r=requests.request(method,f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={key:HTML})
    print(f"{method} {key}: http={r.status_code} {r.text[:250]}")
    if r.status_code<300: break

g=requests.get(f"https://api.mercadolibre.com/items/{iid}/description",headers=H).json()
print(f"\nVERIFY plain_text len={len(g.get('plain_text') or '')} text len={len(g.get('text') or '')}")
