import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

# PICS re-subidas previamente (ya en Juan). Recuperar IDs nuevos o re-subir.
PICS_SRC={
    "Negro": ["743992-MLM110800825777_042026","907793-MLM110799812411_042026","790642-MLM109897660404_042026"],
    "Azul":  ["802251-MLM110798835311_042026","943615-MLM110799872413_042026"],
    "Rojo":  ["754099-MLM110799606261_042026","670337-MLM110799339535_042026","942753-MLM109897720252_042026","872073-MLM109897600822_042026"],
    "Morado":["607429-MLM110800675803_042026","914260-MLM109897600830_042026"],
}
GTIN_PER_COLOR={
    "Negro":"1200130019272",
    "Azul":"1200130019289",
    "Rojo":"1200130019296",
    "Morado":"1200130019319",
}

def reupload(pid):
    try:
        img=requests.get(f"https://http2.mlstatic.com/D_{pid}-O.jpg",timeout=15).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

print("=== UPLOAD PICS flip7 con logo ===")
color_pics={}
for c,pids in PICS_SRC.items():
    out=[]
    for p in pids:
        n=reupload(p)
        if n: out.append(n)
    color_pics[c]=out
    print(f"  {c}: {len(out)}")

cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

def build_attrs():
    a=[
        {"id":"BRAND","value_name":"JBL"},
        {"id":"MODEL","value_name":"Flip 7"},
        {"id":"LINE","value_name":"Flip"},
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
        {"id":"HAS_USB_INPUT","value_name":"Si"},
        {"id":"SPEAKERS_NUMBER","value_name":"1"},{"id":"PICKUPS_NUMBER","value_name":"1"},
        {"id":"SPEAKER_FORMAT","value_name":"1.0"},
    ]
    seen={x["id"] for x in a}
    BAD={"EAN","UPC","MPN","SELLER_SKU","COLOR","GTIN","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","ALPHANUMERIC_MODEL","GRADING","HAS_MICROPHONE","IS_DUAL_VOICE_COIL","WITH_HANDSFREE_FUNCTION","HAS_LED_LIGHTS","IS_DUAL_VOICE_ASSISTANTS","HAS_FM_RADIO","HAS_SD_MEMORY_INPUT","HAS_APP_CONTROL","WITH_AUX"}
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

# variations con GTIN por color
variations=[]
for c in ["Negro","Azul","Rojo","Morado"]:
    if not color_pics.get(c): continue
    variations.append({
        "price":799,"available_quantity":10,
        "attribute_combinations":[
            {"id":"COLOR","value_name":c},
            {"id":"GTIN","value_name":GTIN_PER_COLOR[c]},
        ],
        "picture_ids":color_pics[c],
    })
all_pics=[]
for c in ["Negro","Azul","Rojo","Morado"]:
    for p in color_pics.get(c,[]):
        if p not in all_pics: all_pics.append(p)

body={
    "site_id":"MLM","title":"Bocina Jbl Flip 7 Bluetooth Portatil Ip67 Bass Original Color"[:60],
    "category_id":cat_id,"currency_id":"MXN",
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

print("\n=== POST Flip 7 unificada ===")
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"status: {rp.status_code}")
d=rp.json()
FLIP_ID=None
if rp.status_code in (200,201):
    FLIP_ID=d["id"]
    print(f"*** Flip7 OK {FLIP_ID} ***")
    DESC="""BOCINA JBL FLIP 7 BLUETOOTH PORTATIL IP67 - ORIGINAL - 4 COLORES

CARACTERISTICAS:
- Bluetooth 5.3 estable hasta 15 metros
- Resistente al agua y polvo IP67
- Bateria 16 horas de autonomia
- Sonido 35W RMS JBL Pro Sound
- Manos libres con microfono
- Puerto USB-C de carga
- Entrada USB para alimentacion
- Correa integrada

COLORES: Negro, Azul, Rojo, Morado.

IMPORTANTE:
- Este modelo cuenta con entrada USB para alimentacion y datos.
- Este modelo NO es compatible con la app JBL Portable ni Auracast.
- Opera como bocina Bluetooth estandar.
- Al comprar usted acepta estas caracteristicas tecnicas.

QUE INCLUYE: bocina, cable USB-C, documentacion.

GARANTIA: 30 dias por defecto de fabrica (video + orden).

POLITICA: no se aceptan reclamos por caracteristicas ya informadas ni devoluciones por cambio de opinion.

ENVIO GRATIS."""
    requests.put(f"https://api.mercadolibre.com/items/{FLIP_ID}/description",headers=H,json={"plain_text":DESC},timeout=30)
    print(f"desc enviada")
else:
    print(json.dumps(d,ensure_ascii=False)[:2000])

# ===== GRIP =====
print("\n\n=== GRIP: buscar pics en catalog o search live =====")
# Buscar un item vivo de JBL Grip en MELI de cualquier vendedor para obtener su pic_ids
s=requests.get("https://api.mercadolibre.com/sites/MLM/search?q=JBL+Grip+bocina&limit=10",headers=H).json()
grip_pics_urls=[]
for r_ in (s.get("results") or []):
    if "Grip" in r_.get("title","") and "JBL" in r_.get("title",""):
        tn=r_.get("thumbnail","")
        if tn and "http" in tn:
            # secondary picture
            iid=r_.get("id")
            d=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=pictures",headers=H).json()
            for p in (d.get("pictures") or [])[:5]:
                if p.get("url"): grip_pics_urls.append(p.get("url"))
            break
print(f"  URLs pics Grip: {len(grip_pics_urls)}")

# Download each URL
def upload_url(url):
    try:
        img=requests.get(url,timeout=20).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

grip_pics=[]
for u in grip_pics_urls[:5]:
    n=upload_url(u)
    if n: grip_pics.append(n)
print(f"  grip pics subidas a Juan: {len(grip_pics)}")

if grip_pics:
    ga=[
        {"id":"BRAND","value_name":"JBL"},
        {"id":"MODEL","value_name":"Grip"},
        {"id":"LINE","value_name":"Grip"},
        {"id":"COLOR","value_name":"Negro"},
        {"id":"GTIN","value_name":"050036400242"},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"},
        {"id":"MAX_BATTERY_AUTONOMY","value_name":"12 h"},
        {"id":"POWER_OUTPUT_RMS","value_name":"15 W"},
        {"id":"MAX_POWER","value_name":"15 W"},
        {"id":"MIN_FREQUENCY_RESPONSE","value_name":"85 Hz"},
        {"id":"MAX_FREQUENCY_RESPONSE","value_name":"20 kHz"},
        {"id":"INPUT_IMPEDANCE","value_name":"4 Ω"},
        {"id":"DISTORTION","value_name":"0.5 %"},
        {"id":"BATTERY_VOLTAGE","value_name":"5 V"},
        {"id":"IS_WATERPROOF","value_name":"Si"},{"id":"IS_PORTABLE","value_name":"Si"},
        {"id":"IS_WIRELESS","value_name":"Si"},{"id":"IS_RECHARGEABLE","value_name":"Si"},
        {"id":"WITH_BLUETOOTH","value_name":"Si"},{"id":"HAS_BLUETOOTH","value_name":"Si"},
        {"id":"INCLUDES_CABLE","value_name":"Si"},{"id":"INCLUDES_BATTERY","value_name":"Si"},
        {"id":"HAS_USB_INPUT","value_name":"Si"},
        {"id":"SPEAKERS_NUMBER","value_name":"1"},{"id":"PICKUPS_NUMBER","value_name":"1"},
        {"id":"SPEAKER_FORMAT","value_name":"1.0"},
    ]
    seen={x["id"] for x in ga}
    BAD={"EAN","UPC","MPN","SELLER_SKU","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","ALPHANUMERIC_MODEL","GRADING","HAS_MICROPHONE","IS_DUAL_VOICE_COIL","WITH_HANDSFREE_FUNCTION","HAS_LED_LIGHTS","IS_DUAL_VOICE_ASSISTANTS","HAS_FM_RADIO","HAS_SD_MEMORY_INPUT","HAS_APP_CONTROL","WITH_AUX"}
    for ca in cat_attrs:
        aid=ca.get("id"); tags=ca.get("tags") or {}
        req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
        if not req or aid in seen or aid in BAD: continue
        vals=ca.get("values") or []; vt=ca.get("value_type")
        if vals: ga.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
        elif vt in ("number","number_unit"): ga.append({"id":aid,"value_name":"1"})
        else: ga.append({"id":aid,"value_name":"No aplica"})
        seen.add(aid)

    gbody={
        "site_id":"MLM","title":"Bocina Jbl Grip Bluetooth Portatil Ip67 Original Negra","category_id":cat_id,"currency_id":"MXN",
        "price":699,"available_quantity":10,
        "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
        "pictures":[{"id":p} for p in grip_pics],
        "attributes":ga,
    }
    rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=gbody,timeout=60)
    print(f"  grip status: {rp.status_code}")
    if rp.status_code in (200,201):
        GID=rp.json()["id"]
        print(f"  *** Grip OK {GID} ***")
        GDESC="""BOCINA JBL GRIP BLUETOOTH PORTATIL IP67 - ORIGINAL NEGRA

CARACTERISTICAS:
- Bluetooth 5.3 conexion estable
- Resistente al agua y polvo IP67
- Bateria 12 horas de autonomia
- Sonido JBL Pro Sound
- Manos libres con microfono
- Puerto USB-C de carga
- Entrada USB para alimentacion
- Diseno ergonomico con agarre

IMPORTANTE:
- Este modelo cuenta con entrada USB para alimentacion y datos.
- Este modelo NO es compatible con la app JBL Portable ni Auracast.
- Opera como bocina Bluetooth estandar.
- Al comprar usted acepta estas caracteristicas tecnicas.

QUE INCLUYE: bocina, cable USB-C, documentacion.

GARANTIA: 30 dias por defecto de fabrica (video + orden).

POLITICA: no se aceptan reclamos por caracteristicas ya informadas ni devoluciones por cambio de opinion.

ENVIO GRATIS."""
        requests.put(f"https://api.mercadolibre.com/items/{GID}/description",headers=H,json={"plain_text":GDESC},timeout=30)
        # save stock_config
        try:
            cfg=json.load(open("stock_config.json")) if os.path.exists("stock_config.json") else {}
        except: cfg={}
        cfg[GID]={"line":"Grip-Original","stock":10,"max_stock":10,"active":True,"price":699}
        if FLIP_ID: cfg[FLIP_ID]={"line":"Flip7-Original-Unificada","variations":{c:10 for c in ["Negro","Azul","Rojo","Morado"]},"active":True,"price":799}
        json.dump(cfg,open("stock_config.json","w"),indent=2,ensure_ascii=False)
    else:
        print(f"  grip err: {rp.text[:800]}")
else:
    print("  SIN PICS - no se publica Grip")
