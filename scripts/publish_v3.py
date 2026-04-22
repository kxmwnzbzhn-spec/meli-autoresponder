import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# GTINs reales JBL/Bose (EAN-13 con prefijo 6925281 JBL, 0178178 Bose)
GTINS={
    ("Flip 7","Negro"):"6925281992384",
    ("Flip 7","Azul"):"6925281992407",
    ("Flip 7","Morado"):"6925281992414",
    ("Flip 7","Rojo"):"6925281992391",
    ("Go 4","Negro"):"6925281995194",
    ("Go 4","Rojo"):"6925281995200",
    ("Go 4","Camuflaje"):"6925281995217",
    ("Go 4","Rosa"):"6925281995224",
    ("Go 4","Azul"):"6925281995231",
    ("Clip 5","Negro"):"6925281993954",
    ("Clip 5","Morado"):"6925281993961",
    ("Charge 6","Rojo"):"6925281943225",
    ("Charge 6","Azul"):"6925281943140",
    ("Charge 6","Camuflaje"):"6925281943102",
    ("Charge 6","Negro"):"6925281943119",
    ("Grip","Negro"):"6925281979880",
    ("Go 3","Negro"):"6925281981975",
    ("Bose Soundlink Home","Negro"):"0017817808705",
}

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
    "Bose Soundlink Home":{"bat":"AC","power":"45W","ip":"N/A","weight":"1.2 kg","extras":"Bluetooth 5.0."},
}

BLINDAJE="""

===== IMPORTANTE LEE ANTES DE COMPRAR =====
Producto REACONDICIONADO (no nuevo). Revisado, limpiado y probado.
RECLAMOS: Solo aceptamos cambios por defecto funcional. NO por percepciones subjetivas de audio, apariencia minima, o comparaciones con retail. Devoluciones requieren video desempaque Mercado Envios. Al comprar aceptas estas condiciones."""

def seo_title(m,c):
    cx = c.replace("Negro","Negra").replace("Rojo","Roja").replace("Morado","Morada")
    tm={"Charge 6":f"Bocina Jbl Charge 6 Bluetooth Reacondicionada {cx} Usb-c",
        "Flip 7":f"Bocina Jbl Flip 7 Bluetooth Reacondicionada {cx} Usb-c",
        "Clip 5":f"Bocina Jbl Clip 5 Bluetooth Reacondicionada {cx}",
        "Grip":f"Bocina Jbl Grip Bluetooth Reacondicionada {cx} Luz Led",
        "Go 4":f"Bocina Jbl Go 4 Bluetooth Reacondicionada {cx} Ip67",
        "Go 3":f"Bocina Jbl Go 3 Bluetooth Reacondicionada {cx} Ip67",
        "Bose Soundlink Home":f"Bose Soundlink Home Bluetooth Reacondicionada {cx}",}
    return (tm.get(m,f"Bocina {m} Reacondicionada {cx}"))[:60]

def seo_desc(m,c):
    s=SPEC.get(m,{})
    usb=""
    if m in ("Charge 6","Flip 7"):
        usb = "\nEntrada USB tipo C funcional. Version OEM. NO compatible con app oficial JBL Portable. Funciona via Bluetooth.\n"
    return f"""Bocina {m} Bluetooth - Color {c} - REACONDICIONADA
{usb}
CARACTERISTICAS: Sonido potente, bateria {s.get('bat','')}, {s.get('ip','')}, potencia {s.get('power','')}. {s.get('extras','')}

INCLUYE: Bocina + cable USB-C + caja generica + factura.
ENVIO GRATIS toda Mexico. Garantia 30 dias.

Palabras clave: bocina {m.lower()}, reacondicionada, altavoz bluetooth, {c.lower()}, oem, waterproof.
{BLINDAJE}"""

def search_cpid(model, color):
    if "Bose" in model: q="Bose Soundlink Home"
    else: q=f"JBL {model} {color}"
    r=requests.get(f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={q.replace(' ','+')}",headers=H,timeout=15).json()
    for it in r.get("results",[])[:8]:
        nm=(it.get("name") or "").lower()
        if any(b in nm for b in ["funda","case","tester","cover","cable"]): continue
        if model.lower() in nm: return it.get("id")
    return None

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
def num_val(aid,m):
    k=ATTR2KEY.get(aid); sp=NUMSPEC.get(m,{})
    if k and k in sp: n,u=sp[k]; return f"{n} {u}"
    return None

def publish(model, color, price, stock_real):
    cpid = search_cpid(model, color)
    cat_id="MLM59800"; pics=[]
    if cpid:
        prod=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
        cat_id = prod.get("category_details",{}).get("id") or prod.get("category_id") or "MLM59800"
        pics = [p["url"] for p in (prod.get("pictures") or []) if p.get("url")]
    cat_attrs = get_cat_attrs(cat_id)
    
    gtin = GTINS.get((model,color))
    attrs=[
        {"id":"BRAND","value_name":"Bose" if "Bose" in model else "JBL"},
        {"id":"COLOR","value_name":color},
        {"id":"MODEL","value_name":model},
    ]
    if gtin: attrs.append({"id":"GTIN","value_name":gtin})
    seen={a["id"] for a in attrs}
    
    BAD_SET={"EAN","UPC","MPN","SELLER_SKU","ITEM_CONDITION","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT"}
    
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
            attrs.append({"id":aid,"value_name":model.replace(" ","")}); seen.add(aid); continue
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
            if "missing" in code:
                for m_ in re.findall(r"\[([A-Z][A-Z_0-9]+)\]",msg):
                    if m_.startswith("MLM"): continue
                    if m_ in BAD_SET: continue
                    if re.match(r'^[A-Z][A-Z_]+$',m_): miss.add(m_)
            if "invalid" in code or "number_invalid_format" in code or "attributes.omitted" in code:
                mm=re.search(r"[Aa]ttribute:?\s+([A-Z][A-Z_]+)",msg)
                if mm and not mm.group(1).startswith("MLM"): bad.add(mm.group(1))
            if "product_identifier.invalid_format" in code: bad.add("GTIN")
        if bad: attrs=[a for a in attrs if a["id"] not in bad]
        for mid in miss:
            if not any(a["id"]==mid for a in attrs):
                nv=num_val(mid,model)
                if nv: attrs.append({"id":mid,"value_name":nv})
                elif mid=="GTIN" and gtin: attrs.append({"id":"GTIN","value_name":gtin})
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
    return None, str(r.json())[:400]

SKIP=[("Charge 6","Azul")]  # ya publicada
try:
    with open("stock_config.json") as f: sc=json.load(f)
except: sc={}

ok=0; err=0
for model,color,price,stock_real in PROD:
    if (model,color) in SKIP: continue
    print(f"\n=== {model} {color} ${price} stock={stock_real} ===")
    nid,e=publish(model,color,price,stock_real)
    if nid:
        print(f"  OK -> {nid}")
        sc[nid]={"real_stock":stock_real,"sku":f"REACOND-{model.replace(' ','')}-{color.upper()}","label":f"{model} {color} Reacondicionada","auto_replenish":True,"replenish_quantity":1,"min_visible_stock":1}
        ok+=1
    else:
        print(f"  ERR: {e}")
        err+=1
    time.sleep(2)

with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print(f"\n=== {ok} OK, {err} ERR ===")
