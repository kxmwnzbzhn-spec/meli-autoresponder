import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

COLOR_URLS={
    "Negro": "https://http2.mlstatic.com/D_NQ_NP_640926-MLA102988010115_122025-F.jpg",
    "Morado": "https://http2.mlstatic.com/D_NQ_NP_615832-MLA99988153679_112025-F.jpg",
    "Azul": "https://http2.mlstatic.com/D_NQ_NP_885019-MLA92554764038_092025-F.jpg",
    "Rojo": "https://http2.mlstatic.com/D_NQ_NP_821565-MLA99986261729_112025-F.jpg"
}
EXTRA_PICS=[
  "https://http2.mlstatic.com/D_NQ_NP_892726-MLA102477869906_122025-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_770858-MLA92554764046_092025-F.jpg"
]

variations=[]
for color,url in COLOR_URLS.items():
    variations.append({
        "attribute_combinations":[{"id":"COLOR","value_name":color}],
        "available_quantity":10,
        "price":399,
        "picture_ids":[],
        "pictures":[{"source":url}]
    })

# Top-level pictures = all 4 + extras
main_pics=[{"source":url} for url in list(COLOR_URLS.values())+EXTRA_PICS]

SEO_TITLE="Bocina Bluetooth Portátil Flip 7 Calidad Espejo Ip67 30w"
SEO_DESC = """🔊 BOCINA BLUETOOTH PORTÁTIL ESTILO FLIP 7 - CALIDAD ESPEJO 1:1

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

🎵 IDEAL PARA: Fiestas, playa, alberca, ducha, camping, fiestas en casa, gym, oficina, regalo.

🚚 ENVÍO GRATIS a todo México con Mercado Envíos
✅ Envío en 24/48 horas

COLORES: Negro / Morado / Azul / Rojo

#BocinaBluetooth #BocinaPortatil #SpeakerPortatil #Altavoz #FlipBluetooth #BocinaInalambrica"""

body={
    "title": SEO_TITLE,
    "category_id": "MLM59800",
    "price": 399,
    "currency_id": "MXN",
    "buying_mode": "buy_it_now",
    "listing_type_id": "gold_pro",
    "condition": "new",
    "pictures": main_pics,
    "attributes": [
        {"id":"BRAND","value_name":"Genérica"},
        {"id":"MODEL","value_name":"Flip 7 Espejo"},
        {"id":"LINE","value_name":"Flip"},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"}
    ],
    "variations": variations,
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
    new_id=new.get("id")
    print(f"NEW_ID={new_id} price=${new.get('price')} status={new.get('status')} sub={new.get('sub_status')}")
    print(f"link=https://articulo.mercadolibre.com.mx/{new_id}")
    d=requests.post(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H,json={"plain_text":SEO_DESC})
    print(f"DESC http={d.status_code} {d.text[:200]}")
else:
    print(f"ERR: {r.text[:1500]}")
