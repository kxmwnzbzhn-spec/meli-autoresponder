import os,requests,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

PICS=["743992-MLM110800825777_042026","907793-MLM110799812411_042026","754099-MLM110799606261_042026","670337-MLM110799339535_042026","607429-MLM110800675803_042026","942753-MLM109897720252_042026","943615-MLM110799872413_042026","872073-MLM109897600822_042026","790642-MLM109897660404_042026","914260-MLM109897600830_042026","802251-MLM110798835311_042026"]
pics_negro=PICS[0:4]; pics_azul=PICS[4:8]; pics_morado=PICS[8:11]

TITLE="Bocina Bluetooth Portatil Impermeable Ip67 Bass Potente 16h"[:60]
DESC_SHORT="Bocina Bluetooth IP67 con bass potente 35W y 16 horas bateria. 3 colores."

cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

attrs=[
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
seen={a["id"] for a in attrs}
BAD={"EAN","UPC","MPN","SELLER_SKU","COLOR","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","LINE","ALPHANUMERIC_MODEL","GTIN"}
for ca in cat_attrs:
    aid=ca.get("id"); tags=ca.get("tags") or {}
    req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
    if not req or aid in seen or aid in BAD: continue
    vals=ca.get("values") or []; vt=ca.get("value_type")
    if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
    elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
    else: attrs.append({"id":aid,"value_name":"No aplica"})
    seen.add(aid)

# SIN family_name pero CON price y available_quantity top-level
variations=[
    {"price":299,"available_quantity":1,"attribute_combinations":[{"id":"COLOR","value_name":"Negro"}],"picture_ids":pics_negro},
    {"price":299,"available_quantity":1,"attribute_combinations":[{"id":"COLOR","value_name":"Azul"}],"picture_ids":pics_azul},
    {"price":299,"available_quantity":1,"attribute_combinations":[{"id":"COLOR","value_name":"Morado"}],"picture_ids":pics_morado},
]

body={
    "site_id":"MLM","title":TITLE,"category_id":cat_id,"currency_id":"MXN",
    "price":299,  # requerido aunque variations override
    "available_quantity":3,  # requerido aunque vars override
    "condition":"new","listing_type_id":"gold_pro","buying_mode":"buy_it_now","catalog_listing":False,
    "pictures":[{"id":p} for p in PICS],
    "attributes":attrs,
    "variations":variations,
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}]
}

r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
retry=0
while r.status_code not in (200,201) and retry<8:
    retry+=1
    try: j=r.json()
    except: break
    msg_full=str(j)[:400]
    print(f"retry {retry}: {msg_full}")
    bad=set(); miss=set()
    for c in j.get("cause",[]):
        msg=c.get("message","") or ""; code=c.get("code","") or ""
        if "missing_required" in code or "required" in code:
            for m_ in re.findall(r"\[([A-Z][A-Z_0-9]+)\]",msg):
                if m_.startswith("MLM") or m_ in BAD: continue
                miss.add(m_)
        if "attributes.ignored" in code or "attributes.invalid" in code or "attributes.omitted" in code or "number_invalid" in code or "attribute.invalid" in code:
            for m_ in re.findall(r"\[([A-Z][A-Z_]+)\]",msg):
                if m_=="MLM": continue
                if m_.isupper(): bad.add(m_)
            mm=re.search(r"[Aa]ttribute:?\s+([A-Z][A-Z_]+)",msg)
            if mm and not mm.group(1).startswith("MLM"): bad.add(mm.group(1))
    print(f"  bad={bad} miss={miss}")
    if bad: body["attributes"]=[a for a in body["attributes"] if a["id"] not in bad]
    for mid in miss:
        if not any(a["id"]==mid for a in body["attributes"]):
            body["attributes"].append({"id":mid,"value_name":"No aplica"})
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)

if r.status_code in (200,201):
    resp=r.json()
    nid=resp.get("id")
    print(f"\n🎉 OK: {nid}")
    DESC="""Bocina Bluetooth Portatil Resistente al Agua IP67 con Bass Potente

CARACTERISTICAS: Sonido estereo 35W, bateria 16 horas, Bluetooth 5.3, IP67 waterproof, carga USB-C, correa integrada. Compatible iPhone, Android, Samsung, Xiaomi, tablets, laptops, Smart TV.

INCLUYE: Bocina + cable USB-C + manual. Envio GRATIS. Garantia 30 dias.

Colores disponibles: Negro, Azul, Morado.

IMPORTANTE: Producto importado sin licencia de marcas. Funciona al 100% via Bluetooth estandar. Reclamos solo por defecto funcional, no por audio subjetivo.

Palabras clave: bocina bluetooth, altavoz portatil, parlante inalambrico, bocina impermeable, bocina waterproof ip67, bocina bass potente, altavoz 16 horas, bocina alberca, bocina playa, bocina camping, bocina fiesta, bocina outdoor, bocina viaje, bocina regalo, bocina economica."""
    requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":DESC},timeout=15)
    for v in resp.get("variations",[]):
        ac=v.get("attribute_combinations",[])
        col=ac[0].get("value_name","") if ac else ""
        print(f"  {v.get('id')} {col} ${v.get('price')}")
    try:
        with open("stock_config_asva.json") as f: sc=json.load(f)
    except: sc={}
    sc[nid]={"real_stock":460,"sku":"BOCINA-BT-IP67-ASVA","label":"Bocina Bluetooth IP67 ASVA","auto_replenish":True,"replenish_quantity":1,"min_visible_stock":1,"account":"asva","variations":{"Negro":{"stock":179},"Azul":{"stock":82},"Morado":{"stock":202}}}
    with open("stock_config_asva.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
    print(f"config: {nid} stock=460")
else:
    print(f"ERR FINAL: {r.json()}")
