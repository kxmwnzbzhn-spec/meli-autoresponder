import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

# 1) Cerrar las 4 Flip 7 separadas existentes en ASVA
OLD={"Negro":"MLM5233480022","Azul":"MLM5233454100","Rojo":"MLM2886030837","Morado":"MLM2886136351"}
# Leer stock real antes de cerrar (preservar en nueva unificada)
OLD_STOCK={}
for c,iid in OLD.items():
    d=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,available_quantity,status",headers=H).json()
    OLD_STOCK[c]=d.get("available_quantity",1)
    print(f"  {c} {iid}: stock_actual={OLD_STOCK[c]} status={d.get('status')}")

print("\n=== CERRAR separadas ===")
for c,iid in OLD.items():
    rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"closed"},timeout=20)
    print(f"  close {c} {iid}: {rp.status_code}")
    time.sleep(1)

# 2) Pics por color (las originales con logo que ya están subidas en ASVA)
COLOR_PICS={
    "Negro": ["743992-MLM110800825777_042026","907793-MLM110799812411_042026","790642-MLM109897660404_042026"],
    "Azul":  ["802251-MLM110798835311_042026","943615-MLM110799872413_042026"],
    "Rojo":  ["754099-MLM110799606261_042026","670337-MLM110799339535_042026","942753-MLM109897720252_042026","872073-MLM109897600822_042026"],
    "Morado":["607429-MLM110800675803_042026","914260-MLM109897600830_042026"],
}

cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

def build_attrs():
    a=[
        {"id":"BRAND","value_name":"Generica"},
        {"id":"MODEL","value_name":"BT Flip Bass 40W"},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"},
        {"id":"MAX_BATTERY_AUTONOMY","value_name":"16 h"},
        {"id":"POWER_OUTPUT_RMS","value_name":"35 W"},
        {"id":"MAX_POWER","value_name":"35 W"},
        {"id":"MIN_FREQUENCY_RESPONSE","value_name":"60 Hz"},
        {"id":"MAX_FREQUENCY_RESPONSE","value_name":"20 kHz"},
        {"id":"INPUT_IMPEDANCE","value_name":"4 Ω"},
        {"id":"DISTORTION","value_name":"0.5 %"},
        {"id":"BATTERY_VOLTAGE","value_name":"5 V"},
        {"id":"IS_WATERPROOF","value_name":"Si"},{"id":"IS_PORTABLE","value_name":"Si"},
        {"id":"IS_WIRELESS","value_name":"Si"},{"id":"IS_RECHARGEABLE","value_name":"Si"},
        {"id":"WITH_BLUETOOTH","value_name":"Si"},{"id":"HAS_BLUETOOTH","value_name":"Si"},
        {"id":"INCLUDES_CABLE","value_name":"Si"},{"id":"INCLUDES_BATTERY","value_name":"Si"},
        {"id":"HAS_MICROPHONE","value_name":"Si"},{"id":"IS_DUAL_VOICE_COIL","value_name":"No"},
        {"id":"IS_DUAL_VOICE_ASSISTANTS","value_name":"No"},{"id":"HAS_FM_RADIO","value_name":"No"},
        {"id":"HAS_SD_MEMORY_INPUT","value_name":"No"},{"id":"HAS_LED_LIGHTS","value_name":"No"},
        {"id":"HAS_APP_CONTROL","value_name":"No"},{"id":"HAS_USB_INPUT","value_name":"No"},
        {"id":"WITH_AUX","value_name":"No"},{"id":"WITH_HANDSFREE_FUNCTION","value_name":"Si"},
        {"id":"SPEAKERS_NUMBER","value_name":"1"},{"id":"PICKUPS_NUMBER","value_name":"1"},
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

# 3) Construir unificada — usar stock visible=1 para mantener escasez
variations=[]
for c in ["Negro","Azul","Rojo","Morado"]:
    variations.append({
        "price":299,"available_quantity":1,
        "attribute_combinations":[{"id":"COLOR","value_name":c}],
        "picture_ids":COLOR_PICS[c],
    })
all_pics=[]
for c in ["Negro","Azul","Rojo","Morado"]:
    for p in COLOR_PICS[c]:
        if p not in all_pics: all_pics.append(p)

TITLE="Bocina Bluetooth Portatil Impermeable Ip67 Bass 35w Multicolor"[:60]

body={
    "site_id":"MLM","title":TITLE,"category_id":cat_id,"currency_id":"MXN",
    "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
    "pictures":[{"id":p} for p in all_pics],
    "attributes":build_attrs(),
    "variations":variations,
}

print("\n=== POST UNIFICADA ASVA ===")
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"status: {rp.status_code}")
d=rp.json()
if rp.status_code not in (200,201):
    print(json.dumps(d,ensure_ascii=False)[:1500])
else:
    NEW=d["id"]
    print(f"*** OK {NEW} ***")
    DESC="""BOCINA BLUETOOTH PORTATIL SUMERGIBLE IP67 - 35W RMS

CARACTERISTICAS TECNICAS:
- Bluetooth 5.3 estable hasta 15 metros
- Resistente al agua y polvo grado IP67
- Bateria recargable 16 horas de uso continuo
- Sonido potente 35W RMS con graves profundos
- Manos libres con microfono integrado
- Puerto USB-C de carga rapida
- 4 colores disponibles: Negro, Azul, Rojo, Morado

QUE INCLUYE:
- 1 Bocina Bluetooth
- 1 Cable USB-C de carga
- Manual de usuario

IMPORTANTE:
- Producto generico de importacion. No es de marca reconocida.
- No cuenta con garantia de fabricante internacional.
- Funciona como bocina Bluetooth estandar. No requiere aplicacion movil.
- Garantia del vendedor de 30 dias por defectos de fabricacion.

POLITICA:
- Se aceptan devoluciones por defecto de fabrica comprobado en 30 dias.
- NO se aceptan devoluciones por cambio de opinion.
- NO se aceptan reclamos por caracteristicas ya informadas.
- Toda devolucion requiere producto + empaque + accesorios completos.

ENVIO GRATIS - Despacho 24h habiles."""
    rd=requests.put(f"https://api.mercadolibre.com/items/{NEW}/description",headers=H,json={"plain_text":DESC},timeout=30)
    print(f"desc: {rd.status_code}")
    # Actualizar stock_config
    try:
        cfg=json.load(open("stock_config_asva.json")) if os.path.exists("stock_config_asva.json") else {}
    except: cfg={}
    # Remover antiguas del config
    for oiid in OLD.values():
        if oiid in cfg: cfg[oiid]["active"]=False; cfg[oiid]["closed"]=True
    # Agregar nueva unificada
    cfg[NEW]={
        "line":"Flip7-Generica-Unificada",
        "variations":{c:{"max":OLD_STOCK.get(c,10),"visible":1} for c in ["Negro","Azul","Rojo","Morado"]},
        "hidden_stock":True,
        "active":True,
    }
    json.dump(cfg,open("stock_config_asva.json","w"),indent=2,ensure_ascii=False)
    print(f"Stock preservado: {OLD_STOCK}")
