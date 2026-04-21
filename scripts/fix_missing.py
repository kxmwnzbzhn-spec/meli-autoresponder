import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# 1. Borrar Go 4 Rosa forbidden para liberar el slot
GO4_ROSA_BAD="MLM2880775041"
print(f"\n=== Closing Go 4 Rosa forbidden ({GO4_ROSA_BAD}) ===")
rr=requests.put(f"https://api.mercadolibre.com/items/{GO4_ROSA_BAD}",headers=H,json={"status":"closed"},timeout=15)
print(f"close: {rr.status_code}")
time.sleep(1)
rr=requests.put(f"https://api.mercadolibre.com/items/{GO4_ROSA_BAD}",headers=H,json={"deleted":"true"},timeout=15)
print(f"delete: {rr.status_code}")
time.sleep(1)

# 2. Buscar catalog IDs correctos
def search_best(q, must_have, must_not_have):
    r=requests.get(f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={q}",headers=H,timeout=15).json()
    for item in r.get("results",[])[:10]:
        name=(item.get("name") or "").lower()
        if any(bad in name for bad in must_not_have): continue
        if all(good in name for good in must_have[:2]):
            return item.get("id"), item.get("name")
    for item in r.get("results",[])[:10]:
        name=(item.get("name") or "").lower()
        if any(bad in name for bad in must_not_have): continue
        if must_have[0] in name:
            return item.get("id"), item.get("name")
    return None, None

print("\n=== Buscando catálogo ===")
ch6neg_cpid, ch6neg_nm = search_best("JBL Charge 6 Negro", ["charge 6","negr"], ["charge 5","rojo","azul","blanco","camuflaje"])
print(f"Charge 6 Negra: {ch6neg_cpid} -> {ch6neg_nm}")
go4ros_cpid, go4ros_nm = search_best("JBL Go 4 Rosa", ["go 4","rosa"], ["go 3","azul","rojo","negro","camuflaje"])
print(f"Go 4 Rosa: {go4ros_cpid} -> {go4ros_nm}")

# 3. Publicar las 2 como tradicionales SEO
NUMSPEC={
    "Charge 6":{"bat":(28,"h"),"pwr":(40,"W"),"minf":(60,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
    "Go 4":    {"bat":(7,"h"),"pwr":(4.2,"W"),"minf":(180,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
}
ATTR2KEY={"MAX_BATTERY_AUTONOMY":"bat","POWER_OUTPUT_RMS":"pwr","MAX_POWER":"pwr","MIN_FREQUENCY_RESPONSE":"minf","MAX_FREQUENCY_RESPONSE":"maxf","INPUT_IMPEDANCE":"imp","DISTORTION":"dis","BATTERY_VOLTAGE":"volt"}

def num_val(aid,model):
    k=ATTR2KEY.get(aid); sp=NUMSPEC.get(model,{})
    if k and k in sp: n,u=sp[k]; return f"{n} {u}"
    return None

SPEC={
    "Charge 6":{"bat":"28 horas","power":"40W","ip":"IP68","weight":"970 g","extras":"Powerbank integrada. AURACAST."},
    "Go 4":{"bat":"7 horas","power":"4.2W","ip":"IP67","weight":"190 g","extras":"Tamano bolsillo. AI Sound Boost."},
}

def seo_title(m,c):
    if m=="Charge 6": return f"Bocina Jbl Charge 6 Bluetooth Portatil {c} Ip68 Nueva"[:60]
    if m=="Go 4":     return f"Bocina Jbl Go 4 Bluetooth Portatil {c} Ip67 Nueva"[:60]
    return f"Bocina Jbl {m} {c}"[:60]

def seo_desc(m,c,price):
    s=SPEC.get(m,{})
    return f"""JBL {m} Bluetooth Portatil - Color {c} - NUEVA 100% ORIGINAL CON FACTURA

CARACTERISTICAS PRINCIPALES:
- Sonido JBL PRO Sound potente y claro
- Bateria de {s.get('bat','')} de reproduccion continua
- Resistencia al agua y polvo {s.get('ip','')}
- Potencia {s.get('power','')}
- Peso {s.get('weight','')} - ultraportatil
- {s.get('extras','')}

INCLUYE: 1x Bocina JBL {m} color {c}, cable USB-C, manual, guia de inicio.

GARANTIA Y ENVIO: Producto nuevo en caja sellada con factura. Garantia 30 dias. Envio GRATIS a todo Mexico. Entrega en 24-72 hrs.

COMPATIBILIDAD: Compatible con cualquier dispositivo Bluetooth (iPhone, Android, Samsung, etc.).

Palabras clave: bocina jbl, altavoz bluetooth, parlante portatil, jbl {m.lower()}, bocina {c.lower()}, bluetooth portatil, bocina waterproof, bocina impermeable, bocina inalambrica, jbl {m.lower()} {c.lower()}."""

def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

def publish_tradic(cpid, model, color, price):
    prod=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
    cat_id=prod.get("category_details",{}).get("id") or prod.get("category_id") or "MLM59800"
    pics=[p["url"] for p in (prod.get("pictures") or []) if p.get("url")]
    cat_attrs=get_cat_attrs(cat_id)
    attrs=[
        {"id":"BRAND","value_name":"JBL"},
        {"id":"COLOR","value_name":color},
        {"id":"MODEL","value_name":model},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"},
        {"id":"GTIN","value_name":"No aplica"},
    ]
    seen={a["id"] for a in attrs}
    for ca in cat_attrs:
        aid=ca.get("id"); tags=ca.get("tags") or {}
        req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
        if not req or aid in seen: continue
        nv=num_val(aid,model)
        if nv: attrs.append({"id":aid,"value_name":nv}); seen.add(aid); continue
        vals=ca.get("values") or []
        vt=ca.get("value_type")
        if aid in ("RAM_MEMORY","INTERNAL_MEMORY"):
            if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")}); seen.add(aid)
            continue
        if aid=="ALPHANUMERIC_MODEL":
            attrs.append({"id":aid,"value_name":f"JBL-{model.replace(' ','')}"}); seen.add(aid); continue
        BOOL_YES={"IS_SMART","WITH_BLUETOOTH","HAS_BLUETOOTH","IS_PORTABLE","IS_RECHARGEABLE","IS_WIRELESS","IS_WATERPROOF","INCLUDES_CABLE","INCLUDES_BATTERY"}
        BOOL_NO={"IS_DUAL_VOICE_COIL","IS_DUAL_VOICE_ASSISTANTS","WITH_HANDLE","HAS_FM_RADIO","HAS_LED_LIGHTS","WITH_AUX","HAS_SD_MEMORY_INPUT"}
        if vt=="boolean":
            attrs.append({"id":aid,"value_name":"Si" if aid in BOOL_YES else ("No" if aid in BOOL_NO else "No")})
            seen.add(aid); continue
        if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
        elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
        else: attrs.append({"id":aid,"value_name":"No aplica"})
        seen.add(aid)
    title=seo_title(model,color)
    body={
        "site_id":"MLM","title":title,"category_id":cat_id,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","condition":"new","listing_type_id":"gold_pro",
        "catalog_listing":False,"attributes":attrs,"catalog_product_id":cpid,
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}],
    }
    if pics: body["pictures"]=[{"source":u} for u in pics[:10]]
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    retry=0
    while r.status_code not in (200,201) and retry<6:
        retry+=1
        try: j=r.json()
        except: break
        bad=set(); miss=set(); fix=set()
        for c in j.get("cause",[]):
            msg=c.get("message","") or ""; code=c.get("code","") or ""
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
            if "product_identifier.invalid_format" in code: fix.add("GTIN")
        if bad: attrs=[a for a in attrs if a["id"] not in bad]
        for mid in miss:
            if not any(a["id"]==mid for a in attrs):
                nv=num_val(mid,model)
                if nv: attrs.append({"id":mid,"value_name":nv})
                elif mid in ("RAM_MEMORY","INTERNAL_MEMORY"):
                    for ca in cat_attrs:
                        if ca.get("id")==mid:
                            vs=ca.get("values") or []
                            if vs: attrs.append({"id":mid,"value_id":vs[0]["id"],"value_name":vs[0].get("name","")})
                            break
                else: attrs.append({"id":mid,"value_name":"No aplica"})
        if "GTIN" in fix: attrs=[a for a in attrs if a["id"]!="GTIN"]
        body["attributes"]=attrs
        r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    if r.status_code in (200,201):
        nid=r.json().get("id")
        requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":seo_desc(model,color,price)},timeout=15)
        return nid, None
    return None, str(r.json())[:400]

# Charge 6 Negra tradicional
if ch6neg_cpid:
    nid,err=publish_tradic(ch6neg_cpid,"Charge 6","Negra",919)
    print(f"\nCharge 6 Negra -> {nid} ERR={err}")
else:
    print("Charge 6 Negra: no cpid found")

time.sleep(2)

# Go 4 Rosa republish
if go4ros_cpid:
    nid,err=publish_tradic(go4ros_cpid,"Go 4","Rosa",469)
    print(f"\nGo 4 Rosa -> {nid} ERR={err}")
else:
    print("Go 4 Rosa: no cpid found")
