import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

COLOR_PICS={
    "Negro": [
        "https://http2.mlstatic.com/D_NQ_NP_640926-MLA102988010115_122025-F.jpg",
        "https://http2.mlstatic.com/D_NQ_NP_892726-MLA102477869906_122025-F.jpg"
    ],
    "Morado": [
        "https://http2.mlstatic.com/D_NQ_NP_615832-MLA99988153679_112025-F.jpg",
        "https://http2.mlstatic.com/D_NQ_NP_933336-MLA97405146460_112025-F.jpg"
    ],
    "Azul": [
        "https://http2.mlstatic.com/D_NQ_NP_885019-MLA92554764038_092025-F.jpg",
        "https://http2.mlstatic.com/D_NQ_NP_770858-MLA92554764046_092025-F.jpg"
    ],
    "Rojo": [
        "https://http2.mlstatic.com/D_NQ_NP_821565-MLA99986261729_112025-F.jpg",
        "https://http2.mlstatic.com/D_NQ_NP_874113-MLA88010379898_072025-F.jpg"
    ]
}

# Upload pictures via JSON body (alternate endpoint)
def upload_pic(url):
    r=requests.post("https://api.mercadolibre.com/pictures/items/upload",
                    headers={"Authorization":f"Bearer {T}","Content-Type":"application/json"},
                    json={"source":url})
    if r.status_code<300:
        return r.json().get("id")
    print(f"  upload err {r.status_code}: {r.text[:200]}")
    return None

color_pic_ids={}
for color, urls in COLOR_PICS.items():
    ids=[]
    for u in urls:
        pid=upload_pic(u)
        if pid: ids.append(pid)
    color_pic_ids[color]=ids
    print(f"{color}: {len(ids)} pic ids uploaded")

# Main pictures = first of each color
main_pic_ids=[color_pic_ids[c][0] for c in ["Negro","Morado","Azul","Rojo"] if color_pic_ids.get(c)]

variations=[]
for color in ["Negro","Morado","Azul","Rojo"]:
    pids=color_pic_ids.get(color,[])
    if not pids: continue
    variations.append({
        "attribute_combinations":[{"id":"COLOR","value_name":color}],
        "available_quantity":10,
        "price":399,
        "picture_ids":pids
    })

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

⚠️ AVISO IMPORTANTE - LEER ANTES DE COMPRAR:
- Este producto es CALIDAD ESPEJO 1:1 - NO es producto original JBL
- NO es compatible con la aplicación JBL Portable
- Réplica con apariencia, calidad de sonido y resistencia al agua casi idénticas al modelo original
- Calidad superior comparada con otras replicas del mercado

🎵 IDEAL PARA:
- Fiestas, reuniones y conciertos al aire libre
- Playa, piscina, ducha, camping
- Música en casa, oficina o gimnasio
- Regalo perfecto

🚚 ENVÍO GRATIS a todo México con Mercado Envíos
✅ Productos disponibles - Envío en 24/48 horas

COLORES DISPONIBLES: Negro / Morado / Azul / Rojo

#BocinaBluetooth #BocinaPortatil #SpeakerPortatil #Altavoz #FlipBluetooth #BocinaInalambrica #BluetoothSpeaker"""

body={
    "title": SEO_TITLE,
    "category_id": "MLM59800",
    "currency_id": "MXN",
    "buying_mode": "buy_it_now",
    "listing_type_id": "gold_pro",
    "condition": "new",
    "pictures": [{"id":pid} for pid in main_pic_ids] if main_pic_ids else None,
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
if body.get("pictures") is None: body.pop("pictures")

print("\n--- POSTING ITEM ---")
r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body)
print(f"POST http={r.status_code}")
if r.status_code<300:
    new=r.json()
    new_id=new.get("id")
    print(f"NEW_ID={new_id} price=${new.get('price')} status={new.get('status')}")
    d=requests.post(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H,json={"plain_text":SEO_DESC})
    print(f"DESC http={d.status_code} {d.text[:200]}")
else:
    print(f"ERR: {r.text[:1500]}")
