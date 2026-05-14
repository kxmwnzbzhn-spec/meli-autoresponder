import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

# Pictures per color (from earlier scan)
COLOR_PICS={
    "Negro": [
        "https://http2.mlstatic.com/D_NQ_NP_640926-MLA102988010115_122025-F.jpg",
        "https://http2.mlstatic.com/D_NQ_NP_892726-MLA102477869906_122025-F.jpg",
        "https://http2.mlstatic.com/D_NQ_NP_852830-MLA102988566925_122025-F.jpg"
    ],
    "Morado": [
        "https://http2.mlstatic.com/D_NQ_NP_615832-MLA99988153679_112025-F.jpg",
        "https://http2.mlstatic.com/D_NQ_NP_933336-MLA97405146460_112025-F.jpg"
    ],
    "Azul": [
        "https://http2.mlstatic.com/D_NQ_NP_885019-MLA92554764038_092025-F.jpg",
        "https://http2.mlstatic.com/D_NQ_NP_770858-MLA92554764046_092025-F.jpg",
        "https://http2.mlstatic.com/D_NQ_NP_640448-MLA92554803950_092025-F.jpg"
    ],
    "Rojo": [
        "https://http2.mlstatic.com/D_NQ_NP_821565-MLA99986261729_112025-F.jpg",
        "https://http2.mlstatic.com/D_NQ_NP_874113-MLA88010379898_072025-F.jpg",
        "https://http2.mlstatic.com/D_NQ_NP_815979-MLA88350105737_072025-F.jpg"
    ]
}

# Upload pictures first to get picture_ids per color
def upload_pic(url):
    r=requests.post("https://api.mercadolibre.com/pictures/items/upload",headers={"Authorization":f"Bearer {T}"},data={"source":url})
    return r.json().get("id")

color_picture_ids={}
main_pic_ids=[]
for color, urls in COLOR_PICS.items():
    pics_ids=[]
    for u in urls:
        pid=upload_pic(u)
        if pid:
            pics_ids.append(pid)
    color_picture_ids[color]=pics_ids
    main_pic_ids.append(pics_ids[0] if pics_ids else None)
    print(f"{color}: uploaded {len(pics_ids)} pics, first_id={pics_ids[0] if pics_ids else None}")

# Build the variations
variations=[]
for color, pic_ids in color_picture_ids.items():
    variations.append({
        "attribute_combinations":[{"id":"COLOR","value_name":color}],
        "available_quantity":10,
        "price":399,
        "picture_ids":pic_ids
    })

SEO_TITLE="Bocina Bluetooth Portátil Estilo Flip 7 Calidad Espejo Ip67 30w"
SEO_DESC = """🔊 BOCINA BLUETOOTH PORTÁTIL ESTILO FLIP 7 - CALIDAD ESPEJO 1:1

✨ CARACTERÍSTICAS PRINCIPALES:
• Bluetooth 5.3 - Conexión rápida y estable hasta 10 metros
• Resistencia IP67 - Sumergible y a prueba de polvo
• Batería de 12+ horas de reproducción continua
• Potencia 30W RMS - Sonido envolvente y graves potentes
• Carga rápida USB-C - Llévala a todos lados
• Diseño portátil con asa de transporte
• Sonido estéreo de alta fidelidad

📦 INCLUYE:
✓ 1 Bocina Bluetooth portátil
✓ 1 Cable USB-C de carga
✓ 1 Manual de usuario

⚠️ AVISO IMPORTANTE - LEER ANTES DE COMPRAR:
- Este producto es CALIDAD ESPEJO 1:1 - No es producto original JBL
- NO es compatible con la aplicación JBL Portable
- Réplica con apariencia, calidad de sonido y resistencia al agua casi idénticas al modelo original
- Calidad superior comparada con otras replicas del mercado

🎵 IDEAL PARA:
- Fiestas, reuniones y conciertos al aire libre
- Playa, piscina, ducha, camping
- Música en casa, oficina o gimnasio
- Regalo perfecto para amantes de la música

🚚 ENVÍO GRATIS a todo México con Mercado Envíos
✅ Productos disponibles - Envío en 24/48 horas

COLORES DISPONIBLES: Negro / Morado / Azul / Rojo
Selecciona tu color favorito al comprar.

#FlipSpeaker #BluetoothSpeaker #BocinaPortatil #FlipBluetooth #Bocina #BocinaInalambrica #SpeakerPortatil #BocinaJBL #Flip7 #Altavoz
"""

body={
    "title": SEO_TITLE,
    "category_id": "MLM59800",
    "price": 399,
    "currency_id": "MXN",
    "buying_mode": "buy_it_now",
    "listing_type_id": "gold_pro",
    "condition": "new",
    "pictures": [{"id":pid} for pid in main_pic_ids if pid],
    "attributes": [
        {"id":"BRAND","value_name":"Genérica"},
        {"id":"MODEL","value_name":"Flip 7 Espejo"},
        {"id":"LINE","value_name":"Flip"},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"},
        {"id":"PRODUCT_TYPE","value_name":"Altavoz portátil"},
        {"id":"IS_BLUETOOTH","value_name":"Sí"},
        {"id":"INPUT_OUTPUT_TYPE","value_name":"USB-C"}
    ],
    "variations": variations,
    "shipping": {
        "mode":"me2",
        "local_pick_up": False,
        "free_shipping": True,
        "logistic_type": "drop_off"
    },
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"}
    ]
}

print("\n--- POSTING ITEM ---")
r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body)
print(f"POST http={r.status_code}")
if r.status_code<300:
    new=r.json()
    new_id=new.get("id")
    print(f"NEW_ID={new_id} price=${new.get('price')} status={new.get('status')}")
    # Add description
    d=requests.post(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H,json={"plain_text":SEO_DESC})
    print(f"DESC http={d.status_code}")
else:
    print(f"ERR: {r.text[:1000]}")
