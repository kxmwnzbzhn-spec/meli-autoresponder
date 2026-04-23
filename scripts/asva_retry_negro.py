import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

PICS=["743992-MLM110800825777_042026","907793-MLM110799812411_042026","754099-MLM110799606261_042026","670337-MLM110799339535_042026","607429-MLM110800675803_042026","942753-MLM109897720252_042026","943615-MLM110799872413_042026","872073-MLM109897600822_042026","790642-MLM109897660404_042026","914260-MLM109897600830_042026","802251-MLM110798835311_042026"]
PICS_NEGRO=[PICS[0],PICS[1],PICS[8]]

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

title="Bocina Bluetooth Portatil Impermeable Ip67 Bass 35w Negro"[:60]
body={
    "site_id":"MLM","family_name":title,"category_id":cat_id,"currency_id":"MXN",
    "price":299,"available_quantity":179,
    "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
    "pictures":[{"id":p} for p in PICS_NEGRO],
    "attributes":build_attrs("Negro"),
}
# retry con backoff para rate limit brands
for i in range(5):
    rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
    if rp.status_code in (200,201) or "rate_limited" not in rp.text:
        break
    print(f"  attempt {i+1}: rate limited, wait {2**i}s")
    time.sleep(2**i)
print(f"Negro status: {rp.status_code}")
neg_id=None
if rp.status_code in (200,201):
    neg_id=rp.json()["id"]
    print(f"  OK {neg_id}")
else:
    print(json.dumps(rp.json(),indent=2,ensure_ascii=False)[:1500])

# descripciones PUT para las 4
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

IDS={"Azul":"MLM5233454100","Rojo":"MLM2886030837","Morado":"MLM2886136351"}
if neg_id: IDS["Negro"]=neg_id

for color,iid in IDS.items():
    d={"plain_text":DESC_TPL.format(COLOR=color)}
    # intenta PUT, si falla POST
    rp=requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json=d,timeout=15)
    if rp.status_code not in (200,201):
        rp=requests.post(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json=d,timeout=15)
    print(f"desc {color} {iid}: {rp.status_code} {rp.text[:120]}")
    time.sleep(1)

# stock_config
try:
    cfg=json.load(open("stock_config_asva.json")) if os.path.exists("stock_config_asva.json") else {}
except: cfg={}
STK={"Negro":179,"Azul":82,"Rojo":35,"Morado":202}
for c,iid in IDS.items():
    cfg[iid]={"color":c,"stock":STK[c],"max_stock":STK[c],"active":True}
json.dump(cfg,open("stock_config_asva.json","w"),indent=2,ensure_ascii=False)
print("\nRESUMEN FINAL:")
for c,iid in IDS.items(): print(f"  {c}: {iid} | stock={STK[c]}")
