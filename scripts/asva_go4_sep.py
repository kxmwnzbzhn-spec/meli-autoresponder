import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

# Pics ya subidas (de log previo)
COLOR_PICS={
    "Rosa":["943070-MLM110812152897_042026","736301-MLM110811889631_042026","631561-MLM109910375616_042026"],
    "Aqua":["912840-MLM109910346378_042026","974912-MLM110812508765_042026","707783-MLM110812597081_042026"],
    "Azul":["931059-MLM109910551620_042026","608429-MLM110812419181_042026","867982-MLM110811859741_042026"],
    "Negro":["631732-MLM110812597101_042026","950734-MLM110812448995_042026","962690-MLM110812449001_042026"],
    "Rojo":["796791-MLM109910346426_042026","885725-MLM110811889689_042026"],
    "Camuflaje":["758252-MLM110812419221_042026","717391-MLM109910375670_042026","965273-MLM110811889709_042026"],
}

cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

def build_attrs(color):
    a=[
        {"id":"BRAND","value_name":"Generica"},
        {"id":"MODEL","value_name":"BT Go Compact"},
        {"id":"COLOR","value_name":color},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"},
        {"id":"MAX_BATTERY_AUTONOMY","value_name":"7 h"},
        {"id":"POWER_OUTPUT_RMS","value_name":"4.2 W"},
        {"id":"MAX_POWER","value_name":"4.2 W"},
        {"id":"MIN_FREQUENCY_RESPONSE","value_name":"95 Hz"},
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
        {"id":"HAS_MICROPHONE","value_name":"No"},
        {"id":"IS_DUAL_VOICE_COIL","value_name":"No"},
        {"id":"IS_DUAL_VOICE_ASSISTANTS","value_name":"No"},
        {"id":"HAS_FM_RADIO","value_name":"No"},
        {"id":"HAS_SD_MEMORY_INPUT","value_name":"No"},
        {"id":"HAS_LED_LIGHTS","value_name":"No"},
        {"id":"HAS_APP_CONTROL","value_name":"No"},
        {"id":"HAS_USB_INPUT","value_name":"No"},
        {"id":"WITH_AUX","value_name":"No"},
        {"id":"WITH_HANDSFREE_FUNCTION","value_name":"No"},
        {"id":"SPEAKERS_NUMBER","value_name":"1"},
        {"id":"PICKUPS_NUMBER","value_name":"1"},
        {"id":"SPEAKER_FORMAT","value_name":"1.0"},
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

DESC_TPL="""BOCINA BLUETOOTH PORTATIL COMPACTA SUMERGIBLE IP67 - COLOR {COLOR}

CARACTERISTICAS:
- Bluetooth 5.3 estable hasta 10 metros
- Resistente al agua y polvo grado IP67
- Bateria recargable 7 horas de autonomia
- Sonido claro con graves presentes
- Puerto USB-C para carga
- Ultra compacta con correa integrada

QUE INCLUYE:
- 1 Bocina Bluetooth
- 1 Cable USB-C
- Manual

IMPORTANTE:
- Producto GENERICO de importacion. No es de marca reconocida.
- No cuenta con garantia de fabricante internacional.
- Funciona como bocina Bluetooth estandar. No requiere app movil.
- Garantia del vendedor de 30 dias por defectos de fabricacion.

POLITICA:
- Se aceptan devoluciones por defecto de fabrica comprobado en 30 dias.
- NO devoluciones por cambio de opinion.
- NO reclamos por caracteristicas ya informadas.

OTROS COLORES DISPONIBLES: Rosa, Aqua, Azul, Negro, Rojo, Camuflaje.

ENVIO GRATIS - Despacho 24h habiles."""

TITLE_TPL="Bocina Bluetooth Portatil Compacta Ip67 Bass {COLOR}"
RESULTS={}
for color,pics in COLOR_PICS.items():
    if not pics: continue
    title=TITLE_TPL.format(COLOR=color)[:60]
    body={
        "site_id":"MLM","family_name":title,"category_id":cat_id,"currency_id":"MXN",
        "price":199,"available_quantity":10,
        "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
        "sale_terms":[
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"30 días"},
        ],
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
        "pictures":[{"id":p} for p in pics],
        "attributes":build_attrs(color),
    }
    rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=45)
    print(f"=== {color}: {rp.status_code}")
    if rp.status_code in (200,201):
        d=rp.json(); iid=d["id"]
        print(f"  OK {iid}")
        rd=requests.put(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text":DESC_TPL.format(COLOR=color)},timeout=20)
        print(f"  desc: {rd.status_code}")
        RESULTS[color]=iid
    else:
        print(f"  err: {rp.text[:400]}")
    time.sleep(3)

# guardar
try:
    cfg=json.load(open("stock_config_asva.json")) if os.path.exists("stock_config_asva.json") else {}
except: cfg={}
for c,iid in RESULTS.items():
    cfg[iid]={"color":c,"stock":10,"max_stock":10,"active":True,"line":"Go4-Generica"}
json.dump(cfg,open("stock_config_asva.json","w"),indent=2,ensure_ascii=False)

print("\n=== RESUMEN ===")
for c,iid in RESULTS.items(): print(f"  {c}: {iid}")
