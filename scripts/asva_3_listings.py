import os,requests,json,re,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

PICS=["743992-MLM110800825777_042026","907793-MLM110799812411_042026","754099-MLM110799606261_042026","670337-MLM110799339535_042026","607429-MLM110800675803_042026","942753-MLM109897720252_042026","943615-MLM110799872413_042026","872073-MLM109897600822_042026","790642-MLM109897660404_042026","914260-MLM109897600830_042026","802251-MLM110798835311_042026"]
COLORS=[
    ("Negro",179,PICS[0:4]),
    ("Azul",82,PICS[4:8]),
    ("Morado",202,PICS[8:11]),
]

def seo_title(color):
    return f"Bocina Bluetooth Portatil Impermeable Ip67 {color} Bass 16h"[:60]

DESC_TEMPLATE="""Bocina Bluetooth Portatil Resistente al Agua IP67 con Bass Potente - Color {COLOR}

===== SONIDO POTENTE =====
- Bass profundo con radiador pasivo
- Driver 45mm alta fidelidad  
- Sonido estereo 35W sin distorsion
- Refuerzo automatico de graves

===== 16 HORAS DE BATERIA =====
- Bateria recargable larga duracion
- Hasta 16 horas continuas
- Carga rapida USB tipo C

===== RESISTENCIA IP67 =====
- Impermeable total al agua dulce
- A prueba de polvo, arena, golpes
- Flotante en alberca y playa
- Apto para lluvia, piscina, regadera

===== BLUETOOTH 5.3 =====
- Alcance 10 metros sin interferencias
- Compatible iPhone, Android, Samsung, Xiaomi, iPad, tablets, laptops, Smart TV

===== DISENO ULTRAPORTATIL =====
- Peso ligero, correa integrada
- Color {COLOR} vibrante

===== INCLUYE =====
- 1 x Bocina Bluetooth Portatil {COLOR}
- 1 x Cable USB-C
- 1 x Manual

===== IDEAL PARA =====
Fiestas, playa, alberca, camping, viajes, oficina, outdoor, regalo.

===== GARANTIA Y ENVIO =====
- NUEVO en empaque protegido
- Garantia 30 dias contra defectos funcionales
- Envio GRATIS via Mercado Envios
- Envio mismo dia antes 2 PM
- Entrega 24-72 hrs

===== IMPORTANTE =====
Producto importado sin licencia de marcas registradas. Funciona via Bluetooth estandar. NO compatible con apps oficiales de marcas premium.

POLITICA RECLAMOS:
- Cambios solo por defecto de funcionamiento.
- NO por audio subjetivo ni comparaciones.
- Devolucion requiere video desempaque.

Palabras clave: bocina bluetooth, altavoz portatil, parlante inalambrico, bocina impermeable, bocina waterproof ip67, bocina bass potente, altavoz 16 horas, bocina alberca, bocina playa, bocina camping, bocina fiesta, bocina outdoor, bocina viaje, bocina regalo, bocina {color_lower}."""

cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

def build_attrs(color):
    a=[
        {"id":"BRAND","value_name":"Generica"},
        {"id":"MODEL","value_name":"Bluetooth Portatil IP67"},
        {"id":"COLOR","value_name":color},
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

def publish(color,stock,pics):
    attrs=build_attrs(color)
    body={
        "site_id":"MLM","title":seo_title(color),"category_id":cat_id,"currency_id":"MXN",
        "price":299,"available_quantity":1,
        "condition":"new","listing_type_id":"gold_pro","buying_mode":"buy_it_now","catalog_listing":False,
        "pictures":[{"id":p} for p in pics],
        "attributes":attrs,
        "family_name":f"Bocina Bluetooth IP67 {color}",
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}]
    }
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    retry=0
    while r.status_code not in (200,201) and retry<6:
        retry+=1
        try: j=r.json()
        except: break
        bad=set(); miss=set()
        for c in j.get("cause",[]):
            msg=c.get("message","") or ""; code=c.get("code","") or ""
            if "missing_required" in code or "missing_catalog_required" in code:
                for m_ in re.findall(r"\[([A-Z][A-Z_0-9]+)\]",msg):
                    if m_.startswith("MLM"): continue
                    miss.add(m_)
            if "attributes.ignored" in code or "attributes.invalid" in code or "attributes.omitted" in code or "attribute.invalid" in code:
                for m_ in re.findall(r"\[([A-Z][A-Z_]+)\]",msg):
                    if m_.startswith("MLM"): continue
                    bad.add(m_)
                mm=re.search(r"[Aa]ttribute:?\s+([A-Z][A-Z_]+)",msg)
                if mm and not mm.group(1).startswith("MLM"): bad.add(mm.group(1))
        if bad: body["attributes"]=[a for a in body["attributes"] if a["id"] not in bad]
        for mid in miss:
            if not any(a["id"]==mid for a in body["attributes"]):
                body["attributes"].append({"id":mid,"value_name":"No aplica"})
        r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    return r

try:
    with open("stock_config_asva.json") as f: sc=json.load(f)
except: sc={}

for color,stock,pics in COLORS:
    print(f"\n=== Publicando {color} ===")
    r=publish(color,stock,pics)
    if r.status_code in (200,201):
        nid=r.json().get("id")
        desc=DESC_TEMPLATE.replace("{COLOR}",color).replace("{color_lower}",color.lower())
        requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":desc},timeout=15)
        print(f"  OK {nid}")
        sc[nid]={"real_stock":stock,"sku":f"BOCINA-BT-IP67-{color.upper()}","label":f"Bocina Bluetooth IP67 {color} ASVA","auto_replenish":True,"replenish_quantity":1,"min_visible_stock":1,"account":"asva"}
    else:
        print(f"  ERR: {str(r.json())[:300]}")
    time.sleep(2)

with open("stock_config_asva.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print("\nstock_config_asva guardado")
