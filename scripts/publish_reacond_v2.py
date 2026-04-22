import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Nota: Charge 6 Azul ya publicada MLM2880862569, skip
SKIP_LIST=[("Charge 6","Azul")]

PROD=[
    ("Flip 7","Negro",499,179),
    ("Flip 7","Azul",499,63),
    ("Flip 7","Morado",499,59),
    ("Flip 7","Rojo",499,35),
    ("Go 4","Negro",399,31),
    ("Clip 5","Negro",399,30),
    ("Charge 6","Rojo",699,22),
    ("Go 4","Rojo",399,19),
    ("Go 4","Camuflaje",399,12),
    ("Clip 5","Morado",399,11),
    ("Go 4","Rosa",399,10),
    ("Go 4","Azul",399,9),
    ("Grip","Negro",399,5),
    ("Go 3","Negro",399,5),
    ("Charge 6","Camuflaje",699,2),
    ("Charge 6","Negro",699,2),
    ("Bose Soundlink Home","Negro",1499,2),
]

SPEC={
    "Charge 6":{"bat":"28 horas","power":"40W","ip":"IP68","weight":"970 g","extras":"Entrada USB tipo C. Powerbank integrada."},
    "Flip 7":{"bat":"16 horas","power":"35W","ip":"IP68","weight":"560 g","extras":"Entrada USB tipo C. AI Sound Boost."},
    "Clip 5":{"bat":"12 horas","power":"7W","ip":"IP67","weight":"285 g","extras":"Mosqueton integrado."},
    "Grip":{"bat":"12 horas","power":"8W","ip":"IP68","weight":"400 g","extras":"Iluminacion LED."},
    "Go 4":{"bat":"7 horas","power":"4.2W","ip":"IP67","weight":"190 g","extras":"Correa integrada."},
    "Go 3":{"bat":"5 horas","power":"4.2W","ip":"IP67","weight":"209 g","extras":"Cuerda integrada."},
    "Bose Soundlink Home":{"bat":"AC","power":"45W","ip":"N/A","weight":"1.2 kg","extras":"Bluetooth 5.0, uso fijo."},
}

BLINDAJE="""

===== IMPORTANTE LEE ANTES DE COMPRAR =====

Producto REACONDICIONADO (no nuevo en caja sellada). Revisado, limpiado y probado. Puede presentar pequenas marcas cosmeticas.

POLITICA DE RECLAMOS:
- Aceptamos cambios solo por defecto de funcionamiento (no enciende, no pairea, no carga).
- NO aceptamos reclamos subjetivos sobre audio, estetica minima, comparaciones con retail o cambio de opinion.
- Toda devolucion requiere video sin cortes del desempaque desde Mercado Envios.

Al comprar aceptas estas condiciones."""

def seo_title(m,c):
    cx = c.replace("Negro","Negra").replace("Rojo","Roja").replace("Morado","Morada")
    tm={
        "Charge 6": f"Bocina Jbl Charge 6 Bluetooth Reacondicionada {cx} Usb-c",
        "Flip 7": f"Bocina Jbl Flip 7 Bluetooth Reacondicionada {cx} Usb-c",
        "Clip 5": f"Bocina Jbl Clip 5 Bluetooth Reacondicionada {cx} Portatil",
        "Grip": f"Bocina Jbl Grip Bluetooth Reacondicionada {cx} Luz Led",
        "Go 4": f"Bocina Jbl Go 4 Bluetooth Reacondicionada {cx} Ip67",
        "Go 3": f"Bocina Jbl Go 3 Bluetooth Reacondicionada {cx} Ip67",
        "Bose Soundlink Home": f"Bose Soundlink Home Bluetooth Reacondicionada {cx}",
    }
    return (tm.get(m,f"Bocina {m} Reacondicionada {cx}"))[:60]

def seo_desc(m,c):
    s=SPEC.get(m,{})
    usb=""
    if m in ("Charge 6","Flip 7"):
        usb = "\nAVISO: Entrada USB tipo C funcional. Version OEM sin licencia retail. NO compatible con app oficial JBL Portable. Funciona al 100% via Bluetooth.\n"
    return f"""Bocina {m} Bluetooth Portatil - Color {c} - REACONDICIONADA con Garantia
{usb}
CARACTERISTICAS: Sonido potente, bateria {s.get('bat','')}, {s.get('ip','')}, potencia {s.get('power','')}. {s.get('extras','')}

INCLUYE: Bocina + cable USB-C + caja generica de proteccion + factura.

ENVIO: GRATIS toda Mexico. Mismo dia antes 2PM. Entrega 24-72 hrs.

Garantia 30 dias contra defecto de funcionamiento.

PALABRAS CLAVE: bocina {m.lower()}, reacondicionada, altavoz bluetooth, parlante, {c.lower()}, economica, oem, waterproof, impermeable.
{BLINDAJE}"""

def search_best_cpid(q, must_have, must_not_have):
    r=requests.get(f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={q.replace(' ','+')}",headers=H,timeout=15).json()
    for it in r.get("results",[])[:10]:
        nm=(it.get("name") or "").lower()
        if any(b in nm for b in must_not_have): continue
        if all(g in nm for g in must_have):
            return it.get("id"), it.get("name")
    return None, None

def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

NUMSPEC={
    "Charge 6":{"bat":(28,"h"),"pwr":(40,"W"),"minf":(60,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
    "Flip 7":{"bat":(16,"h"),"pwr":(35,"W"),"minf":(60,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
    "Clip 5":{"bat":(12,"h"),"pwr":(7,"W"),"minf":(110,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
    "Grip":{"bat":(12,"h"),"pwr":(8,"W"),"minf":(110,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
    "Go 4":{"bat":(7,"h"),"pwr":(4.2,"W"),"minf":(180,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
    "Go 3":{"bat":(5,"h"),"pwr":(4.2,"W"),"minf":(110,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
    "Bose Soundlink Home":{"bat":(8,"h"),"pwr":(30,"W"),"minf":(50,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(18,"V")},
}
ATTR2KEY={"MAX_BATTERY_AUTONOMY":"bat","POWER_OUTPUT_RMS":"pwr","MAX_POWER":"pwr","MIN_FREQUENCY_RESPONSE":"minf","MAX_FREQUENCY_RESPONSE":"maxf","INPUT_IMPEDANCE":"imp","DISTORTION":"dis","BATTERY_VOLTAGE":"volt"}

def num_val(aid,model):
    k=ATTR2KEY.get(aid); sp=NUMSPEC.get(model,{})
    if k and k in sp: n,u=sp[k]; return f"{n} {u}"
    return None

def is_attr_id(s):
    """Distinguir attribute ID (BRAND, GTIN, etc) de categoria (MLMxxxx)"""
    if not s: return False
    if re.match(r'^MLM\d+$',s): return False
    return s.replace("_","").isupper() and s.isascii() and "_" in s or s.isupper()

def publish(model, color, price, stock_real):
    # Buscar cpid correcto
    if "Bose" in model:
        cpid,nm = search_best_cpid("Bose Soundlink Home",["bose","home"],["funda","case","cable","flex","micro","revolve","mini","color"])
    elif model=="Flip 7":
        color_search = {"Negro":"Negro","Azul":"Azul","Morado":"Morado Violeta","Rojo":"Rojo"}[color]
        cpid,nm = search_best_cpid(f"JBL Flip 7 {color_search}",["flip 7",color.lower().rstrip("o")],["flip 6","flip 5"])
        if not cpid:
            cpid,nm = search_best_cpid(f"JBL Flip 7 {color}",["flip 7"],["flip 6","flip 5","blanco"])
    elif model=="Charge 6":
        color_search = {"Rojo":"Rojo","Azul":"Azul","Camuflaje":"Camuflaje","Negro":"Negro"}[color]
        cpid,nm = search_best_cpid(f"JBL Charge 6 {color_search}",["charge 6"],["charge 5","charge 4"])
    elif model=="Clip 5":
        cpid,nm = search_best_cpid(f"JBL Clip 5 {color}",["clip 5"],["clip 4","clip 3"])
    elif model=="Grip":
        cpid,nm = search_best_cpid(f"JBL Grip {color}",["grip"],["flip","clip","bolsa"])
    elif model=="Go 4":
        cpid,nm = search_best_cpid(f"JBL Go 4 {color}",["go 4"],["go 3","go 2","funda"])
    elif model=="Go 3":
        cpid,nm = search_best_cpid(f"JBL Go 3 {color}",["go 3"],["go 2","go 4","funda"])
    else:
        cpid=None; nm=None
    
    cat_id="MLM59800"
    pics=[]
    if cpid:
        prod=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
        cat_id = prod.get("category_details",{}).get("id") or prod.get("category_id") or "MLM59800"
        pics = [p["url"] for p in (prod.get("pictures") or []) if p.get("url")]
    
    cat_attrs = get_cat_attrs(cat_id)
    
    # Attrs BASE (condition=used, sin ITEM_CONDITION, sin GTIN, sin PACKAGE_*)
    attrs=[
        {"id":"BRAND","value_name":"Bose" if "Bose" in model else "JBL"},
        {"id":"COLOR","value_name":color},
        {"id":"MODEL","value_name":model},
    ]
    seen={a["id"] for a in attrs}
    BAD_SET={"GTIN","EAN","UPC","MPN","SELLER_SKU","ITEM_CONDITION","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT"}
    
    for ca in cat_attrs:
        aid=ca.get("id"); tags=ca.get("tags") or {}
        req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
        if not req or aid in seen or aid in BAD_SET: continue
        nv=num_val(aid,model)
        if nv: attrs.append({"id":aid,"value_name":nv}); seen.add(aid); continue
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
                # regex que SOLO captura atributos (excluye MLMxxxx)
                for m_ in re.findall(r"\[([A-Z][A-Z_0-9]+)\]",msg):
                    if m_.startswith("MLM"): continue
                    if not re.match(r'^[A-Z][A-Z_]+$',m_): continue
                    if m_ not in BAD_SET:
                        miss.add(m_)
            if "attributes.invalid" in code:
                mm=re.search(r"Attribute:?\s+([A-Z][A-Z_]+)",msg)
                if mm and not mm.group(1).startswith("MLM"): bad.add(mm.group(1))
        if bad: attrs=[a for a in attrs if a["id"] not in bad]
        for mid in miss:
            if not any(a["id"]==mid for a in attrs):
                nv=num_val(mid,model)
                if nv: attrs.append({"id":mid,"value_name":nv})
                elif mid=="GTIN":
                    # NO usar "No aplica" - mejor omitir
                    continue
                elif mid in ("RAM_MEMORY","INTERNAL_MEMORY"):
                    for ca in cat_attrs:
                        if ca.get("id")==mid:
                            vs=ca.get("values") or []
                            if vs: attrs.append({"id":mid,"value_id":vs[0]["id"],"value_name":vs[0].get("name","")})
                            break
                else: attrs.append({"id":mid,"value_name":"No aplica"})
        body["attributes"]=attrs
        r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    
    if r.status_code in (200,201):
        nid=r.json().get("id")
        requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":seo_desc(model,color)},timeout=15)
        return nid, None
    return None, str(r.json())[:500]

# Cargar stock_config.json existente
try:
    with open("stock_config.json") as f: sc=json.load(f)
except: sc={}

results=[]
for model,color,price,stock_real in PROD:
    if (model,color) in SKIP_LIST:
        print(f"SKIP {model} {color} (ya publicada)")
        continue
    print(f"\n=== {model} {color} ${price} stock={stock_real} ===")
    nid,err=publish(model,color,price,stock_real)
    if nid:
        print(f"  OK -> {nid}")
        sc[nid]={
            "real_stock": stock_real,
            "sku": f"REACOND-{model.replace(' ','')}-{color.upper()}",
            "label": f"{model} {color} Reacondicionada",
            "auto_replenish": True,
            "replenish_quantity": 1,
            "min_visible_stock": 1
        }
    else:
        print(f"  ERR: {err[:250]}")
    results.append({"model":model,"color":color,"price":price,"stock":stock_real,"new_id":nid,"err":err})
    time.sleep(2)

with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)

print("\n=== RESUMEN ===")
ok=sum(1 for r in results if r["new_id"])
print(f"{ok}/{len(results)} publicadas")
for r in results:
    if r["new_id"]: print(f"  OK {r['new_id']} | {r['model']} {r['color']} | ${r['price']} | stock {r['stock']}")
    else: print(f"  FAIL | {r['model']} {r['color']}")
