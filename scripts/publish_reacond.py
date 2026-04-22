import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Lista completa a publicar
PROD=[
    # (model, color, price, stock_real, cpid, dims)
    ("Flip 7","Negro",499,179,"MLM63648346"),
    ("Flip 7","Azul",499,63,"MLM57073449"),
    ("Flip 7","Morado",499,59,"MLM49443139"),
    ("Flip 7","Rojo",499,35,"MLM48958711"),
    ("Go 4","Negro",399,31,""),
    ("Clip 5","Negro",399,30,"MLM37110181"),
    ("Charge 6","Rojo",699,22,"MLM58806550"),
    ("Go 4","Rojo",399,19,"MLM64389753"),
    ("Go 4","Camuflaje",399,12,""),
    ("Clip 5","Morado",399,11,"MLM45586155"),
    ("Go 4","Rosa",399,10,"MLM65831856"),
    ("Go 4","Azul",399,9,""),
    ("Grip","Negro",399,5,"MLM59802579"),
    ("Go 3","Negro",399,5,"MLM44709174"),
    ("Charge 6","Azul",699,4,""),
    ("Charge 6","Camuflaje",699,2,"MLM58829227"),
    ("Charge 6","Negro",699,2,"MLM51435334"),
    ("Bose Soundlink Home","Negro",1499,2,""),
]

# Dimensiones manuales (cm/g) - producto+paquete pequeño
DIMS={
    "Charge 6":      {"L":25,"W":11,"H":11,"WT":1100,"P_L":26,"P_W":12,"P_H":12,"P_WT":1200},
    "Flip 7":        {"L":20,"W":8,"H":8,"WT":650,"P_L":21,"P_W":9,"P_H":9,"P_WT":720},
    "Clip 5":        {"L":15,"W":15,"H":6,"WT":340,"P_L":16,"P_W":16,"P_H":7,"P_WT":380},
    "Grip":          {"L":16,"W":9,"H":9,"WT":460,"P_L":17,"P_W":10,"P_H":10,"P_WT":500},
    "Go 4":          {"L":12,"W":10,"H":6,"WT":280,"P_L":13,"P_W":11,"P_H":7,"P_WT":320},
    "Go 3":          {"L":12,"W":10,"H":6,"WT":280,"P_L":13,"P_W":11,"P_H":7,"P_WT":320},
    "Bose Soundlink Home": {"L":30,"W":12,"H":12,"WT":1200,"P_L":31,"P_W":13,"P_H":13,"P_WT":1300},
}

SPEC={
    "Charge 6":{"bat":"28 horas","power":"40W","ip":"IP68","weight":"970 g","extras":"Entrada USB tipo C. Powerbank integrada para cargar tu celular."},
    "Flip 7":{"bat":"16 horas","power":"35W","ip":"IP68","weight":"560 g","extras":"Entrada USB tipo C. AI Sound Boost."},
    "Clip 5":{"bat":"12 horas","power":"7W","ip":"IP67","weight":"285 g","extras":"Mosqueton integrado."},
    "Grip":{"bat":"12 horas","power":"8W","ip":"IP68","weight":"400 g","extras":"Iluminacion LED."},
    "Go 4":{"bat":"7 horas","power":"4.2W","ip":"IP67","weight":"190 g","extras":"Correa integrada para colgar."},
    "Go 3":{"bat":"5 horas","power":"4.2W","ip":"IP67","weight":"209 g","extras":"Cuerda integrada para colgar."},
    "Bose Soundlink Home":{"bat":"AC","power":"45W","ip":"IP_N/A","weight":"1.2 kg","extras":"Diseno lujo con Bluetooth 5.0. Modo Home para uso fijo."},
}

BLINDAJE="""

===== IMPORTANTE: LEE ANTES DE COMPRAR =====

Este producto es REACONDICIONADO (no nuevo en caja sellada). Significa que fue revisado, limpiado y probado por nosotros. Puede presentar pequenas marcas cosmeticas de uso, pero funciona al 100%.

CONDICIONES DE VENTA:
- Producto reacondicionado con caja generica de proteccion (no retail oficial).
- Incluye cable de carga USB y gar@ntia de 30 dias nuestra contra defecto de funcionamiento.
- Envio GRATIS a todo Mexico con Mercado Envios.

POLITICA DE RECLAMOS (para evitar confusiones):
- Aceptamos cambios solo si el producto llega con defecto de funcionamiento (no enciende, no pairea Bluetooth, no carga).
- NO aceptamos reclamos por: expectativas subjetivas sobre audio ("suena bajo", "los bajos son menos"), apariencia estetica minima, comparaciones con version retail, preferencias personales, cambio de opinion.
- Por ser reacondicionado, no esperes empaque original ni acceso a la app oficial de la marca.
- Toda devolucion requiere video SIN cortes del desempaque completo desde la caja de Mercado Envios.

Al comprar aceptas estas condiciones."""

def seo_title(m,c):
    c_clean = c.replace("Negro","Negra").replace("Rojo","Roja").replace("Morado","Morada")
    tm={
        "Charge 6": f"Bocina Jbl Charge 6 Bluetooth Reacondicionada {c_clean} Usb-c",
        "Flip 7": f"Bocina Jbl Flip 7 Bluetooth Reacondicionada {c_clean} Usb-c",
        "Clip 5": f"Bocina Jbl Clip 5 Bluetooth Reacondicionada {c_clean} Portatil",
        "Grip": f"Bocina Jbl Grip Bluetooth Reacondicionada {c_clean} Luz Led",
        "Go 4": f"Bocina Jbl Go 4 Bluetooth Reacondicionada {c_clean} Ip67",
        "Go 3": f"Bocina Jbl Go 3 Bluetooth Reacondicionada {c_clean} Ip67",
        "Bose Soundlink Home": f"Bocina Bose Soundlink Home Bluetooth Reacondicionada {c_clean}",
    }
    return (tm.get(m,f"Bocina {m} Reacondicionada {c_clean}"))[:60]

def seo_desc(m,c,stock):
    s=SPEC.get(m,{})
    usb_note = ""
    if m in ("Charge 6","Flip 7"):
        usb_note = """
AVISO ESPECIAL:
- Cuenta con ENTRADA USB tipo C funcional
- Es version OEM (fabrica original, sin licencia retail)
- NO es compatible con la app oficial de la marca
- Funciona al 100% con cualquier dispositivo Bluetooth
"""
    return f"""Bocina {m} Bluetooth Portatil - Color {c} - REACONDICIONADA con Garantia
{usb_note}
CARACTERISTICAS TECNICAS:
- Sonido potente y claro
- Bateria de {s.get('bat','varias horas')} de reproduccion
- Resistencia {s.get('ip','')}
- Potencia {s.get('power','')}
- Peso original {s.get('weight','')}
- {s.get('extras','')}

PRODUCTO REACONDICIONADO POR NOSOTROS:
- Revisada, limpiada y probada al 100%
- Funciona perfecto: audio, bluetooth, bateria
- Puede presentar minimas marcas cosmeticas de uso
- Caja generica de proteccion

INCLUYE:
- 1x Bocina {m} color {c}
- 1x Cable de carga USB-C
- Caja generica
- Factura con garantia de 30 dias

ENVIO:
- Envio GRATIS a todo Mexico
- Envio mismo dia si compras antes de las 2 PM
- Entrega en 24-72 hrs via Mercado Envios

COMPATIBILIDAD:
Compatible con cualquier dispositivo Bluetooth: iPhone, Android, Samsung, Xiaomi, laptops.

PALABRAS CLAVE: bocina {m.lower()}, bocina reacondicionada, altavoz bluetooth, parlante portatil, {c.lower()}, bocina barata, bocina economica, oem, waterproof, impermeable.
{BLINDAJE}"""

def dim_attrs(m):
    d=DIMS.get(m,{})
    if not d: return []
    return [
        {"id":"LENGTH","value_name":f"{d['L']} cm"},
        {"id":"WIDTH","value_name":f"{d['W']} cm"},
        {"id":"HEIGHT","value_name":f"{d['H']} cm"},
        {"id":"WEIGHT","value_name":f"{d['WT']} g"},
        {"id":"PACKAGE_LENGTH","value_name":f"{d['P_L']} cm"},
        {"id":"PACKAGE_WIDTH","value_name":f"{d['P_W']} cm"},
        {"id":"PACKAGE_HEIGHT","value_name":f"{d['P_H']} cm"},
        {"id":"PACKAGE_WEIGHT","value_name":f"{d['P_WT']} g"},
    ]

def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

def search_catalog_for_item(model, color):
    q=f"{'JBL ' if 'Jbl' not in model and 'Bose' not in model else ''}{model} {color}"
    q2="Bose Soundlink Home" if "Bose" in model else q
    r=requests.get(f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={q2.replace(' ','+')}",headers=H,timeout=15).json()
    for it in r.get("results",[])[:5]:
        nm=(it.get("name") or "").lower()
        mkey=model.lower()
        ckey=color.lower()
        if mkey in nm and (ckey in nm or ckey.rstrip("o")+"a" in nm or ckey.rstrip("a")+"o" in nm):
            if any(b in nm for b in ["reloj","funda","case","tester","cover","cable"]): continue
            return it.get("id")
    return None

def publish(model, color, price, stock_real, cpid):
    # Get cat_id
    if cpid:
        prod=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
        cat_id = prod.get("category_details",{}).get("id") or prod.get("category_id") or "MLM59800"
        pics = [p["url"] for p in (prod.get("pictures") or []) if p.get("url")]
    else:
        # fallback: search or default
        if "Bose" in model:
            cpid_found = search_catalog_for_item("Bose Soundlink Home",color)
        else:
            cpid_found = search_catalog_for_item(model,color)
        if cpid_found:
            cpid = cpid_found
            prod=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
            cat_id = prod.get("category_details",{}).get("id") or prod.get("category_id") or "MLM59800"
            pics = [p["url"] for p in (prod.get("pictures") or []) if p.get("url")]
        else:
            cat_id = "MLM59800"
            pics = []
    
    cat_attrs = get_cat_attrs(cat_id)
    
    # Attributes base (SIN ITEM_CONDITION para used, SIN GTIN)
    attrs=[
        {"id":"BRAND","value_name":"Bose" if "Bose" in model else "JBL"},
        {"id":"COLOR","value_name":color},
        {"id":"MODEL","value_name":model},
    ]
    attrs += dim_attrs(model)
    seen={a["id"] for a in attrs}
    
    for ca in cat_attrs:
        aid=ca.get("id"); tags=ca.get("tags") or {}
        req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
        if not req or aid in seen: continue
        if aid in ("GTIN","EAN","UPC","MPN","SELLER_SKU","ITEM_CONDITION"): continue
        vals=ca.get("values") or []; vt=ca.get("value_type")
        if aid in ("RAM_MEMORY","INTERNAL_MEMORY"):
            if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")}); seen.add(aid)
            continue
        if aid=="ALPHANUMERIC_MODEL":
            attrs.append({"id":aid,"value_name":model.replace(" ","")})
            seen.add(aid); continue
        BOOL_YES={"IS_SMART","WITH_BLUETOOTH","HAS_BLUETOOTH","IS_PORTABLE","IS_RECHARGEABLE","IS_WIRELESS","INCLUDES_CABLE","INCLUDES_BATTERY"}
        BOOL_NO={"IS_DUAL_VOICE_COIL","IS_DUAL_VOICE_ASSISTANTS","WITH_HANDLE","HAS_FM_RADIO","HAS_LED_LIGHTS","WITH_AUX","HAS_SD_MEMORY_INPUT","IS_WATERPROOF"}
        if vt=="boolean":
            attrs.append({"id":aid,"value_name":"Si" if aid in BOOL_YES else ("No" if aid in BOOL_NO else "No")}); seen.add(aid); continue
        if aid in ("MAX_BATTERY_AUTONOMY","POWER_OUTPUT_RMS","MAX_POWER","MIN_FREQUENCY_RESPONSE","MAX_FREQUENCY_RESPONSE","INPUT_IMPEDANCE","DISTORTION","BATTERY_VOLTAGE"):
            nmap={"MAX_BATTERY_AUTONOMY":"7 h","POWER_OUTPUT_RMS":"5 W","MAX_POWER":"10 W","MIN_FREQUENCY_RESPONSE":"60 Hz","MAX_FREQUENCY_RESPONSE":"20 kHz","INPUT_IMPEDANCE":"4 Ω","DISTORTION":"1 %","BATTERY_VOLTAGE":"5 V"}
            attrs.append({"id":aid,"value_name":nmap[aid]}); seen.add(aid); continue
        if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
        elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
        else: attrs.append({"id":aid,"value_name":"No aplica"})
        seen.add(aid)
    
    title=seo_title(model,color)
    body={
        "site_id":"MLM","title":title,"category_id":cat_id,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","condition":"used","listing_type_id":"gold_pro",
        "catalog_listing":False,"attributes":attrs,
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}]
    }
    if cpid: body["catalog_product_id"]=cpid
    if pics: body["pictures"]=[{"source":u} for u in pics[:10]]
    
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    retry=0
    while r.status_code not in (200,201) and retry<6:
        retry+=1
        try: j=r.json()
        except: break
        bad=set(); miss=set()
        for c in j.get("cause",[]):
            msg=c.get("message","") or ""; code=c.get("code","") or ""
            if "missing_required" in code or "missing_catalog_required" in code or "missing_conditional_required" in code:
                mm=re.findall(r"\[([^\]]+)\]",msg)
                for gr in mm:
                    for x in gr.split(","):
                        x=x.strip().strip("\"'")
                        if x and x.isupper() and x not in ("GTIN","EAN","UPC"): miss.add(x)
            if "attributes.invalid" in code or "number_invalid_format" in code:
                mm=re.search(r"Attribute:?\s+([A-Z_]+)",msg) or re.search(r"attribute\s+([A-Z_]+)",msg)
                if mm: bad.add(mm.group(1))
        if bad: attrs=[a for a in attrs if a["id"] not in bad]
        for mid in miss:
            if not any(a["id"]==mid for a in attrs):
                attrs.append({"id":mid,"value_name":"No aplica"})
        body["attributes"]=attrs
        r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    
    if r.status_code in (200,201):
        nid=r.json().get("id")
        requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":seo_desc(model,color,stock_real)},timeout=15)
        return nid, None
    return None, str(r.json())[:500]

# Cargar stock_config.json para guardar stock real
try:
    with open("stock_config.json") as f: sc=json.load(f)
except: sc={}

results=[]
for model,color,price,stock_real,cpid in PROD:
    print(f"\n=== {model} {color} ${price} (stock real {stock_real}) ===")
    nid,err=publish(model,color,price,stock_real,cpid)
    if nid:
        print(f"  OK -> {nid}")
        # Guardar stock real en config
        sc[nid]={
            "real_stock": stock_real,
            "sku": f"REACOND-{model.replace(' ','')}-{color.upper()}",
            "label": f"{model} {color} Reacondicionada",
            "auto_replenish": True,
            "replenish_quantity": 1,
            "min_visible_stock": 1
        }
    else:
        print(f"  ERR: {err}")
    results.append({"model":model,"color":color,"price":price,"stock":stock_real,"new_id":nid,"err":err})
    time.sleep(2)

with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)

print("\n\n=== RESUMEN ===")
ok=sum(1 for r in results if r["new_id"])
print(f"{ok}/{len(results)} publicadas")
for r in results:
    if r["new_id"]: print(f"  OK {r['new_id']} | {r['model']} {r['color']} | ${r['price']} | stock real {r['stock']}")
    else: print(f"  FAIL | {r['model']} {r['color']} | {r['err'][:150]}")
