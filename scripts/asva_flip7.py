import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
print(f"ASVA: {me.get('nickname')} id={me.get('id')}")

GDRIVE=[
    "1WAjsRUVzSteUJ6FtN350AWbX6uMEB04_",
    "15JlA3vVZyPH1iT052upDf-1JjNXQX_Bo",
    "1cA2oU9c-GZQHB7gtj-jL1pKPopfemwXO",
    "1bSlP5L-lE7ZiL7uxov55fZj67NlLt0bN",
    "1vlSQMy9wUZUcpZ1y4amA62gca-iN4Ytl",
    "1UOavi0b7RDwbXYDpYlfwdhnbkV19NSAr",
    "1BQA9VQEaOi6hB6bpY0cLCnjjdzTGP8Ks",
    "1HClbNLwd396vm_OaKS-h8aMB1JkOhuGj",
    "1-gES-9ZmC96x1H6dYbttySi1tBzFXl1N",
    "16vsn7pmIIdYfoXF9Ps5IdZuuT2rUPToE",
    "1OWUVXFvyK73zQB-HjX-h_U84qLW4Ipb_",
]

# 1. Descargar
print("\n=== Descargando 11 fotos ===")
imgs=[]
for fid in GDRIVE:
    for url in [f"https://drive.google.com/uc?export=download&id={fid}",f"https://drive.usercontent.google.com/download?id={fid}&export=download&authuser=0"]:
        r=requests.get(url,timeout=30,allow_redirects=True)
        if r.status_code==200 and len(r.content)>1000 and r.content[:4] in (b'\xff\xd8\xff\xe0',b'\xff\xd8\xff\xe1',b'\xff\xd8\xff\xdb',b'\xff\xd8\xff\xee',b'\x89PNG'):
            imgs.append(r.content)
            print(f"  OK {fid[:15]}: {len(r.content)} bytes")
            break
    else:
        print(f"  FAIL {fid}")

# 2. Upload a MELI
print(f"\n=== Upload {len(imgs)} fotos a MELI ===")
pic_ids=[]
for idx,img in enumerate(imgs):
    files={"file":(f"bocina_{idx}.jpg",img,"image/jpeg")}
    r=requests.post("https://api.mercadolibre.com/pictures",headers={"Authorization":f"Bearer {TOKEN}"},files=files,timeout=60)
    if r.status_code in (200,201):
        pid=r.json().get("id")
        pic_ids.append(pid)
        print(f"  OK pic{idx}: {pid}")
    else:
        print(f"  ERR pic{idx}: {r.status_code}")
    time.sleep(0.8)

print(f"Total pic_ids: {len(pic_ids)}")

# 3. Dividir fotos por color (asumo 4/4/3 en orden)
# Negro: 0-3, Azul: 4-7, Morado: 8-10
pics_negro=pic_ids[0:4]
pics_azul=pic_ids[4:8]
pics_morado=pic_ids[8:11]

# 4. Construir publicacion
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
- Indicador LED de nivel de bateria

===== RESISTENCIA IP67 =====
- Impermeable total al agua dulce
- A prueba de polvo, arena y golpes
- Flotante en alberca y playa
- Apto para uso en lluvia, piscina, regadera
- Construccion reforzada resistente a caidas

===== BLUETOOTH 5.3 DE ULTIMA GENERACION =====
- Alcance 10 metros sin interferencias
- Conexion estable y rapida
- Compatible con cualquier dispositivo Bluetooth
- Empareja con iPhone, Android, Samsung, Xiaomi, iPad, tablets, laptops Windows / Mac, Smart TV, consolas

===== DISENO ULTRAPORTATIL =====
- Peso ligero, facil de llevar
- Correa integrada para colgar o atar
- Materiales premium antideslizantes
- Colores vibrantes: Negro, Azul, Morado

===== CONTENIDO DE LA CAJA =====
- 1 x Bocina Bluetooth Portatil
- 1 x Cable de carga USB tipo C
- 1 x Manual de usuario
- 1 x Guia rapida

===== IDEAL PARA =====
- Fiestas, reuniones, eventos sociales
- Playa, alberca, camping, excursiones
- Viajes, carretera, oficina, estudio
- Gym, deportes outdoor, yoga al aire libre
- Regalo original para jovenes, hombres, mujeres, adolescentes

===== GARANTIA Y ENVIO =====
- Producto NUEVO en empaque protegido
- Garantia de 30 dias contra defectos de funcionamiento
- Envio GRATIS a todo Mexico via Mercado Envios
- Envio el mismo dia si compras antes de las 2 PM
- Entrega en 24 a 72 hrs habiles en toda la Republica

===== IMPORTANTE LEE ANTES DE COMPRAR =====
Producto importado sin licencia de marcas registradas. Funcionalidad identica a bocinas premium del mercado. Funciona via Bluetooth estandar con cualquier dispositivo.

POLITICA DE RECLAMOS:
- Cambios solo por defecto de funcionamiento (no enciende, no pairea, no carga).
- NO aceptamos reclamos subjetivos sobre audio, comparaciones con otras marcas o cambio de opinion.
- Devoluciones requieren video sin cortes del desempaque desde Mercado Envios.

Al comprar aceptas estas condiciones.

===== PALABRAS CLAVE =====
bocina bluetooth, altavoz portatil, parlante inalambrico, bocina impermeable, bocina waterproof ip67, bocina bass potente, altavoz 16 horas, bocina alberca, bocina playa, bocina camping, bocina fiesta, bocina outdoor, bocina viaje, bocina regalo, bocina pequena, bocina economica, altavoz bluetooth 5.3, bocina con subwoofer, bocina estereo, bocina negra, bocina azul, bocina morada, bocina inalambrica.

Preguntanos lo que quieras antes de comprar. Respondemos en minutos."""

def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

cat_id="MLM59800"  # Bocinas Bluetooth
cat_attrs=get_cat_attrs(cat_id)

# Item-level attrs (sin BRAND/MODEL oficial - generico)
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
BAD={"EAN","UPC","MPN","SELLER_SKU","COLOR","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","LINE","ALPHANUMERIC_MODEL"}
for ca in cat_attrs:
    aid=ca.get("id"); tags=ca.get("tags") or {}
    req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
    if not req or aid in seen or aid in BAD: continue
    vals=ca.get("values") or []; vt=ca.get("value_type")
    if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
    elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
    else: attrs.append({"id":aid,"value_name":"No aplica"})
    seen.add(aid)

variations=[
    {"price":299,"available_quantity":1,"attribute_combinations":[{"id":"COLOR","value_name":"Negro"}],"picture_ids":pics_negro},
    {"price":299,"available_quantity":1,"attribute_combinations":[{"id":"COLOR","value_name":"Azul"}],"picture_ids":pics_azul},
    {"price":299,"available_quantity":1,"attribute_combinations":[{"id":"COLOR","value_name":"Morado"}],"picture_ids":pics_morado},
]

body={
    "site_id":"MLM","title":TITLE,"category_id":cat_id,"currency_id":"MXN",
    "condition":"new","listing_type_id":"gold_pro","buying_mode":"buy_it_now","catalog_listing":False,
    "pictures":[{"id":p} for p in pic_ids],
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
    bad=set(); miss=set()
    for c in j.get("cause",[]):
        msg=c.get("message","") or ""; code=c.get("code","") or ""
        if "missing" in code:
            for m_ in re.findall(r"\[([A-Z][A-Z_0-9]+)\]",msg):
                if m_.startswith("MLM") or m_ in BAD: continue
                miss.add(m_)
        if "invalid" in code or "omitted" in code or "ignored" in code:
            mm=re.search(r"[Aa]ttribute:?\s+([A-Z][A-Z_]+)",msg)
            if mm and not mm.group(1).startswith("MLM"): bad.add(mm.group(1))
            for m_ in re.findall(r"\[([A-Z][A-Z_0-9]+)\]",msg):
                if not m_.startswith("MLM"): bad.add(m_)
    print(f"  retry {retry} bad={bad} miss={miss}")
    if bad: attrs=[a for a in attrs if a["id"] not in bad]
    for mid in miss:
        if not any(a["id"]==mid for a in attrs):
            attrs.append({"id":mid,"value_name":"No aplica"})
    body["attributes"]=attrs
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)

if r.status_code in (200,201):
    resp=r.json()
    nid=resp.get("id")
    print(f"\n🎉 OK Publicacion creada: {nid}")
    # description
    requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":DESC},timeout=15)
    print(f"Variaciones:")
    for v in resp.get("variations",[]):
        ac=v.get("attribute_combinations",[])
        col=ac[0].get("value_name","") if ac else ""
        print(f"  {v.get('id')} {col}: ${v.get('price')} qty={v.get('available_quantity')} pics={len(v.get('picture_ids',[]))}")
    
    # Stock config
    try:
        with open("stock_config_asva.json") as f: sc=json.load(f)
    except: sc={}
    sc[nid]={
        "real_stock":460,
        "sku":"BOCINA-BT-IP67-ASVA",
        "label":"Bocina Bluetooth IP67 ASVA (3 colores)",
        "auto_replenish":True,
        "replenish_quantity":1,
        "min_visible_stock":1,
        "account":"asva",
        "variations":{"Negro":{"stock":179},"Azul":{"stock":82},"Morado":{"stock":202}}
    }
    with open("stock_config_asva.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
    print(f"\nstock_config_asva.json: {nid} stock_real=460")
else:
    print(f"\nERR: {r.json()}")
