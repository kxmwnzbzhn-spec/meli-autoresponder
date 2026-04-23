import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

PICS=["743992-MLM110800825777_042026","907793-MLM110799812411_042026","754099-MLM110799606261_042026","670337-MLM110799339535_042026","607429-MLM110800675803_042026","942753-MLM109897720252_042026","943615-MLM110799872413_042026","872073-MLM109897600822_042026","790642-MLM109897660404_042026","914260-MLM109897600830_042026","802251-MLM110798835311_042026"]

# Mapeo VERIFICADO visualmente:
COLORES={
    "Negro":{"stock":179,"pics":[PICS[0],PICS[1],PICS[8]]},      # pic_00, pic_01 caja, pic_08
    "Azul":{"stock":82,"pics":[PICS[10],PICS[6]]},                 # pic_10, pic_06 caja
    "Rojo":{"stock":35,"pics":[PICS[2],PICS[3],PICS[5],PICS[7]]},  # pic_02, pic_03 caja, pic_05, pic_07
    "Morado":{"stock":202,"pics":[PICS[4],PICS[9]]},               # pic_04, pic_09
}

cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

def build_attrs(color_name):
    a=[
        {"id":"BRAND","value_name":"Generica"},{"id":"MODEL","value_name":"Bluetooth Portatil IP67"},
        {"id":"COLOR","value_name":color_name},
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
    BAD={"EAN","UPC","MPN","SELLER_SKU","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","LINE","ALPHANUMERIC_MODEL","GTIN"}
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

DESC_TPL=("🔊 BOCINA BLUETOOTH PORTATIL SUMERGIBLE IP67 - COLOR {COLOR} 🔊\n\n"
    "✅ SONIDO POTENTE 35W RMS - graves profundos\n"
    "✅ BATERIA 16 HORAS - escucha todo el dia\n"
    "✅ RESISTENTE AL AGUA Y POLVO IP67\n"
    "✅ BLUETOOTH 5.3 ESTABLE 15 metros\n"
    "✅ MANOS LIBRES - contesta llamadas\n"
    "✅ ENVIO GRATIS - llega en 24-48h\n\n"
    "🎁 INCLUYE: Bocina, Cable USB-C, Manual\n\n"
    "⚡ GARANTIA 30 DIAS por defectos de fabrica\n\n"
    "📦 BOCINA NUEVA EN CAJA ORIGINAL SELLADA\n\n"
    "🎨 OTROS COLORES DISPONIBLES: Negro, Azul, Rojo, Morado")

TITLE_TPL="Bocina Bluetooth Portatil Impermeable Ip67 Bass 35w {COLOR}"
results={}
for color,info in COLORES.items():
    title=TITLE_TPL.format(COLOR=color)[:60]
    body={
        "site_id":"MLM","family_name":title,"category_id":cat_id,"currency_id":"MXN",
        "price":299,"available_quantity":info["stock"],
        "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
        "pictures":[{"id":p} for p in info["pics"]],
        "attributes":build_attrs(color),
    }
    rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
    print(f"=== {color} ===  status: {rp.status_code}")
    d=rp.json()
    if rp.status_code in (200,201):
        iid=d["id"]
        print(f"  OK {iid} stock={info['stock']} pics={len(info['pics'])}")
        rd=requests.post(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":DESC_TPL.format(COLOR=color)},timeout=15)
        print(f"  desc: {rd.status_code}")
        results[color]={"id":iid,"stock":info["stock"],"pics":info["pics"]}
    else:
        print(json.dumps(d,indent=2,ensure_ascii=False)[:1500])
    time.sleep(2)

# update stock_config_asva.json
try:
    cfg=json.load(open("stock_config_asva.json")) if os.path.exists("stock_config_asva.json") else {}
except: cfg={}
for color,r in results.items():
    cfg[r["id"]]={"title":TITLE_TPL.format(COLOR=color)[:60],"color":color,"stock":r["stock"],"max_stock":r["stock"]}
json.dump(cfg,open("stock_config_asva.json","w"),indent=2,ensure_ascii=False)
print("\nRESUMEN:")
for c,r in results.items(): print(f"  {c}: {r['id']} | stock={r['stock']}")
