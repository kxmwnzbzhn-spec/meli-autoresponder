import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

# Ya tenemos los pic_ids subidos, reusarlos
PICS=["743992-MLM110800825777_042026","907793-MLM110799812411_042026","754099-MLM110799606261_042026","670337-MLM110799339535_042026","607429-MLM110800675803_042026","942753-MLM109897720252_042026","943615-MLM110799872413_042026","872073-MLM109897600822_042026","790642-MLM109897660404_042026","914260-MLM109897600830_042026","802251-MLM110798835311_042026"]
pics_negro=PICS[0:4]; pics_azul=PICS[4:8]; pics_morado=PICS[8:11]

TITLE="Bocina Bluetooth Portatil Impermeable Ip67 Bass Potente 16h"[:60]

DESC="""Bocina Bluetooth Portatil Resistente al Agua IP67 - Sonido Potente con Bass Profundo

===== SONIDO ENVOLVENTE Y POTENTE =====
- Bass profundo con radiador pasivo
- Driver de 45mm de alta fidelidad
- Sonido estereo cristalino con hasta 35W de potencia
- Refuerzo automatico de graves segun entorno
- Audio claro a todo volumen sin distorsion

===== 16 HORAS DE BATERIA =====
- Bateria recargable de larga duracion
- Hasta 16 horas continuas de reproduccion
- Carga rapida via USB tipo C

===== RESISTENCIA IP67 =====
- Impermeable total al agua dulce
- A prueba de polvo, arena y golpes
- Flotante en alberca y playa
- Apto para uso en lluvia, piscina, regadera

===== BLUETOOTH 5.3 DE ULTIMA GENERACION =====
- Alcance 10 metros sin interferencias
- Compatible con iPhone, Android, Samsung, Xiaomi, iPad, tablets, laptops, Smart TV

===== DISENO ULTRAPORTATIL =====
- Peso ligero, correa integrada
- Colores: Negro, Azul, Morado

===== CONTENIDO DE LA CAJA =====
- 1 x Bocina Bluetooth Portatil
- 1 x Cable de carga USB tipo C
- 1 x Manual de usuario

===== GARANTIA Y ENVIO =====
- Producto NUEVO
- Garantia 30 dias contra defectos de funcionamiento
- Envio GRATIS via Mercado Envios
- Envio mismo dia antes de las 2 PM
- Entrega 24-72 hrs

===== IMPORTANTE =====
Producto importado sin licencia de marcas registradas. Funcionalidad identica a bocinas premium del mercado. Funciona via Bluetooth estandar.

POLITICA DE RECLAMOS:
- Cambios solo por defecto de funcionamiento.
- NO aceptamos reclamos subjetivos sobre audio ni comparaciones con otras marcas.
- Devolucion requiere video sin cortes del desempaque.

Palabras clave: bocina bluetooth, altavoz portatil, parlante inalambrico, bocina impermeable, bocina waterproof ip67, bocina bass potente, altavoz 16 horas, bocina alberca, bocina playa, bocina camping, bocina fiesta, bocina outdoor, bocina viaje, bocina regalo."""

def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

cat_id="MLM59800"
cat_attrs=get_cat_attrs(cat_id)

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
    {"id":"IS_SMART","value_name":"No"},
    {"id":"SPEAKERS_NUMBER","value_name":"1"},
    {"id":"PICKUPS_NUMBER","value_name":"1"},
    {"id":"SPEAKER_FORMAT","value_name":"1.0"},
]
seen={a["id"] for a in attrs}
BAD={"EAN","UPC","MPN","SELLER_SKU","COLOR","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","LINE","ALPHANUMERIC_MODEL","GTIN"}
for ca in cat_attrs:
    aid=ca.get("id"); tags=ca.get("tags") or {}
    req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
    if not req or aid in seen or aid in BAD: continue
    vals=ca.get("values") or []; vt=ca.get("value_type")
    if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
    elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
    else: attrs.append({"id":aid,"value_name":"No aplica"})
    seen.add(aid)

# family_name requerido para variations
FAMILY_NAME="Bocina Bluetooth Portatil IP67 ASVA"

variations=[
    {"price":299,"available_quantity":1,"attribute_combinations":[{"id":"COLOR","value_name":"Negro"}],"picture_ids":pics_negro},
    {"price":299,"available_quantity":1,"attribute_combinations":[{"id":"COLOR","value_name":"Azul"}],"picture_ids":pics_azul},
    {"price":299,"available_quantity":1,"attribute_combinations":[{"id":"COLOR","value_name":"Morado"}],"picture_ids":pics_morado},
]

body={
    "site_id":"MLM","title":TITLE,"category_id":cat_id,"currency_id":"MXN",
    "condition":"new","listing_type_id":"gold_pro","buying_mode":"buy_it_now","catalog_listing":False,
    "family_name":FAMILY_NAME,
    "pictures":[{"id":p} for p in PICS],
    "attributes":attrs,
    "variations":variations,
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}]
}

r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
retry=0
while r.status_code not in (200,201) and retry<6:
    retry+=1
    try: j=r.json()
    except: break
    print(f"retry {retry}: {j.get('message')}")
    bad=set(); miss=set(); need_family=False; need_price_qty=False
    for c in j.get("cause",[]):
        msg=c.get("message","") or ""; code=c.get("code","") or ""
        if "family_name" in msg: need_family=True
        if "family_name" in msg and "variations" in msg: pass  # ya tiene
        if "required_fields" in code:
            for m_ in re.findall(r"\[([^\]]+)\]",msg):
                for x in m_.split(","):
                    x=x.strip()
                    if x=="family_name": need_family=True
        if "attributes.ignored" in code or "attributes.invalid" in code or "attributes.omitted" in code:
            mm=re.search(r"\[([A-Z][A-Z_]+)\]",msg)
            if mm: bad.add(mm.group(1))
    if bad: body["attributes"]=[a for a in body["attributes"] if a["id"] not in bad]
    if need_family and "family_name" not in body:
        body["family_name"]=FAMILY_NAME
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)

if r.status_code in (200,201):
    resp=r.json()
    nid=resp.get("id")
    print(f"\n🎉 OK Publicacion: {nid}")
    requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":DESC},timeout=15)
    for v in resp.get("variations",[]):
        ac=v.get("attribute_combinations",[])
        col=ac[0].get("value_name","") if ac else ""
        print(f"  {v.get('id')} {col}: ${v.get('price')} qty={v.get('available_quantity')} pics={len(v.get('picture_ids',[]))}")
    try:
        with open("stock_config_asva.json") as f: sc=json.load(f)
    except: sc={}
    sc[nid]={"real_stock":460,"sku":"BOCINA-BT-IP67-ASVA","label":"Bocina Bluetooth IP67 ASVA","auto_replenish":True,"replenish_quantity":1,"min_visible_stock":1,"account":"asva","variations":{"Negro":{"stock":179},"Azul":{"stock":82},"Morado":{"stock":202}}}
    with open("stock_config_asva.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
    print(f"stock_config_asva: {nid} stock=460")
else:
    print(f"ERR final: {r.json()}")
