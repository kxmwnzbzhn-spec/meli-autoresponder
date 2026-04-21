import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

SRC=[
    ("MLM2880754323","Go 3","Negra",469),
    ("MLM2880758735","Charge 6","Roja",919),
    ("MLM2880758747","Clip 5","Morada",719),
    ("MLM2880758751","Grip","Negra",619),
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
    "Charge 6": {"bat":"28 horas","power":"40W","ip":"IP68","weight":"970 g","extras":"Powerbank integrada. AURACAST multi-bocina. Conexion con app JBL Portable."},
    "Flip 7":   {"bat":"16 horas","power":"35W","ip":"IP68","weight":"560 g","extras":"AI Sound Boost. AURACAST. Conexion con app JBL Portable."},
    "Clip 5":   {"bat":"12 horas","power":"7W","ip":"IP67","weight":"285 g","extras":"Mosqueton integrado para llevar donde sea. AURACAST."},
    "Grip":     {"bat":"12 horas","power":"8W","ip":"IP68","weight":"400 g","extras":"Iluminacion LED dinamica. Forma pensada para agarrar con una mano."},
    "Go 4":     {"bat":"7 horas","power":"4.2W","ip":"IP67","weight":"190 g","extras":"Tamano bolsillo. AI Sound Boost. Conexion con app JBL Portable."},
    "Go Essential 2": {"bat":"7 horas","power":"3.1W","ip":"IPX7","weight":"200 g","extras":"Edicion esencial. Bluetooth 5.1. Clip integrado."},
    "Go 3":     {"bat":"5 horas","power":"4.2W","ip":"IP67","weight":"209 g","extras":"Diseno iconico JBL. Cuerda integrada para colgar."},
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

Palabras clave: bocina jbl, altavoz bluetooth, parlante portatil, jbl {m.lower()}, bocina {c.lower()}, bluetooth portatil, bocina waterproof, bocina impermeable, bocina inalambrica, bocina jbl original, jbl {m.lower()} {c.lower()}, regalo bocina, bocina fiesta, bocina exterior."""

# Defaults amplios para atributos comunes que MELI marca obligatorios en distintas categorias
GEN_DEFAULTS={
    "IS_DUAL_VOICE_COIL":"No","IS_DUAL_VOICE_ASSISTANTS":"No","IS_SMART":"Si","IS_WATERPROOF":"Si",
    "IS_WIRELESS":"Si","IS_PORTABLE":"Si","IS_RECHARGEABLE":"Si","HAS_MICROPHONE":"Si",
    "INCLUDES_CABLE":"Si","INCLUDES_BATTERY":"Si","WITH_HANDLE":"No","WITH_HANDSFREE_FUNCTION":"Si",
    "WITH_BLUETOOTH":"Si","HAS_BLUETOOTH":"Si","HAS_APP_CONTROL":"Si","HAS_FM_RADIO":"No",
    "HAS_LED_LIGHTS":"No","HAS_USB_INPUT":"Si","WITH_AUX":"No","HAS_SD_MEMORY_INPUT":"No",
    "ALPHANUMERIC_MODEL":"Bluetooth","SPEAKERS_NUMBER":"1","PICKUPS_NUMBER":"1",
    "SPEAKER_FORMAT":"1.0","MAX_BATTERY_AUTONOMY":"5","BATTERY_VOLTAGE":"5",
    "POWER_OUTPUT_RMS":"5","DISTORTION":"1","MAX_FREQUENCY_RESPONSE":"20000","MIN_FREQUENCY_RESPONSE":"60",
    "MAX_POWER":"10","INPUT_IMPEDANCE":"4","SPEAKERS_FORMAT":"1.0",
    "RAM_MEMORY":"No aplica","INTERNAL_MEMORY":"No aplica","RAM":"No aplica",
    "MODEL":"", # se llena despues con m
}

def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

def predict_cat(title):
    try:
        r=requests.get(f"https://api.mercadolibre.com/sites/MLM/domain_discovery/search?limit=1&q={title}",headers=H,timeout=15).json()
        if r and isinstance(r,list): return r[0].get("category_id")
    except: pass
    return None

def sanitize_vn(aid, vn):
    vn = (vn or "").strip()
    if not vn: return None
    if aid.endswith("_WEIGHT") or aid.endswith("_WIDTH") or aid.endswith("_LENGTH") or aid.endswith("_HEIGHT"):
        # numeric unit format needs value_struct; skip
        return None
    if aid in ("MAX_POWER","POWER_OUTPUT_RMS","BATTERY_VOLTAGE","MAX_BATTERY_AUTONOMY","MIN_FREQUENCY_RESPONSE","MAX_FREQUENCY_RESPONSE","INPUT_IMPEDANCE","DISTORTION"):
        # number with unit — extract number
        mm = re.search(r"[\d.]+", vn)
        return mm.group(0) if mm else None
    return vn

def build_attrs(prod_attrs, cat_attrs, model, color):
    base={}
    for a in (prod_attrs or []):
        aid=a.get("id"); vid=a.get("value_id"); vn=a.get("value_name")
        if not aid or aid in ("SELLER_SKU","GTIN","EAN","UPC","MPN"): continue
        if not vid and not vn: continue
        e={"id":aid}
        if vid: e["value_id"]=vid
        if vn:
            svn=sanitize_vn(aid,vn)
            if svn: e["value_name"]=svn
        base[aid]=e
    # required from category
    for ca in cat_attrs:
        aid=ca.get("id")
        if aid in base: continue
        tags=ca.get("tags") or {}
        if not (tags.get("required") or tags.get("catalog_required")): continue
        # pick default
        vals=ca.get("values") or []
        def_val=None
        # prefer preset defaults matching
        if aid in GEN_DEFAULTS:
            pv=GEN_DEFAULTS[aid] or (model if aid=="MODEL" else "")
            if pv:
                # try to match to value id
                for v in vals:
                    if (v.get("name") or "").strip().lower()==pv.strip().lower():
                        base[aid]={"id":aid,"value_id":v["id"],"value_name":v["name"]}
                        break
                else:
                    base[aid]={"id":aid,"value_name":pv}
                continue
        # special handling by id
        if aid=="BRAND":
            base[aid]={"id":aid,"value_name":"JBL"}
        elif aid=="COLOR":
            # try to match
            for v in vals:
                if (v.get("name") or "").strip().lower()==color.strip().lower():
                    base[aid]={"id":aid,"value_id":v["id"],"value_name":v["name"]}; break
            else:
                base[aid]={"id":aid,"value_name":color}
        elif aid=="MODEL" or aid=="LINE":
            base[aid]={"id":aid,"value_name":model}
        elif aid=="ITEM_CONDITION":
            base[aid]={"id":aid,"value_name":"Nuevo"}
        else:
            # numeric/list: pick first allowed value
            if vals:
                v=vals[0]
                base[aid]={"id":aid,"value_id":v["id"],"value_name":v.get("name","")}
            else:
                vt=ca.get("value_type")
                if vt=="boolean":
                    base[aid]={"id":aid,"value_name":"No"}
                elif vt=="number" or vt=="number_unit":
                    base[aid]={"id":aid,"value_name":"1"}
                else:
                    base[aid]={"id":aid,"value_name":"No aplica"}
    return list(base.values())

created=[]
closed=[]
for iid,model,color,price in SRC:
    item=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    cpid=item.get("catalog_product_id")
    cat_id=item.get("category_id") or "MLM1055"
    pics=[p["url"] for p in item.get("pictures",[]) if p.get("url")]
    title=seo_title(model,color)
    # predict category from title (mejor match)
    pc=predict_cat(title) or cat_id
    cat_id=pc
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
    while r.status_code not in (200,201) and retry<6:
        retry+=1
        try: j=r.json()
        except: break
        # colectar atributos faltantes y malos
        bad=set(); missing=set()
        for c in j.get("cause",[]):
            msg=(c.get("message") or "")
            code=c.get("code") or ""
            if "missing_required" in code or "missing_catalog_required" in code:
                mm=re.findall(r"\[([^\]]+)\]",msg)
                for gr in mm:
                    for x in gr.split(","):
                        x=x.strip().strip("\"'")
                        if x and x.isupper(): missing.add(x)
                # also detect spanish field names
                sp=re.search(r'campo\s+"([^"]+)"\s+es obligatorio',msg)
                if sp:
                    fn=sp.group(1).lower()
                    # map common spanish -> attr ids
                    spmap={"memoria ram":"RAM_MEMORY","memoria interna":"INTERNAL_MEMORY","marca":"BRAND","modelo":"MODEL","color":"COLOR"}
                    if fn in spmap: missing.add(spmap[fn])
            if "attribute.invalid" in code or "attribute.number_invalid_format" in code or "attributes.omitted" in code:
                mm=re.search(r"attribute\s+([A-Z_]+)",msg)
                if mm: bad.add(mm.group(1))
        if bad: attrs=[a for a in attrs if a["id"] not in bad]
        for m_id in missing:
            if not any(a["id"]==m_id for a in attrs):
                pv=GEN_DEFAULTS.get(m_id,"No aplica")
                attrs.append({"id":m_id,"value_name":pv})
        body["attributes"]=attrs
        r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    if r.status_code in (200,201):
        resp=r.json()
        new_id=resp.get("id")
        requests.post(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H,json={"plain_text":seo_desc(model,color,price)},timeout=15)
        print(f"OK {iid} -> {new_id} [{model} {color}] cat={cat_id}")
        created.append({"src":iid,"new":new_id,"model":model,"color":color,"price":price})
    else:
        err=str(r.json() if r.headers.get("content-type","").startswith("application") else r.text)[:500]
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
