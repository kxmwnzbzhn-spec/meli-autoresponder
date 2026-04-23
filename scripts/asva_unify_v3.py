import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

PICS=["743992-MLM110800825777_042026","907793-MLM110799812411_042026","754099-MLM110799606261_042026","670337-MLM110799339535_042026","607429-MLM110800675803_042026","942753-MLM109897720252_042026","943615-MLM110799872413_042026","872073-MLM109897600822_042026","790642-MLM109897660404_042026","914260-MLM109897600830_042026","802251-MLM110798835311_042026"]
pics_negro =[PICS[0], PICS[1], PICS[8]]
pics_azul  =[PICS[10], PICS[6]]
pics_rojo  =[PICS[2], PICS[3], PICS[5], PICS[7]]
pics_morado=[PICS[4], PICS[9]]
STOCK={"Negro":179,"Azul":82,"Rojo":35,"Morado":202}
TITLE="Bocina Bluetooth Portatil Impermeable Ip67 Bass Potente 16h"[:60]
cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

def build_attrs():
    a=[
        {"id":"BRAND","value_name":"Generica"},{"id":"MODEL","value_name":"Bluetooth Portatil IP67"},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"},{"id":"MAX_BATTERY_AUTONOMY","value_name":"16 h"},
        {"id":"POWER_OUTPUT_RMS","value_name":"35 W"},{"id":"MAX_POWER","value_name":"35 W"},
        {"id":"MIN_FREQUENCY_RESPONSE","value_name":"60 Hz"},{"id":"MAX_FREQUENCY_RESPONSE","value_name":"20 kHz"},
        {"id":"INPUT_IMPEDANCE","value_name":"4 Ω"},{"id":"DISTORTION","value_name":"0.5 %"},
        {"id":"BATTERY_VOLTAGE","value_name":"5 V"},{"id":"IS_WATERPROOF","value_name":"Si"},
        {"id":"IS_PORTABLE","value_name":"Si"},{"id":"IS_WIRELESS","value_name":"Si"},
        {"id":"IS_RECHARGEABLE","value_name":"Si"},{"id":"WITH_BLUETOOTH","value_name":"Si"},
        {"id":"HAS_BLUETOOTH","value_name":"Si"},{"id":"INCLUDES_CABLE","value_name":"Si"},
        {"id":"INCLUDES_BATTERY","value_name":"Si"},{"id":"HAS_MICROPHONE","value_name":"Si"},
        {"id":"IS_DUAL_VOICE_COIL","value_name":"No"},{"id":"IS_DUAL_VOICE_ASSISTANTS","value_name":"No"},
        {"id":"HAS_FM_RADIO","value_name":"No"},{"id":"HAS_SD_MEMORY_INPUT","value_name":"No"},
        {"id":"HAS_LED_LIGHTS","value_name":"No"},{"id":"HAS_APP_CONTROL","value_name":"No"},
        {"id":"HAS_USB_INPUT","value_name":"No"},{"id":"WITH_AUX","value_name":"No"},
        {"id":"WITH_HANDSFREE_FUNCTION","value_name":"Si"},{"id":"SPEAKERS_NUMBER","value_name":"1"},
        {"id":"PICKUPS_NUMBER","value_name":"1"},{"id":"SPEAKER_FORMAT","value_name":"1.0"},
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

# ENFOQUE: crear con catalog_product_id generico (MLM47809508) - permite family_name y acepta variaciones
print("=== Intento 1: catalog_product_id generico MLM47809508 + variations ===")
body={
    "site_id":"MLM","catalog_product_id":"MLM47809508","category_id":cat_id,"currency_id":"MXN",
    "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
    "pictures":[{"id":p} for p in PICS],
    "attributes":attrs,
    "variations":variations,
}
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"  status: {rp.status_code}")
data=rp.json()
print(json.dumps(data,indent=2,ensure_ascii=False)[:1800])

if rp.status_code not in (200,201):
    # Intento 2: price + available_quantity a nivel root junto con variations
    print("\n=== Intento 2: root price+qty + variations ===")
    body2=dict(body)
    body2.pop("catalog_product_id",None)
    body2["title"]=TITLE
    body2["price"]=299
    body2["available_quantity"]=sum(STOCK.values())
    rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body2,timeout=60)
    print(f"  status: {rp.status_code}")
    data=rp.json()
    print(json.dumps(data,indent=2,ensure_ascii=False)[:1800])

if rp.status_code not in (200,201):
    # Intento 3: crear via /user-products primero
    print("\n=== Intento 3: crear user_product + usar su ID ===")
    up_body={
        "family_name":TITLE,
        "category_id":cat_id,
        "attributes":attrs,
        "pictures":[{"id":p} for p in PICS],
        "variations":variations,
    }
    r3=requests.post("https://api.mercadolibre.com/user-products",headers=H,json=up_body,timeout=60)
    print(f"  user-products status: {r3.status_code}")
    print(json.dumps(r3.json(),indent=2,ensure_ascii=False)[:1500])

if rp.status_code in (200,201):
    new_id=data["id"]
    print(f"\n*** UNIFICADA CREADA: {new_id} ***")
    DESC=("🔊 BOCINA BLUETOOTH PORTATIL SUMERGIBLE IP67 🔊\n\n"
          "✅ SONIDO POTENTE 35W RMS - graves profundos\n"
          "✅ BATERIA 16 HORAS - escucha todo el dia\n"
          "✅ RESISTENTE AL AGUA Y POLVO IP67\n"
          "✅ BLUETOOTH 5.3 ESTABLE 15 metros\n"
          "✅ MANOS LIBRES - contesta llamadas\n"
          "✅ 4 COLORES: Negro, Azul, Rojo, Morado\n"
          "✅ ENVIO GRATIS - llega en 24-48h\n\n"
          "🎁 INCLUYE: Bocina, Cable USB-C, Manual\n\n"
          "⚡ GARANTIA 30 DIAS por defectos de fabrica\n\n"
          "📦 BOCINA NUEVA EN CAJA ORIGINAL SELLADA")
    rd=requests.post(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H,json={"plain_text":DESC},timeout=15)
    print(f"  descripcion: {rd.status_code}")
    # actualizar stock_config_asva.json
    try:
        cfg_path="stock_config_asva.json"
        cfg=json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}
    except: cfg={}
    cfg[new_id]={"title":TITLE,"variations":{"Negro":STOCK["Negro"],"Azul":STOCK["Azul"],"Rojo":STOCK["Rojo"],"Morado":STOCK["Morado"]}}
    json.dump(cfg,open("stock_config_asva.json","w"),indent=2,ensure_ascii=False)
else:
    print("\n!!! SIN EXITO EN NINGUN INTENTO !!!")
