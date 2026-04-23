import os,requests,json,re,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

OLD=["MLM2886024307","MLM2886024313","MLM2886037029"]
# 1) Cerrar las 3 viejas
print("=== Cerrando viejas ===")
for iid in OLD:
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"closed"},timeout=15)
    print(f"  close {iid}: {r.status_code}")
    time.sleep(0.5)

# 2) Crear publicacion unificada con variations + family_name (estrategia: primero item sin variations, luego PUT variations)
PICS=["743992-MLM110800825777_042026","907793-MLM110799812411_042026","754099-MLM110799606261_042026","670337-MLM110799339535_042026","607429-MLM110800675803_042026","942753-MLM109897720252_042026","943615-MLM110799872413_042026","872073-MLM109897600822_042026","790642-MLM109897660404_042026","914260-MLM109897600830_042026","802251-MLM110798835311_042026"]
pics_negro=PICS[0:4]; pics_azul=PICS[4:8]; pics_morado=PICS[8:11]

cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

def build_attrs():
    a=[
        {"id":"BRAND","value_name":"Generica"},
        {"id":"MODEL","value_name":"Bluetooth Portatil IP67"},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"},
        {"id":"MAX_BATTERY_AUTONOMY","value_name":"16 h"},
        {"id":"POWER_OUTPUT_RMS","value_name":"35 W"},
        {"id":"MAX_POWER","value_name":"35 W"},
        {"id":"MIN_FREQUENCY_RESPONSE","value_name":"60 Hz"},
        {"id":"MAX_FREQUENCY_RESPONSE","value_name":"20 kHz"},
        {"id":"INPUT_IMPEDANCE","value_name":"4 Ω"},
        {"id":"DISTORTION","value_name":"0.5 %"},
        {"id":"BATTERY_VOLTAGE","value_name":"5 V"},
        {"id":"IS_WATERPROOF","value_name":"Si"},
        {"id":"IS_PORTABLE","value_name":"Si"},
        {"id":"IS_WIRELESS","value_name":"Si"},
        {"id":"IS_RECHARGEABLE","value_name":"Si"},
        {"id":"WITH_BLUETOOTH","value_name":"Si"},
        {"id":"HAS_BLUETOOTH","value_name":"Si"},
        {"id":"INCLUDES_CABLE","value_name":"Si"},
        {"id":"INCLUDES_BATTERY","value_name":"Si"},
        {"id":"HAS_MICROPHONE","value_name":"Si"},
        {"id":"IS_DUAL_VOICE_COIL","value_name":"No"},
        {"id":"IS_DUAL_VOICE_ASSISTANTS","value_name":"No"},
        {"id":"HAS_FM_RADIO","value_name":"No"},
        {"id":"HAS_SD_MEMORY_INPUT","value_name":"No"},
        {"id":"HAS_LED_LIGHTS","value_name":"No"},
        {"id":"HAS_APP_CONTROL","value_name":"No"},
        {"id":"HAS_USB_INPUT","value_name":"No"},
        {"id":"WITH_AUX","value_name":"No"},
        {"id":"WITH_HANDSFREE_FUNCTION","value_name":"Si"},
        {"id":"SPEAKERS_NUMBER","value_name":"1"},
        {"id":"PICKUPS_NUMBER","value_name":"1"},
        {"id":"SPEAKER_FORMAT","value_name":"1.0"},
    ]
    seen={x["id"] for x in a}
    BAD={"EAN","UPC","MPN","SELLER_SKU","COLOR","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","LINE","ALPHANUMERIC_MODEL","GTIN"}
    for ca in cat_attrs:
        aid=ca.get("id"); tags=ca.get("tags") or {}
        req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
        if not req or aid in seen or aid in BAD: continue
        vals=ca.get("values") or []; vt=ca.get("value_type")
        if vals: a.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
        elif vt in ("number","number_unit"): a.append({"id":aid,"value_name":"1"})
        else: a.append({"id":aid,"value_name":"No aplica"})
        seen.add(aid)
    return a

# Estrategia: intentar con variations + family_name juntos + title
attrs=build_attrs()
variations=[
    {"price":299,"available_quantity":1,"attribute_combinations":[{"id":"COLOR","value_name":"Negro"}],"picture_ids":pics_negro},
    {"price":299,"available_quantity":1,"attribute_combinations":[{"id":"COLOR","value_name":"Azul"}],"picture_ids":pics_azul},
    {"price":299,"available_quantity":1,"attribute_combinations":[{"id":"COLOR","value_name":"Morado"}],"picture_ids":pics_morado},
]

# Intento 1: SOLO con title (sin family_name) - copia el approach exitoso de Juan
TITLE="Bocina Bluetooth Portatil Impermeable Ip67 Bass Potente 16h"[:60]
body1={
    "site_id":"MLM","title":TITLE,"category_id":cat_id,"currency_id":"MXN",
    "condition":"new","listing_type_id":"gold_pro","buying_mode":"buy_it_now","catalog_listing":False,
    "pictures":[{"id":p} for p in PICS],
    "attributes":attrs,
    "variations":variations,
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}]
}

print("\n=== Intento 1: title + variations (sin family_name) ===")
r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body1,timeout=30)
print(f"POST: {r.status_code}")
if r.status_code not in (200,201):
    print(f"  err: {str(r.json())[:400]}")

# Intento 2: Si falla, intentar vía /user-products (v2)
if r.status_code not in (200,201):
    print("\n=== Intento 2: via user_product ===")
    # Crear user_product con variations
    up_body={
        "domain":"SPEAKERS",  # sin marca específica
        "family_name":"Bocina Bluetooth IP67",
        "variations":[
            {"attributes":[{"id":"COLOR","value_name":"Negro"}],"pictures":[{"id":p} for p in pics_negro]},
            {"attributes":[{"id":"COLOR","value_name":"Azul"}],"pictures":[{"id":p} for p in pics_azul]},
            {"attributes":[{"id":"COLOR","value_name":"Morado"}],"pictures":[{"id":p} for p in pics_morado]},
        ]
    }
    r2=requests.post("https://api.mercadolibre.com/user-products",headers=H,json=up_body,timeout=30)
    print(f"user-products POST: {r2.status_code} {r2.text[:300]}")

# Intento 3: Crear UN item sin variations, luego PUT con variations
if r.status_code not in (200,201):
    print("\n=== Intento 3: Item simple + PUT variations despues ===")
    body3={**body1}
    del body3["variations"]
    body3["price"]=299
    body3["available_quantity"]=463
    r3=requests.post("https://api.mercadolibre.com/items",headers=H,json=body3,timeout=30)
    print(f"POST simple: {r3.status_code}")
    if r3.status_code in (200,201):
        nid=r3.json().get("id")
        print(f"  created {nid}, ahora PUT variations")
        # Ahora agregar variations
        r4=requests.put(f"https://api.mercadolibre.com/items/{nid}",headers=H,json={"variations":variations,"pictures":[{"id":p} for p in PICS]},timeout=30)
        print(f"PUT variations: {r4.status_code} {r4.text[:300]}")
        if r4.status_code in (200,201):
            # Setup stock config
            DESC="""Bocina Bluetooth Portatil IP67 con Bass Potente y Bateria 16h - Colores: Negro, Azul, Morado

CARACTERISTICAS:
- Sonido estereo 35W con bass profundo
- Bateria 16 horas continuas
- Bluetooth 5.3 alcance 10m
- Impermeable IP67 (alberca, playa, lluvia)
- Carga USB tipo C, correa integrada
- Compatible con iPhone, Android, Samsung, iPad, tablets, laptops, Smart TV

INCLUYE: Bocina + cable USB-C + manual. Envio GRATIS. Garantia 30 dias.

IMPORTANTE: Producto importado sin licencia de marcas premium. Funciona via Bluetooth estandar. NO compatible con apps oficiales. Reclamos solo por defecto funcional, no por audio subjetivo. Devolucion requiere video desempaque.

Palabras clave: bocina bluetooth, altavoz portatil, parlante inalambrico, bocina impermeable, waterproof ip67, bocina bass potente, 16 horas, bocina alberca, playa, camping, fiesta, outdoor, viaje, regalo."""
            requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":DESC},timeout=15)
            try:
                with open("stock_config_asva.json") as f: sc=json.load(f)
            except: sc={}
            # apagar las 3 viejas en stock
            for iid in OLD:
                if iid in sc:
                    sc[iid]["auto_replenish"]=False
                    sc[iid]["deleted"]=True
                    sc[iid]["real_stock"]=0
            sc[nid]={"real_stock":463,"sku":"BOCINA-BT-IP67-UNIFIED","label":"Bocina Bluetooth IP67 ASVA unified","auto_replenish":True,"replenish_quantity":1,"min_visible_stock":1,"account":"asva","variations":{"Negro":{"stock":179},"Azul":{"stock":82},"Morado":{"stock":202}}}
            with open("stock_config_asva.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
            print(f"\n🎉 UNIFIED: {nid}")

if r.status_code in (200,201):
    nid=r.json().get("id")
    print(f"\n🎉 UNIFIED (intento 1): {nid}")
    DESC="""Bocina Bluetooth Portatil IP67 con Bass Potente y Bateria 16h - Colores: Negro, Azul, Morado

CARACTERISTICAS: Sonido estereo 35W, bateria 16 horas, Bluetooth 5.3, IP67, USB-C, correa integrada.

Compatible con iPhone, Android, Samsung, Xiaomi, tablets, laptops, Smart TV.

INCLUYE: Bocina + cable USB-C + manual. Envio GRATIS. Garantia 30 dias.

IMPORTANTE: Producto importado sin licencia de marcas premium. Funciona via Bluetooth estandar. NO compatible con apps oficiales. Reclamos solo por defecto funcional.

Palabras clave: bocina bluetooth, altavoz portatil, parlante inalambrico, bocina impermeable, waterproof ip67, bocina bass potente, 16 horas, bocina alberca, playa, camping, fiesta, outdoor, viaje, regalo."""
    requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":DESC},timeout=15)
    try:
        with open("stock_config_asva.json") as f: sc=json.load(f)
    except: sc={}
    for iid in OLD:
        if iid in sc:
            sc[iid]["auto_replenish"]=False
            sc[iid]["deleted"]=True
            sc[iid]["real_stock"]=0
    sc[nid]={"real_stock":463,"sku":"BOCINA-BT-IP67-UNIFIED","label":"Bocina Bluetooth IP67 ASVA unified","auto_replenish":True,"replenish_quantity":1,"min_visible_stock":1,"account":"asva","variations":{"Negro":{"stock":179},"Azul":{"stock":82},"Morado":{"stock":202}}}
    with open("stock_config_asva.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
