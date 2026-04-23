import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

# === Fotos por color (mapeo VERIFICADO visualmente) ===
PICS=["743992-MLM110800825777_042026","907793-MLM110799812411_042026","754099-MLM110799606261_042026","670337-MLM110799339535_042026","607429-MLM110800675803_042026","942753-MLM109897720252_042026","943615-MLM110799872413_042026","872073-MLM109897600822_042026","790642-MLM109897660404_042026","914260-MLM109897600830_042026","802251-MLM110798835311_042026"]
# pic_00 Negro / pic_01 caja Negro / pic_02 Rojo / pic_03 caja Rojo / pic_04 Morado / pic_05 Rojo / pic_06 caja Azul / pic_07 Rojo / pic_08 Negro / pic_09 Morado / pic_10 Azul
pics_negro =[PICS[0], PICS[1], PICS[8]]
pics_azul  =[PICS[10], PICS[6]]
pics_rojo  =[PICS[2], PICS[3], PICS[5], PICS[7]]
pics_morado=[PICS[4], PICS[9]]

STOCK={"Negro":179,"Azul":82,"Rojo":35,"Morado":202}
print(f"Total stock unificado: {sum(STOCK.values())}")

# === 1) Cerrar viejas publicaciones separadas ===
OLD=["MLM2886024307","MLM2886024313","MLM2886037029"]
print("=== Cerrando publicaciones viejas ===")
for iid in OLD:
    try:
        rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"closed"},timeout=15)
        print(f"  close {iid}: {rp.status_code}")
    except Exception as e:
        print(f"  close {iid} err: {e}")
    time.sleep(0.5)

# === 2) Crear publicación unificada 4 colores ===
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

attrs=build_attrs()

variations=[
    {"price":299,"available_quantity":STOCK["Negro"],"attribute_combinations":[{"id":"COLOR","value_name":"Negro"}],"picture_ids":pics_negro},
    {"price":299,"available_quantity":STOCK["Azul"],"attribute_combinations":[{"id":"COLOR","value_name":"Azul"}],"picture_ids":pics_azul},
    {"price":299,"available_quantity":STOCK["Rojo"],"attribute_combinations":[{"id":"COLOR","value_name":"Rojo"}],"picture_ids":pics_rojo},
    {"price":299,"available_quantity":STOCK["Morado"],"attribute_combinations":[{"id":"COLOR","value_name":"Morado"}],"picture_ids":pics_morado},
]

TITLE="Bocina Bluetooth Portatil Impermeable Ip67 Bass Potente 16h"[:60]

body={
    "site_id":"MLM","title":TITLE,"category_id":cat_id,"currency_id":"MXN",
    "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
    "pictures":[{"id":p} for p in PICS],
    "attributes":attrs,
    "variations":variations,
}

# Intento A: con title + variations (sin family_name) — formula que funcionó para Go 4 de Juan
print("\n=== Intento A: title + variations (sin family_name) ===")
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"  status: {rp.status_code}")
data=rp.json()
print(json.dumps(data,indent=2,ensure_ascii=False)[:2500])

if rp.status_code not in (200,201):
    # Intento B: con family_name, sin title
    print("\n=== Intento B: family_name sin title ===")
    bodyb=dict(body); bodyb.pop("title",None); bodyb["family_name"]=TITLE
    rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=bodyb,timeout=60)
    print(f"  status: {rp.status_code}")
    data=rp.json()
    print(json.dumps(data,indent=2,ensure_ascii=False)[:2500])

if rp.status_code in (200,201):
    new_id=data["id"]
    print(f"\n*** UNIFICADA CREADA: {new_id} ***")
    # Descripción SEO
    DESC="""🔊 BOCINA BLUETOOTH PORTÁTIL SUMERGIBLE IP67 🔊

✅ SONIDO POTENTE 35W RMS — graves profundos
✅ BATERÍA 16 HORAS — escucha todo el día
✅ RESISTENTE AL AGUA Y POLVO IP67 — alberca, playa, lluvia
✅ BLUETOOTH 5.3 ESTABLE — 15 metros
✅ MANOS LIBRES — contesta llamadas
✅ 4 COLORES: Negro, Azul, Rojo, Morado
✅ ENVÍO GRATIS — llega en 24-48h

🎁 INCLUYE:
• Bocina
• Cable USB-C
• Manual

⚡ GARANTÍA 30 DÍAS por defectos de fábrica

📦 BOCINA NUEVA EN CAJA ORIGINAL SELLADA"""
    rd=requests.post(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H,json={"plain_text":DESC},timeout=15)
    print(f"  descripción: {rd.status_code}")
else:
    print("\n!!! NO SE PUDO CREAR UNIFICADA !!!")
