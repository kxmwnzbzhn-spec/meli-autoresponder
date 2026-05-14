import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM5347216886"
DESC = """🔊 BOCINA BLUETOOTH PORTÁTIL ESTILO FLIP 7 - CALIDAD ESPEJO 1:1

✨ CARACTERÍSTICAS PRINCIPALES:
• Bluetooth 5.3 - Conexión rápida y estable hasta 10 metros
• Resistencia IP67 - Sumergible y a prueba de polvo
• Batería de 12+ horas de reproducción continua
• Potencia 30W RMS - Sonido envolvente y graves potentes
• Carga rápida USB-C
• Diseño portátil con asa de transporte
• Sonido estéreo de alta fidelidad

📦 INCLUYE:
✓ 1 Bocina Bluetooth portátil
✓ 1 Cable USB-C de carga
✓ 1 Manual de usuario

⚠️ AVISO IMPORTANTE:
- CALIDAD ESPEJO 1:1 — NO es producto original JBL
- NO compatible con la aplicación JBL Portable
- Réplica con apariencia, sonido y resistencia al agua casi idénticos al modelo original

🎵 IDEAL PARA: Fiestas, playa, alberca, ducha, camping, gym, oficina, regalo.

🚚 ENVÍO GRATIS a todo México con Mercado Envíos
✅ Envío en 24/48 horas

COLORES: Negro / Morado / Azul / Rojo

Etiquetas: Bocina Bluetooth, Bocina Portatil, Speaker Portatil, Altavoz, Flip Bluetooth, Bocina Inalambrica, Bluetooth Speaker"""

# Try multiple endpoint variants
for ep, payload in [
    ("POST",{"plain_text":DESC}),
    ("PUT",{"plain_text":DESC}),
    ("PUT",{"text":DESC}),
]:
    method = ep
    r=requests.request(method,f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json=payload)
    print(f"{method} {list(payload.keys())[0]}: http={r.status_code} {r.text[:200]}")
    if r.status_code<300:
        print("OK!")
        break
