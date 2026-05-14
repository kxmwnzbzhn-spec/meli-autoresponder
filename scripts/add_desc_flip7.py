import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM5347216886"
DESC_PLAIN = """BOCINA BLUETOOTH PORTATIL ESTILO FLIP 7 - CALIDAD ESPEJO 1:1

CARACTERISTICAS PRINCIPALES:
- Bluetooth 5.3 - Conexion rapida y estable hasta 10 metros
- Resistencia IP67 - Sumergible y a prueba de polvo
- Bateria de 12+ horas de reproduccion continua
- Potencia 30W RMS - Sonido envolvente y graves potentes
- Carga rapida USB-C
- Diseno portatil con asa de transporte
- Sonido estereo de alta fidelidad

INCLUYE:
- 1 Bocina Bluetooth portatil
- 1 Cable USB-C de carga
- 1 Manual de usuario

AVISO IMPORTANTE - LEER ANTES DE COMPRAR:
- CALIDAD ESPEJO 1:1 - NO es producto original JBL
- NO compatible con la aplicacion JBL Portable
- Replica con apariencia, sonido y resistencia al agua casi identicos al modelo original
- Calidad superior comparada con otras replicas del mercado

IDEAL PARA: Fiestas, playa, alberca, ducha, camping, gym, oficina, regalo.

ENVIO GRATIS a todo Mexico con Mercado Envios
Envio en 24/48 horas

COLORES DISPONIBLES: Negro, Morado, Azul, Rojo

Etiquetas: Bocina Bluetooth, Bocina Portatil, Speaker Portatil, Altavoz, Flip Bluetooth, Bocina Inalambrica, Bluetooth Speaker, Altavoz Resistente al Agua, IP67"""

# Try plain_text without emojis/diacritics first
r=requests.post(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":DESC_PLAIN})
print(f"POST plain_text (ascii): http={r.status_code} {r.text[:300]}")
if r.status_code>=300:
    # Try HTML
    DESC_HTML=DESC_PLAIN.replace("\n","<br>")
    r2=requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"text":f"<p>{DESC_HTML}</p>"})
    print(f"PUT text(html): http={r2.status_code} {r2.text[:200]}")
# Verify
g=requests.get(f"https://api.mercadolibre.com/items/{iid}/description",headers=H).json()
print(f"\nVERIFY: plain_text={(g.get('plain_text') or '')[:100]!r} text={(g.get('text') or '')[:100]!r}")
