import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Mismas funciones pero con GTIN valido (13 digits) y RAM/INT memoria con valor de lista
GTIN_JBL="0050036391016"  # generic JBL GTIN — if rejected, try "No aplica" como enum

SRC=[
    ("MLM5222936976","Charge 6","Azul",919),
    ("MLM5222987710","Go 4","Roja",469),
    ("MLM5222987718","Go 4","Azul Marino",469),
]

def seo_title(m, c):
    tm={
        "Charge 6": f"Bocina Jbl Charge 6 Bluetooth Portatil {c} Ip68 Nueva",
        "Go 4":     f"Bocina Jbl Go 4 Bluetooth Portatil {c} Ip67 Nueva",
    }
    return tm.get(m,f"Bocina Jbl {m} {c} Nueva")[:60]

NUMSPEC={
    "Charge 6":{"bat":(28,"h"),"pwr":(40,"W"),"minf":(60,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
    "Go 4":    {"bat":(7,"h"),"pwr":(4.2,"W"),"minf":(180,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
}
ATTR2KEY={"MAX_BATTERY_AUTONOMY":"bat","POWER_OUTPUT_RMS":"pwr","MAX_POWER":"pwr","MIN_FREQUENCY_RESPONSE":"minf","MAX_FREQUENCY_RESPONSE":"maxf","INPUT_IMPEDANCE":"imp","DISTORTION":"dis","BATTERY_VOLTAGE":"volt"}

def num_val(aid,model):
    k=ATTR2KEY.get(aid); sp=NUMSPEC.get(model,{})
    if k and k in sp: n,u=sp[k]; return f"{n} {u}"
    return None

def seo_desc(m,c,price):
    return f"""JBL {m} Bluetooth Portatil {c} - NUEVA 100% ORIGINAL CON FACTURA

CARACTERISTICAS: Sonido JBL PRO, IP67/IP68 waterproof, bateria de larga duracion, AURACAST multi-bocina, AI Sound Boost.

INCLUYE: Bocina JBL {m} {c} + cable USB-C + manual + guia.

GARANTIA Y ENVIO: 30 dias garantia, envio GRATIS mismo dia antes 2PM, entrega 24-72hrs.

Palabras clave: bocina jbl, jbl {m.lower()}, bluetooth portatil, {c.lower()}, waterproof, inalambrica, impermeable."""

def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

for iid,model,color,price in SRC:
    item=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    cpid=item.get("catalog_product_id")
    cat_id=item.get("category_id") or "MLM59800"
    pics=[p["url"] for p in item.get("pictures",[]) if p.get("url")]
    title=seo_title(model,color)
    prod=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json() if cpid else {}
    cat_attrs=get_cat_attrs(cat_id)
    # Build attrs: brand, color, model, item_condition, + number_unit with units, + RAM/INT from list, + GTIN enum "No aplica"
    attrs=[
        {"id":"BRAND","value_name":"JBL"},
        {"id":"COLOR","value_name":color},
        {"id":"MODEL","value_name":model},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"},
        {"id":"GTIN","value_name":"No aplica"},  # literal con espacio
    ]
    # agregar num_unit required
    for ca in cat_attrs:
        aid=ca.get("id")
        tags=ca.get("tags") or {}
        req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
        if not req: continue
        if aid in {a["id"] for a in attrs}: continue
        nv=num_val(aid,model)
        if nv:
            attrs.append({"id":aid,"value_name":nv})
            continue
        vals=ca.get("values") or []
        vt=ca.get("value_type")
        if aid=="RAM_MEMORY" or aid=="INTERNAL_MEMORY":
            # pick first value from allowed list
            if vals:
                attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
            continue
        if aid=="ALPHANUMERIC_MODEL":
            attrs.append({"id":aid,"value_name":f"JBL-{model.replace(' ','')}"}); continue
        BOOL_YES={"IS_SMART","WITH_BLUETOOTH","HAS_BLUETOOTH","IS_PORTABLE","IS_RECHARGEABLE","IS_WIRELESS","IS_WATERPROOF","INCLUDES_CABLE","INCLUDES_BATTERY"}
        BOOL_NO={"IS_DUAL_VOICE_COIL","IS_DUAL_VOICE_ASSISTANTS","WITH_HANDLE","HAS_FM_RADIO","HAS_LED_LIGHTS","WITH_AUX","HAS_SD_MEMORY_INPUT"}
        if vt=="boolean":
            attrs.append({"id":aid,"value_name":"Si" if aid in BOOL_YES else ("No" if aid in BOOL_NO else "No")})
            continue
        if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
        elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
        else: attrs.append({"id":aid,"value_name":"No aplica"})
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
    # retry loop simple
    retry=0
    while r.status_code not in (200,201) and retry<6:
        retry+=1
        try: j=r.json()
        except: break
        bad=set(); miss=set(); fix=set()
        for c in j.get("cause",[]):
            msg=(c.get("message") or ""); code=(c.get("code") or "")
            if "missing_required" in code or "missing_catalog_required" in code or "missing_conditional_required" in code:
                mm=re.findall(r"\[([^\]]+)\]",msg)
                for gr in mm:
                    for x in gr.split(","):
                        x=x.strip().strip("\"'")
                        if x and x.isupper(): miss.add(x)
                sp=re.search(r'campo\s+"([^"]+)"\s+es obligatorio',msg)
                if sp:
                    fn=sp.group(1).lower()
                    spmap={"memoria ram":"RAM_MEMORY","memoria interna":"INTERNAL_MEMORY"}
                    if fn in spmap: miss.add(spmap[fn])
            if "attributes.omitted" in code or "number_invalid_format" in code:
                mm=re.search(r"attribute\s+([A-Z_]+)",msg) or re.search(r"Attribute\s+([A-Z_]+)",msg)
                if mm: fix.add(mm.group(1))
            if "attributes.invalid" in code:
                mm=re.search(r"Attribute:\s+([A-Z_]+)",msg)
                if mm: bad.add(mm.group(1))
            if "product_identifier.invalid_format" in code:
                fix.add("GTIN")
        if bad: attrs=[a for a in attrs if a["id"] not in bad]
        for mid in miss:
            if not any(a["id"]==mid for a in attrs):
                nv=num_val(mid,model)
                if nv: attrs.append({"id":mid,"value_name":nv})
                elif mid=="RAM_MEMORY" or mid=="INTERNAL_MEMORY":
                    for ca in cat_attrs:
                        if ca.get("id")==mid:
                            vs=ca.get("values") or []
                            if vs: attrs.append({"id":mid,"value_id":vs[0]["id"],"value_name":vs[0].get("name","")})
                            break
        if "GTIN" in fix:
            # quitar GTIN problemático
            attrs=[a for a in attrs if a["id"]!="GTIN"]
        body["attributes"]=attrs
        r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    if r.status_code in (200,201):
        nid=r.json().get("id")
        requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":seo_desc(model,color,price)},timeout=15)
        print(f"OK {iid} -> {nid} [{model} {color}]")
        # cerrar original
        rr=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"closed"},timeout=15)
        print(f"close {iid}: {rr.status_code}")
    else:
        print(f"ERR {iid} [{model} {color}]: {str(r.json())[:400]}")
    time.sleep(2)
