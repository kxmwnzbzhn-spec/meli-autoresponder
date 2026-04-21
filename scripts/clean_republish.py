import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Atributos TÓXICOS a filtrar (inducen a confusión con reacondicionado/artesanal)
BAD_ATTRS={"GTIN","EAN","UPC","MPN","SELLER_SKU","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","PRODUCT_CONDITION","ITEM_CONDITION_NOTE","RECONDITIONED_CONDITION","IS_HANDMADE"}

def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

NUMSPEC={
    "Charge 6":{"bat":(28,"h"),"pwr":(40,"W"),"minf":(60,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
    "Go 4":    {"bat":(7,"h"),"pwr":(4.2,"W"),"minf":(180,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
    "Sony XB100":{"bat":(16,"h"),"pwr":(10,"W"),"minf":(100,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
}
ATTR2KEY={"MAX_BATTERY_AUTONOMY":"bat","POWER_OUTPUT_RMS":"pwr","MAX_POWER":"pwr","MIN_FREQUENCY_RESPONSE":"minf","MAX_FREQUENCY_RESPONSE":"maxf","INPUT_IMPEDANCE":"imp","DISTORTION":"dis","BATTERY_VOLTAGE":"volt"}

def num_val(aid, model):
    k=ATTR2KEY.get(aid); sp=NUMSPEC.get(model,{})
    if k and k in sp: n,u=sp[k]; return f"{n} {u}"
    return None

def build_clean_attrs(cat_attrs, model, color, condition):
    """Construye atributos MÍNIMOS y CONSISTENTES con la condicion deseada."""
    cond_attr_value="Nuevo" if condition=="new" else "Reacondicionado"
    attrs=[
        {"id":"BRAND","value_name":"Sony" if "Sony" in model else "JBL"},
        {"id":"COLOR","value_name":color},
        {"id":"ITEM_CONDITION","value_name":cond_attr_value},
    ]
    seen={a["id"] for a in attrs}
    for ca in cat_attrs:
        aid=ca.get("id"); tags=ca.get("tags") or {}
        req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
        if not req or aid in seen or aid in BAD_ATTRS: continue
        nv=num_val(aid,model)
        if nv: attrs.append({"id":aid,"value_name":nv}); seen.add(aid); continue
        vals=ca.get("values") or []
        vt=ca.get("value_type")
        if aid in ("RAM_MEMORY","INTERNAL_MEMORY"):
            if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")}); seen.add(aid)
            continue
        BOOL_YES={"IS_SMART","WITH_BLUETOOTH","HAS_BLUETOOTH","IS_PORTABLE","IS_RECHARGEABLE","IS_WIRELESS","IS_WATERPROOF","INCLUDES_CABLE","INCLUDES_BATTERY"}
        BOOL_NO={"IS_DUAL_VOICE_COIL","IS_DUAL_VOICE_ASSISTANTS","WITH_HANDLE","HAS_FM_RADIO","HAS_LED_LIGHTS","WITH_AUX","HAS_SD_MEMORY_INPUT"}
        if vt=="boolean":
            attrs.append({"id":aid,"value_name":"Si" if aid in BOOL_YES else ("No" if aid in BOOL_NO else "No")}); seen.add(aid); continue
        if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
        elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
        else: attrs.append({"id":aid,"value_name":"No aplica"})
        seen.add(aid)
    return attrs

def publish(cpid, model, color, price, condition, title, desc):
    prod=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
    cat_id=prod.get("category_details",{}).get("id") or prod.get("category_id") or "MLM59800"
    pics=[p["url"] for p in (prod.get("pictures") or []) if p.get("url")]
    cat_attrs=get_cat_attrs(cat_id)
    attrs=build_clean_attrs(cat_attrs, model, color, condition)
    body={
        "site_id":"MLM","title":title[:60],"category_id":cat_id,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","condition":condition,"listing_type_id":"gold_pro",
        "catalog_listing":False,"catalog_product_id":cpid,"attributes":attrs,
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
                        if x and x.isupper() and x not in BAD_ATTRS: miss.add(x)
            if "attributes.omitted" in code or "number_invalid_format" in code:
                mm=re.search(r"attribute\s+([A-Z_]+)",msg) or re.search(r"Attribute\s+([A-Z_]+)",msg)
                if mm: fix.add(mm.group(1))
            if "attributes.invalid" in code:
                mm=re.search(r"Attribute:\s+([A-Z_]+)",msg)
                if mm: bad.add(mm.group(1))
        if bad: attrs=[a for a in attrs if a["id"] not in bad]
        for mid in miss:
            if mid in BAD_ATTRS: continue
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
        body["attributes"]=attrs
        r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    if r.status_code in (200,201):
        nid=r.json().get("id")
        requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":desc},timeout=15)
        return nid, None
    return None, str(r.json())[:500]

# 1) Go 4 Rosa NUEVA (limpia, sin GTIN "No aplica")
print("=== Go 4 Rosa limpia ===")
title="Bocina JBL Go 4 Bluetooth Portatil Rosa Ip67 Nueva Original"
desc="""JBL Go 4 Bluetooth Portatil Color Rosa - NUEVA ORIGINAL CON FACTURA

CARACTERISTICAS:
- Sonido JBL PRO Sound potente y claro
- Bateria de 7 horas de reproduccion continua
- Resistencia al agua y polvo IP67
- Potencia 4.2W, peso 190 g ultraportatil
- AI Sound Boost y conexion con app JBL Portable

INCLUYE: Bocina JBL Go 4 Rosa, cable USB-C, manual, guia.

GARANTIA Y ENVIO: Nueva en caja sellada con factura. Garantia 30 dias. Envio GRATIS todo Mexico. Entrega 24-72 hrs.

COMPATIBILIDAD: Compatible con dispositivos Bluetooth (iPhone, Android, Samsung).

Preguntanos antes de comprar. Respondemos en minutos."""
nid,err=publish("MLM65831856","Go 4","Rosa",479,"new",title,desc)
print(f"Go 4 Rosa -> {nid} ERR={err}")
time.sleep(2)

# 2) Sony XB100 Negra REACONDICIONADA (limpia)
print("\n=== Sony XB100 Reacondicionada limpia ===")
title="Bocina Sony SRS-XB100 Bluetooth Reacondicionada Negra Original"
desc="""Sony SRS-XB100 Bluetooth Portatil Negro - REACONDICIONADA POR NOSOTROS

PRODUCTO REACONDICIONADO:
- Bocina revisada, limpia y probada al 100% (audio, bluetooth, bateria, microfono)
- Puede presentar minimas marcas cosmeticas de uso
- Incluye caja generica de proteccion (no original)
- Con factura y garantia de 30 dias

CARACTERISTICAS:
- Sonido EXTRA BASS de Sony
- 16 horas de bateria
- Resistencia al agua IPX4
- Peso 274 g - ultraportatil con correa
- Bluetooth 5.3 estable

INCLUYE: Bocina Sony SRS-XB100 Negra reacondicionada, cable USB, manual digital.

GARANTIA Y ENVIO: Garantia 30 dias. Envio GRATIS todo Mexico. Entrega 24-72 hrs.

IMPORTANTE: Producto REACONDICIONADO (no nuevo). Si buscas nueva en empaque sellado, ver nuestra publicacion Sony XB100 Nueva."""
nid,err=publish("MLM25912333","Sony XB100","Negra",449,"used",title,desc)
print(f"Sony Reacond -> {nid} ERR={err}")
time.sleep(2)

# 3) Reactivar Go 4 Negra out_of_stock
print("\n=== Reactivando Go 4 Negra ===")
rr=requests.put(f"https://api.mercadolibre.com/items/MLM2880766117",headers=H,json={"available_quantity":1,"status":"active"},timeout=15)
print(f"Go 4 Negra reactivate: {rr.status_code} {rr.text[:200]}")
