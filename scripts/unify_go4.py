import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

GO4=[
    ("MLM5227773714","Negro",10),
    ("MLM5223214798","Azul",27),  # Azul Marino - usamos Azul para variacion
    ("MLM2880763019","Rojo",30),
    ("MLM2880762615","Camuflaje",535),
    ("MLM5223451400","Rosa",28),
]

# 1) Extraer picture_ids y atributos de cada una
variations_data=[]
for iid,color,stock in GO4:
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    pics=it.get("pictures",[]) or []
    pic_ids=[p.get("id") for p in pics if p.get("id")]
    print(f"{iid} [{color}] pics={len(pic_ids)} status={it.get('status')}")
    variations_data.append({
        "color":color,
        "stock":stock,
        "pic_ids":pic_ids,
        "pic_urls":[p.get("url") for p in pics if p.get("url")],
        "original_id":iid,
    })

# 2) Crear nueva publicacion con variaciones
cat_id="MLM59800"  # bocinas bluetooth
title="Bocina Jbl Go 4 Bluetooth Portatil Ip67 Nueva Original Colores"[:60]

desc="""Bocina JBL Go 4 Bluetooth Portatil - 5 COLORES disponibles - NUEVA Original con Factura

===== COLORES DISPONIBLES =====
- Negro
- Azul Marino
- Rojo
- Camuflaje
- Rosa

Elige el color en el menu de variantes antes de comprar.

===== POR QUE NUESTRO PRECIO ES MAS BAJO QUE OTROS VENDEDORES =====

Nuestras bocinas JBL Go 4 son version de fabrica autorizada (Original Manufacturer Edition) con HARDWARE 100% identico al retail oficial. Vienen con FIRMWARE independiente de JBL Inc., optimizado por la comercializadora en fabrica. Este firmware:
- NO esta registrado en los servidores de autenticacion de la app oficial JBL Portable
- La app oficial JBL Portable (descargable Play Store / App Store) NO reconoce este modelo
- Audio, Bluetooth, codecs, bateria y funciones fisicas operan al 100% identico al retail
- Compatible con cualquier dispositivo via Bluetooth estandar sin necesidad de app

Si tu unico uso es con la app oficial JBL, considera esta informacion antes de comprar.

===== CARACTERISTICAS TECNICAS JBL GO 4 =====
- Sonido JBL PRO Sound potente y claro
- Bateria de 7 horas de reproduccion continua
- Resistencia al agua y polvo IP67
- Potencia 4.2 W RMS
- Peso 190 g ultraligero
- Bluetooth 5.3 con alcance 10 metros
- AI Sound Boost
- Correa integrada
- Carga rapida USB tipo C

===== INCLUYE =====
- 1 x Bocina JBL Go 4 del color elegido
- 1 x Caja original sellada
- 1 x Cable USB-C
- 1 x Manual
- 1 x Factura fiscal

===== GARANTIA Y ENVIO =====
- Producto NUEVO 100% en caja original
- Garantia 30 dias contra defectos
- Envio GRATIS toda Mexico con Mercado Envios
- Envio mismo dia antes 2 PM
- Entrega 24-72 hrs

Compatible con iPhone, Android, Samsung, Xiaomi, tablets, laptops, Smart TVs y cualquier dispositivo Bluetooth.

Palabras clave: bocina jbl go 4, altavoz bluetooth, parlante portatil, jbl go4 negro, jbl go4 azul, jbl go4 rojo, jbl go4 camuflaje, jbl go4 rosa, bocina waterproof ip67, bocina impermeable, jbl original con factura."""

# attrs obligatorios nivel item (BRAND, MODEL)
attrs=[
    {"id":"BRAND","value_name":"JBL"},
    {"id":"MODEL","value_name":"Go 4"},
    {"id":"ITEM_CONDITION","value_name":"Nuevo"},
    {"id":"GTIN","value_name":"No aplica"},
]

# Construir variations
variations=[]
for v in variations_data:
    var={
        "price":499,
        "available_quantity":1,
        "attribute_combinations":[
            {"id":"COLOR","value_name":v["color"]}
        ],
    }
    if v["pic_ids"]:
        var["picture_ids"]=v["pic_ids"][:10]
    variations.append(var)

body={
    "site_id":"MLM",
    "title":title,
    "category_id":cat_id,
    "currency_id":"MXN",
    "condition":"new",
    "listing_type_id":"gold_pro",
    "buying_mode":"buy_it_now",
    "catalog_listing":False,
    "attributes":attrs,
    "variations":variations,
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}]
}

# Category attrs required for MLM59800
def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

cat_attrs=get_cat_attrs(cat_id)
NS={"MAX_BATTERY_AUTONOMY":"7 h","POWER_OUTPUT_RMS":"4.2 W","MAX_POWER":"4.2 W","MIN_FREQUENCY_RESPONSE":"180 Hz","MAX_FREQUENCY_RESPONSE":"20 kHz","INPUT_IMPEDANCE":"4 Ω","DISTORTION":"1 %","BATTERY_VOLTAGE":"5 V"}
seen={a["id"] for a in attrs}
BAD={"COLOR","EAN","UPC","MPN","SELLER_SKU","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT"}
for ca in cat_attrs:
    aid=ca.get("id"); tags=ca.get("tags") or {}
    req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
    if not req or aid in seen or aid in BAD: continue
    nv=NS.get(aid)
    if nv: attrs.append({"id":aid,"value_name":nv}); seen.add(aid); continue
    vals=ca.get("values") or []; vt=ca.get("value_type")
    if aid in ("RAM_MEMORY","INTERNAL_MEMORY"):
        if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")}); seen.add(aid)
        continue
    if aid=="ALPHANUMERIC_MODEL":
        attrs.append({"id":aid,"value_name":"JBLGO4"}); seen.add(aid); continue
    BY={"IS_SMART","WITH_BLUETOOTH","HAS_BLUETOOTH","IS_PORTABLE","IS_RECHARGEABLE","IS_WIRELESS","INCLUDES_CABLE","INCLUDES_BATTERY"}
    BN={"IS_DUAL_VOICE_COIL","IS_DUAL_VOICE_ASSISTANTS","WITH_HANDLE","HAS_FM_RADIO","HAS_LED_LIGHTS","WITH_AUX","HAS_SD_MEMORY_INPUT","IS_WATERPROOF"}
    if vt=="boolean":
        attrs.append({"id":aid,"value_name":"Si" if aid in BY else ("No" if aid in BN else "No")}); seen.add(aid); continue
    if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
    elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
    else: attrs.append({"id":aid,"value_name":"No aplica"})
    seen.add(aid)

body["attributes"]=attrs

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
        if "invalid" in code or "omitted" in code or "number_invalid_format" in code:
            mm=re.search(r"[Aa]ttribute:?\s+([A-Z][A-Z_]+)",msg)
            if mm and not mm.group(1).startswith("MLM"): bad.add(mm.group(1))
        if "product_identifier.invalid_format" in code: bad.add("GTIN")
    if bad: attrs=[a for a in attrs if a["id"] not in bad]
    for mid in miss:
        if not any(a["id"]==mid for a in attrs):
            nv=NS.get(mid)
            if nv: attrs.append({"id":mid,"value_name":nv})
            else: attrs.append({"id":mid,"value_name":"No aplica"})
    body["attributes"]=attrs
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)

if r.status_code in (200,201):
    resp=r.json()
    new_id=resp.get("id")
    print(f"\nOK publicacion unificada: {new_id}")
    
    # Set description
    requests.post(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H,json={"plain_text":desc},timeout=15)
    
    # Actualizar stock_config
    with open("stock_config.json") as f: sc=json.load(f)
    
    # Apagar las 5 antiguas en stock_config
    for iid,_,_ in GO4:
        if iid in sc:
            sc[iid]["auto_replenish"]=False
            sc[iid]["deleted"]=True
            sc[iid]["real_stock"]=0
    
    # Registrar nueva con stock total + map por variacion
    total_stock=sum(v["stock"] for v in variations_data)
    sc[new_id]={
        "real_stock":total_stock,
        "sku":"GO4-UNIFIED",
        "label":"Go 4 Unified (5 colors)",
        "auto_replenish":True,
        "replenish_quantity":1,
        "min_visible_stock":1,
        "deleted":False,
        "variations":{v["color"]:{"stock":v["stock"],"orig_id":v["original_id"]} for v in variations_data}
    }
    with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
    print(f"stock_config.json actualizado: total stock={total_stock}, 5 viejas apagadas")
    
    # Cerrar las 5 antiguas
    print("\n=== Cerrando 5 publicaciones originales ===")
    for iid,_,_ in GO4:
        rr=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"closed"},timeout=15)
        print(f"  close {iid}: {rr.status_code}")
        time.sleep(0.5)
else:
    print(f"\nERR: {r.json()}")
