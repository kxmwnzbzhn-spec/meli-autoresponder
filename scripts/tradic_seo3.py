import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Quedan 12 por hacer (Grip Negra ya se creo MLM2880794089)
SRC=[
    ("MLM2880754323","Go 3","Negra",469),
    ("MLM2880758735","Charge 6","Roja",919),
    ("MLM2880758747","Clip 5","Morada",719),
    ("MLM2880766021","Flip 7","Roja",819),
    ("MLM5222936976","Charge 6","Azul",919),
    ("MLM5222983008","Charge 6","Camuflaje",919),
    ("MLM5222983106","Go Essential 2","Azul",469),
    ("MLM5222983110","Go Essential 2","Roja",469),
    ("MLM5222983148","Go 4","Camuflaje",469),
    ("MLM5222987710","Go 4","Roja",469),
    ("MLM5222987718","Go 4","Azul Marino",469),
    ("MLM5222987720","Go 4","Rosa",469),
]

def seo_title(m, c):
    tm={
        "Charge 6": f"Bocina Jbl Charge 6 Bluetooth Portatil {c} Ip68 Nueva",
        "Flip 7":   f"Bocina Jbl Flip 7 Bluetooth Portatil {c} Ip68 Nueva",
        "Clip 5":   f"Bocina Jbl Clip 5 Bluetooth Portatil {c} Ip67 Nueva",
        "Grip":     f"Bocina Jbl Grip Bluetooth Portatil {c} Luz Led Nueva",
        "Go 4":     f"Bocina Jbl Go 4 Bluetooth Portatil {c} Ip67 Nueva",
        "Go Essential 2": f"Jbl Go Essential 2 Bluetooth Portatil {c} Ip67",
        "Go 3":     f"Bocina Jbl Go 3 Bluetooth Portatil {c} Ip67 Nueva",
    }
    return tm.get(m,f"Bocina Jbl {m} Bluetooth Portatil {c} Nueva")[:60]

SPEC={
    "Charge 6": {"bat":"28 horas","power":"40W","ip":"IP68","weight":"970 g","extras":"Powerbank integrada. AURACAST multi-bocina."},
    "Flip 7":   {"bat":"16 horas","power":"35W","ip":"IP68","weight":"560 g","extras":"AI Sound Boost. AURACAST."},
    "Clip 5":   {"bat":"12 horas","power":"7W","ip":"IP67","weight":"285 g","extras":"Mosqueton integrado. AURACAST."},
    "Grip":     {"bat":"12 horas","power":"8W","ip":"IP68","weight":"400 g","extras":"Iluminacion LED dinamica."},
    "Go 4":     {"bat":"7 horas","power":"4.2W","ip":"IP67","weight":"190 g","extras":"Tamano bolsillo. AI Sound Boost."},
    "Go Essential 2": {"bat":"7 horas","power":"3.1W","ip":"IPX7","weight":"200 g","extras":"Bluetooth 5.1. Clip integrado."},
    "Go 3":     {"bat":"5 horas","power":"4.2W","ip":"IP67","weight":"209 g","extras":"Diseno iconico JBL."},
}

def seo_desc(m, c, price):
    s=SPEC.get(m,{"bat":"","power":"","ip":"","weight":"","extras":""})
    return f"""JBL {m} Bluetooth Portatil - Color {c} - NUEVA 100% ORIGINAL CON FACTURA

CARACTERISTICAS PRINCIPALES:
- Sonido JBL PRO Sound potente y claro
- Bateria de {s['bat']} de reproduccion continua
- Resistencia al agua y polvo {s['ip']}
- Potencia {s['power']}
- Peso {s['weight']} - ultraportatil
- {s['extras']}

INCLUYE:
- 1x Bocina JBL {m} color {c}
- 1x Cable de carga USB-C
- 1x Manual de usuario
- 1x Guia de inicio rapido

GARANTIA Y ENVIO:
- Producto NUEVO en caja sellada con factura
- Garantia de 30 dias con nosotros
- Envio GRATIS a todo Mexico
- Envio el mismo dia si compras antes de las 2 PM
- Entrega en 24-72 hrs via Mercado Envios

COMPATIBILIDAD:
Compatible con cualquier dispositivo Bluetooth: iPhone, Android, Samsung, Xiaomi, Motorola, iPad, tablets, laptops Windows/Mac.

IMPORTANTE:
Esta bocina JBL {m} es 100% original, adquirida por medio de comercializadora autorizada con factura. No es reacondicionada, no es replica.

Preguntanos lo que quieras antes de comprar. Respondemos en menos de 1 hora.

Palabras clave: bocina jbl, altavoz bluetooth, parlante portatil, jbl {m.lower()}, bocina {c.lower()}, bluetooth portatil, bocina waterproof, bocina impermeable, bocina inalambrica, jbl {m.lower()} {c.lower()}."""

# Parametros especificos con UNIDADES correctas por modelo
NUMSPEC={
    "Charge 6":      {"bat":(28,"h"),"pwr":(40,"W"),"minf":(60,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
    "Flip 7":        {"bat":(16,"h"),"pwr":(35,"W"),"minf":(60,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
    "Clip 5":        {"bat":(12,"h"),"pwr":(7,"W"),"minf":(110,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
    "Grip":          {"bat":(12,"h"),"pwr":(8,"W"),"minf":(110,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
    "Go 4":          {"bat":(7,"h"), "pwr":(4.2,"W"),"minf":(180,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
    "Go Essential 2":{"bat":(7,"h"), "pwr":(3.1,"W"),"minf":(180,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
    "Go 3":          {"bat":(5,"h"), "pwr":(4.2,"W"),"minf":(110,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
}

# Mapeo de attribute id a clave NUMSPEC
ATTR2KEY={
    "MAX_BATTERY_AUTONOMY":"bat",
    "POWER_OUTPUT_RMS":"pwr",
    "MAX_POWER":"pwr",
    "MIN_FREQUENCY_RESPONSE":"minf",
    "MAX_FREQUENCY_RESPONSE":"maxf",
    "INPUT_IMPEDANCE":"imp",
    "DISTORTION":"dis",
    "BATTERY_VOLTAGE":"volt",
}

def num_val(aid, model):
    key=ATTR2KEY.get(aid)
    spec=NUMSPEC.get(model,{})
    if key and key in spec:
        n,u=spec[key]
        return f"{n} {u}"
    return None

def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

def predict_cat(title):
    try:
        r=requests.get(f"https://api.mercadolibre.com/sites/MLM/domain_discovery/search?limit=1&q={title}",headers=H,timeout=15).json()
        if r and isinstance(r,list): return r[0].get("category_id")
    except: pass
    return None

def build_attrs(prod_attrs, cat_attrs, model, color):
    base={}
    # primero desde catalogo
    for a in (prod_attrs or []):
        aid=a.get("id"); vid=a.get("value_id"); vn=a.get("value_name")
        if not aid: continue
        if aid in ("SELLER_SKU","GTIN","EAN","UPC","MPN","LINE"): continue
        if not vid and not vn: continue
        e={"id":aid}
        if vid: e["value_id"]=vid
        # reemplazar num con unit valida
        nv=num_val(aid,model)
        if nv:
            e={"id":aid,"value_name":nv}
        elif vn:
            e["value_name"]=vn
        base[aid]=e
    # ahora requeridos por categoria
    for ca in cat_attrs:
        aid=ca.get("id")
        tags=ca.get("tags") or {}
        req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required") or tags.get("conditional_required_fixed")
        if not req: continue
        if aid in base: continue
        vals=ca.get("values") or []
        vt=ca.get("value_type")
        # val numerica?
        nv=num_val(aid,model)
        if nv:
            base[aid]={"id":aid,"value_name":nv}; continue
        # specials
        if aid=="BRAND": base[aid]={"id":aid,"value_name":"JBL"}; continue
        if aid=="COLOR":
            matched=False
            for v in vals:
                if (v.get("name") or "").strip().lower()==color.strip().lower():
                    base[aid]={"id":aid,"value_id":v["id"],"value_name":v["name"]}; matched=True; break
            if not matched: base[aid]={"id":aid,"value_name":color}
            continue
        if aid=="MODEL": base[aid]={"id":aid,"value_name":model}; continue
        if aid=="ITEM_CONDITION": base[aid]={"id":aid,"value_name":"Nuevo"}; continue
        if aid=="GTIN": base[aid]={"id":aid,"value_name":"No aplica"}; continue
        if aid=="ALPHANUMERIC_MODEL": base[aid]={"id":aid,"value_name":f"JBL-{model.replace(' ','')}"}; continue
        # boolean defaults
        BOOL_YES={"IS_SMART","WITH_BLUETOOTH","HAS_BLUETOOTH","IS_PORTABLE","IS_RECHARGEABLE","IS_WIRELESS","IS_WATERPROOF","INCLUDES_CABLE","INCLUDES_BATTERY","HAS_APP_CONTROL","HAS_USB_INPUT","WITH_HANDSFREE_FUNCTION","HAS_MICROPHONE"}
        BOOL_NO={"IS_DUAL_VOICE_COIL","IS_DUAL_VOICE_ASSISTANTS","WITH_HANDLE","HAS_FM_RADIO","HAS_LED_LIGHTS","WITH_AUX","HAS_SD_MEMORY_INPUT"}
        if vt=="boolean":
            if aid in BOOL_YES: base[aid]={"id":aid,"value_name":"Si"}
            elif aid in BOOL_NO: base[aid]={"id":aid,"value_name":"No"}
            else: base[aid]={"id":aid,"value_name":"No"}
            continue
        if aid in ("SPEAKERS_NUMBER","PICKUPS_NUMBER"): base[aid]={"id":aid,"value_name":"1"}; continue
        if aid=="SPEAKER_FORMAT": base[aid]={"id":aid,"value_name":"1.0"}; continue
        if aid=="RAM_MEMORY": base[aid]={"id":aid,"value_name":"1 GB"}; continue
        if aid=="INTERNAL_MEMORY": base[aid]={"id":aid,"value_name":"1 GB"}; continue
        # fallback: pick first value from list
        if vals:
            v=vals[0]
            base[aid]={"id":aid,"value_id":v["id"],"value_name":v.get("name","")}
        elif vt=="number":
            base[aid]={"id":aid,"value_name":"1"}
        elif vt=="number_unit":
            base[aid]={"id":aid,"value_name":"1"}
        else:
            base[aid]={"id":aid,"value_name":"No aplica"}
    # Forzar GTIN siempre (por si no esta marcado como required pero lo pide conditionally)
    if "GTIN" not in base: base["GTIN"]={"id":"GTIN","value_name":"No aplica"}
    return list(base.values())

created=[]
closed=[]
for iid,model,color,price in SRC:
    item=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    cpid=item.get("catalog_product_id")
    cat_id=item.get("category_id") or "MLM59800"
    pics=[p["url"] for p in item.get("pictures",[]) if p.get("url")]
    title=seo_title(model,color)
    prod=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json() if cpid else {}
    cat_attrs=get_cat_attrs(cat_id)
    attrs=build_attrs(prod.get("attributes",[]), cat_attrs, model, color)
    body={
        "site_id":"MLM","title":title,"category_id":cat_id,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","condition":"new","listing_type_id":"gold_pro",
        "catalog_listing":False,"attributes":attrs,
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}]
    }
    if cpid: body["catalog_product_id"]=cpid
    if pics: body["pictures"]=[{"source":u} for u in pics[:10]]
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    retry=0
    while r.status_code not in (200,201) and retry<8:
        retry+=1
        try: j=r.json()
        except: break
        bad=set(); missing=set(); fix_unit=set()
        for c in j.get("cause",[]):
            msg=(c.get("message") or ""); code=(c.get("code") or "")
            if "missing_required" in code or "missing_catalog_required" in code or "missing_conditional_required" in code:
                mm=re.findall(r"\[([^\]]+)\]",msg)
                for gr in mm:
                    for x in gr.split(","):
                        x=x.strip().strip("\"'")
                        if x and x.isupper(): missing.add(x)
                sp=re.search(r'campo\s+"([^"]+)"\s+es obligatorio',msg)
                if sp:
                    fn=sp.group(1).lower()
                    spmap={"memoria ram":"RAM_MEMORY","memoria interna":"INTERNAL_MEMORY","marca":"BRAND","modelo":"MODEL","color":"COLOR"}
                    if fn in spmap: missing.add(spmap[fn])
            if "attributes.omitted" in code or "attribute.invalid" in code or "number_invalid_format" in code:
                mm=re.search(r"attribute\s+([A-Z_]+)",msg) or re.search(r"Attribute\s+([A-Z_]+)",msg)
                if mm: fix_unit.add(mm.group(1))
            if "attributes.ignored" in code:
                mm=re.search(r"\[([A-Z_]+)\]",msg)
                if mm: bad.add(mm.group(1))
        # remover bad/ignored
        if bad: attrs=[a for a in attrs if a["id"] not in bad]
        # agregar missing
        for m_id in missing:
            if not any(a["id"]==m_id for a in attrs):
                nv=num_val(m_id,model)
                if nv: attrs.append({"id":m_id,"value_name":nv})
                elif m_id=="GTIN": attrs.append({"id":m_id,"value_name":"No aplica"})
                elif m_id=="RAM_MEMORY": attrs.append({"id":m_id,"value_name":"1 GB"})
                elif m_id=="INTERNAL_MEMORY": attrs.append({"id":m_id,"value_name":"1 GB"})
                else: attrs.append({"id":m_id,"value_name":"No aplica"})
        # recolocar unit en fix_unit
        if fix_unit:
            new_attrs=[]
            for a in attrs:
                if a["id"] in fix_unit:
                    nv=num_val(a["id"],model)
                    if nv:
                        new_attrs.append({"id":a["id"],"value_name":nv})
                    else:
                        # skip si no podemos arreglar
                        continue
                else:
                    new_attrs.append(a)
            attrs=new_attrs
        body["attributes"]=attrs
        r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    if r.status_code in (200,201):
        resp=r.json()
        new_id=resp.get("id")
        requests.post(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H,json={"plain_text":seo_desc(model,color,price)},timeout=15)
        print(f"OK {iid} -> {new_id} [{model} {color}]")
        created.append({"src":iid,"new":new_id,"model":model,"color":color,"price":price})
    else:
        err=str(r.json() if r.headers.get("content-type","").startswith("application") else r.text)[:400]
        print(f"ERR {iid} [{model} {color}]: {err}")
        created.append({"src":iid,"model":model,"color":color,"err":err[:300]})
    time.sleep(2)

print("\n=== CERRANDO ORIGINALES ===")
for c in created:
    if c.get("new"):
        rr=requests.put(f"https://api.mercadolibre.com/items/{c['src']}",headers=H,json={"status":"closed"},timeout=15)
        print(f"close {c['src']}: {rr.status_code}")
        closed.append(c['src'])
        time.sleep(0.5)

print("\n=== SUMMARY ===")
print(f"Tradicionales creadas: {sum(1 for c in created if c.get('new'))}/{len(SRC)}")
print(f"Catalogos cerrados: {len(closed)}")
print("\n=== MAPPING ===")
for c in created:
    if c.get("new"): print(f"  {c['src']} -> {c['new']} [{c['model']} {c['color']}] ${c['price']}")
    else: print(f"  {c['src']} FAILED: {c.get('err')}")
