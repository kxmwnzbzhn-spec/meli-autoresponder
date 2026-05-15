import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM2932676401"

DESC = """Subwoofer pasivo, BT 5.3, USB-C, 12h bateria, modo TWS estereo

BOCINA BLUETOOTH PREMIUM 30W - POTENCIA SIN COMPLICACIONES

Una bocina disenada para los que no se conforman con poco volumen ni con productos fragiles. Acabado espejo metalico de alta gama, sonido envolvente de 30W reales, resistencia IP67 contra agua y polvo, y bateria que dura todo el dia.

===========================================
CARACTERISTICAS DESTACADAS
===========================================
- Potencia: 30W RMS con subwoofer pasivo dual
- Bluetooth: 5.3 - alcance hasta 15 metros
- Resistencia: IP67 - sumergible 1 metro, 30 minutos
- Bateria: 12 horas continuas a volumen medio-alto
- Carga rapida: USB-C, carga completa en 3 horas
- Acabado: Espejo metalico premium antihuella
- Modo TWS: Conecta dos bocinas para sonido estereo amplificado
- Compatibilidad: iPhone, Android, tablets, laptops, PC
- Manos libres: Microfono integrado para llamadas

===========================================
POR QUE ESTA BOCINA Y NO OTRA
===========================================
- Mas potencia que bocinas de marca al doble de precio
- Bass Pro con membrana subwoofer - el bajo se SIENTE, no solo se escucha
- IP67 certificado - alberca, regaderazo, playa, lluvia
- Carga ultra rapida con USB-C incluido
- Compacta y ligera - cabe en mochila, perfecta para viaje
- Conexion instantanea: enciende y suena en 3 segundos
- Diseno espejo que llama la atencion donde sea

===========================================
LA CAJA INCLUYE
===========================================
- 1 Bocina Bluetooth 30W Acabado Espejo
- 1 Cable USB-C de carga rapida
- 1 Correa de transporte
- 1 Manual de usuario en espanol
- Empaque protector original

===========================================
GARANTIA Y POLITICAS
===========================================
- Producto 100% NUEVO, sellado de fabrica
- Garantia del vendedor: 30 dias por defecto de fabricacion
- Devolucion sin preguntas: 30 dias Mercado Libre
- Soporte por mensajeria Mercado Libre 24/7
- Compra protegida con Mercado Pago
- Disponible meses sin intereses segun tu tarjeta

===========================================
ENVIO
===========================================
- Envio Full Mercado Libre cuando aplica
- Entrega en 1-3 dias habiles en zonas metropolitanas
- Resto del pais: 3-7 dias habiles
- Empacado con material anti-golpes y tracking activo

===========================================
PREGUNTAS FRECUENTES
===========================================

Es realmente resistente al agua?
Si, certificacion IP67. Sumergible 1 metro durante 30 minutos. Apta para alberca, regaderazo, playa, lluvia y polvo.

Que tan fuerte suena?
30W RMS con subwoofer pasivo dual. Cubre comodamente espacios abiertos de hasta 50 m2 o reuniones de hasta 20 personas.

Cuanto dura la bateria?
12 horas a volumen medio-alto. A volumen maximo continuo dura aproximadamente 8 horas. Carga completa en 3 horas con USB-C.

Se puede conectar con otra bocina?
Si, funcion TWS estereo. Empareja dos bocinas identicas para sonido envolvente con doble potencia.

Funciona con iPhone?
Si, 100% compatible con iOS, Android, Windows, macOS y cualquier dispositivo con Bluetooth.

El acabado espejo se raya facil?
No, el acabado tiene tratamiento antihuella y anti-rayon. Recomendamos limpiar con un pano suave seco.

Tiene microfono?
Si, microfono integrado para llamadas manos libres con cancelacion de ruido basica.

Trae caja original?
Si, viene con empaque original sellado de fabrica.

===========================================
INFORMACION IMPORTANTE
===========================================
- Stock limitado - pocas unidades disponibles a este precio
- Si tienes dudas tecnicas, escribenos antes de comprar - respondemos en menos de 2 horas
- Vendedor verificado Mercado Libre con envio confiable

Aprovecha el precio promocional, compra ya antes de que suba!"""

# Try POST then PUT
for method in ["POST","PUT"]:
    r=requests.request(method,f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":DESC})
    print(f"{method}: http={r.status_code} {r.text[:200]}")
    if r.status_code<300: break
g=requests.get(f"https://api.mercadolibre.com/items/{iid}/description",headers=H).json()
print(f"VERIFY len={len(g.get('plain_text') or '')}")
