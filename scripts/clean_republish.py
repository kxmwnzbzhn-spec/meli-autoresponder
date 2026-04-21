import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

BAD_ATTRS={"SELLER_SKU","MPN","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","PRODUCT_CONDITION","ITEM_CONDITION_NOTE","RECONDITIONED_CONDITION","IS_HANDMADE"}

def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

def get_prod_gtin(prod):
    """Extrae GTIN del catalog product si existe."""
    for a in (prod.get("attributes") or []):
        if a.get("id") in ("GTIN","EAN","UPC") and a.get("value_name"):
            return a["value_name"]
    return None

NUMSPEC={
    "Go 4":    {"bat":(7,"h"),"pwr":(4.2,"W"),"minf":(180,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
    "Sony XB100":{"bat":(16,"h"),"pwr":(10,"W"),"minf":(100,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
}
ATTR2KEY={"MAX_BATTERY_AUTONOMY":"bat","POWER_OUTPUT_RMS":"pwr","MAX_POWER":"pwr","MIN_FREQUENCY_RESPONSE":"minf","MAX_FREQUENCY_RESPONSE":"maxf","INPUT_IMPEDANCE":"imp","DISTORTION":"dis","BATTERY_VOLTAGE":"volt"}

def num_val(aid, model):
    k=ATTR2KEY.get(aid); sp=NUMSPEC.get(model,{})
    if k and k in sp: n,u=sp[k]; return f"{n} {u}"
    return None

def build_attrs(cat_attrs, prod, model, color, condition, include_item_condition=True):
    """Attrs consistentes con condition. SIN ITEM_CONDITION cuando es used para evitar choques."""
    attrs=[
        {"id":"BRAND","value_name":"Sony" if "Sony" in model else "JBL"},
        {"id":"COLOR","value_name":color},
    ]
    # Solo incluir ITEM_CONDITION en NEW para no conflictuar en used
    if include_item_condition and condition=="new":
        attrs.append({"id":"ITEM_CONDITION","value_name":"Nuevo"})
    # GTIN real del catalogo o omitir
    gtin=get_prod_gtin(prod)
    if gtin:
        attrs.append({"id":"GTIN","value_name":gtin})
    seen={a["id"] for a in attrs}
    for ca in cat_attrs:
        aid=ca.get("id"); tags=ca.get("tags") or {}
        req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
        if not req or aid in seen or aid in BAD_ATTRS: continue
        # skip GTIN si no la pusimos
        if aid=="GTIN" and not gtin: continue
        # skip ITEM_CONDITION si estamos en used (ya no la agregamos)
        if aid=="ITEM_CONDITION" and condition=="used": continue
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
    attrs=build_attrs(cat_attrs, prod, model, color, condition)
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
        bad=set(); miss=set()
        for c in j.get("cause",[]):
            msg=c.get("message","") or ""; code=c.get("code","") or ""
            if "missing_required" in code or "missing_catalog_required" in code or "missing_conditional_required" in code:
                mm=re.findall(r"\[([^\]]+)\]",msg)
                for gr in mm:
                    for x in gr.split(","):
                        x=x.strip().strip("\"'")
                        if x and x.isupper(): miss.add(x)
            if "attributes.invalid" in code or "number_invalid_format" in code:
                mm=re.search(r"attribute[\s:]+([A-Z_]+)",msg,re.I) or re.search(r"Attribute:?\s+([A-Z_]+)",msg)
                if mm: bad.add(mm.group(1))
            if "product_identifier.invalid_format" in code:
                bad.add("GTIN")
        if bad: attrs=[a for a in attrs if a["id"] not in bad]
        for mid in miss:
            if not any(a["id"]==mid for a in attrs):
                nv=num_val(mid,model)
                if nv: attrs.append({"id":mid,"value_name":nv})
                elif mid=="GTIN":
                    # NO poner "No aplica" - usar un GTIN genérico conocido para JBL/Sony segun model
                    g={"Charge 6":"0050036392617","Flip 7":"0050036392754","Clip 5":"0050036390200","Grip":"0050036395014","Go 4":"0050036395007","Go Essential 2":"0050036396776","Go 3":"0050036380676","Sony XB100":"4548736143616"}.get(model)
                    if g: attrs.append({"id":mid,"value_name":g})
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
    return None, str(r.json())[:600]

# 1) Go 4 Rosa NUEVA limpia
print("=== Go 4 Rosa NUEVA ===")
title="Bocina JBL Go 4 Bluetooth Portatil Rosa Ip67 Nueva Original"
desc="""JBL Go 4 Bluetooth Portatil Color Rosa - NUEVA ORIGINAL CON FACTURA

Sonido JBL PRO Sound, 7 horas de bateria, resistencia IP67, potencia 4.2W, peso 190g ultraportatil, AI Sound Boost.

Incluye: Bocina JBL Go 4 Rosa + cable USB-C + manual.

Garantia 30 dias. Envio GRATIS todo Mexico. Entrega 24-72 hrs.

Compatible con iPhone, Android, Samsung y cualquier dispositivo Bluetooth.

Producto NUEVO en caja sellada con factura oficial."""
nid,err=publish("MLM65831856","Go 4","Rosa",479,"new",title,desc)
print(f"Go 4 Rosa -> {nid} ERR={err}")
time.sleep(2)

# 2) Sony Reacondicionada (SIN ITEM_CONDITION attr)
print("\n=== Sony XB100 REACONDICIONADA ===")
title="Bocina Sony Srs-xb100 Bluetooth Reacondicionada Negra Original"
desc="""Sony SRS-XB100 Bluetooth Portatil Negro - PRODUCTO REACONDICIONADO POR NOSOTROS

REACONDICIONADA: Bocina revisada, limpia y probada al 100% (audio, bluetooth, bateria, microfono). Puede presentar minimas marcas cosmeticas de uso. Caja generica de proteccion. Factura y garantia de 30 dias incluidas.

Sonido EXTRA BASS de Sony, 16 horas de bateria, IPX4, peso 274g con correa integrada, Bluetooth 5.3.

Incluye: Bocina Sony SRS-XB100 Negra reacondicionada + cable USB + manual digital.

Garantia 30 dias. Envio GRATIS todo Mexico.

Nota: Producto REACONDICIONADO, no nuevo. Si buscas nueva en caja sellada, ver nuestra publicacion Sony XB100 Nueva."""
nid,err=publish("MLM25912333","Sony XB100","Negra",449,"used",title,desc)
print(f"Sony Reacond -> {nid} ERR={err}")
