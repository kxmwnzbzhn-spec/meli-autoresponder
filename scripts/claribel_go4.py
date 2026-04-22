import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_OFICIAL"]}).json()
if "access_token" not in r:
    print(f"AUTH ERR: {r}")
    raise SystemExit(1)
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
print(f"Cuenta: {me.get('nickname')} (id {me.get('id')}) email={me.get('email')}")

# 5 colores Go 4 reacondicionadas $299, stock 10 c/u, visible 1
PROD=[
    ("Go 4","Negro","MLM44731940",10),
    ("Go 4","Rojo","MLM64389753",10),
    ("Go 4","Rosa","MLM65831856",10),
    ("Go 4","Azul","MLM44731712",10),
    ("Go 4","Camuflaje",None,10),  # buscar
]

BLINDAJE="""

===== IMPORTANTE LEE ANTES DE COMPRAR =====
Producto REACONDICIONADO (no nuevo). Revisado, limpiado y probado.
RECLAMOS: Solo aceptamos cambios por defecto funcional. NO por audio subjetivo, apariencia estetica minima, ni cambio de opinion. Devolucion requiere video desempaque completo. Al comprar aceptas estas condiciones."""

def seo_title(color):
    cx = color.replace("Negro","Negra").replace("Rojo","Roja")
    return f"Bocina Jbl Go 4 Bluetooth Reacondicionada {cx} Ip67"[:60]

def seo_desc(color):
    return f"""Bocina JBL Go 4 Bluetooth Portatil - Color {color} - REACONDICIONADA con Garantia

Sonido JBL PRO Sound, 7 horas de bateria, resistencia IP67, potencia 4.2W, peso 190g ultraportatil, correa integrada.

INCLUYE: Bocina JBL Go 4 {color} reacondicionada, cable USB-C, caja generica de proteccion, factura.

ENVIO GRATIS toda Mexico. Garantia 30 dias. Entrega 24-72 hrs.

Palabras clave: jbl go 4, bocina reacondicionada, {color.lower()}, bluetooth portatil, waterproof, impermeable, economica.
{BLINDAJE}"""

GTINS={
    ("Go 4","Negro"):"6925281995194",
    ("Go 4","Rojo"):"6925281995200",
    ("Go 4","Camuflaje"):"6925281995217",
    ("Go 4","Rosa"):"6925281995224",
    ("Go 4","Azul"):"6925281995231",
}

def search_cpid(model,color):
    r=requests.get(f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q=JBL+{model.replace(' ','+')}+{color}",headers=H,timeout=15).json()
    for it in r.get("results",[])[:8]:
        nm=(it.get("name") or "").lower()
        if any(b in nm for b in ["funda","case","tester"]): continue
        if "go 4" in nm and color.lower() in nm: return it.get("id")
    return None

def get_cat_attrs(cat_id):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

def num_val(aid,model):
    NS={"bat":(7,"h"),"pwr":(4.2,"W"),"minf":(180,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")}
    M={"MAX_BATTERY_AUTONOMY":"bat","POWER_OUTPUT_RMS":"pwr","MAX_POWER":"pwr","MIN_FREQUENCY_RESPONSE":"minf","MAX_FREQUENCY_RESPONSE":"maxf","INPUT_IMPEDANCE":"imp","DISTORTION":"dis","BATTERY_VOLTAGE":"volt"}
    k=M.get(aid)
    if k and k in NS: n,u=NS[k]; return f"{n} {u}"
    return None

def publish(model,color,cpid,stock_real):
    if not cpid: cpid=search_cpid(model,color)
    cat_id="MLM59800"; pics=[]
    if cpid:
        p=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
        cat_id=p.get("category_details",{}).get("id") or "MLM59800"
        pics=[x["url"] for x in (p.get("pictures") or []) if x.get("url")]
    cat_attrs=get_cat_attrs(cat_id)
    attrs=[{"id":"BRAND","value_name":"JBL"},{"id":"COLOR","value_name":color},{"id":"MODEL","value_name":model}]
    gtin=GTINS.get((model,color))
    if gtin: attrs.append({"id":"GTIN","value_name":gtin})
    seen={a["id"] for a in attrs}
    BAD={"EAN","UPC","MPN","SELLER_SKU","ITEM_CONDITION","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT"}
    for ca in cat_attrs:
        aid=ca.get("id"); tags=ca.get("tags") or {}
        req=tags.get("required") or tags.get("catalog_required") or tags.get("conditional_required")
        if not req or aid in seen or aid in BAD: continue
        nv=num_val(aid,model)
        if nv: attrs.append({"id":aid,"value_name":nv}); seen.add(aid); continue
        vals=ca.get("values") or []; vt=ca.get("value_type")
        if aid in ("RAM_MEMORY","INTERNAL_MEMORY"):
            if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")}); seen.add(aid)
            continue
        if aid=="ALPHANUMERIC_MODEL":
            attrs.append({"id":aid,"value_name":"JBLGO4"}); seen.add(aid); continue
        BOOL_YES={"IS_SMART","WITH_BLUETOOTH","HAS_BLUETOOTH","IS_PORTABLE","IS_RECHARGEABLE","IS_WIRELESS","INCLUDES_CABLE","INCLUDES_BATTERY"}
        BOOL_NO={"IS_DUAL_VOICE_COIL","IS_DUAL_VOICE_ASSISTANTS","WITH_HANDLE","HAS_FM_RADIO","HAS_LED_LIGHTS","WITH_AUX","HAS_SD_MEMORY_INPUT","IS_WATERPROOF"}
        if vt=="boolean":
            attrs.append({"id":aid,"value_name":"Si" if aid in BOOL_YES else ("No" if aid in BOOL_NO else "No")}); seen.add(aid); continue
        if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
        elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
        else: attrs.append({"id":aid,"value_name":"No aplica"})
        seen.add(aid)
    
    body={"site_id":"MLM","title":seo_title(color),"category_id":cat_id,"price":299,"currency_id":"MXN",
          "available_quantity":1,"buying_mode":"buy_it_now","condition":"used","listing_type_id":"gold_pro",
          "catalog_listing":False,"attributes":attrs,
          "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
          "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}]}
    if cpid: body["catalog_product_id"]=cpid
    if pics: body["pictures"]=[{"source":u} for u in pics[:10]]
    
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    retry=0
    while r.status_code not in (200,201) and retry<5:
        retry+=1
        try: j=r.json()
        except: break
        bad=set(); miss=set()
        for c in j.get("cause",[]):
            msg=c.get("message","") or ""; code=c.get("code","") or ""
            if "missing" in code:
                for m_ in re.findall(r"\[([A-Z][A-Z_0-9]+)\]",msg):
                    if m_.startswith("MLM") or m_ in BAD: continue
                    if re.match(r'^[A-Z][A-Z_]+$',m_): miss.add(m_)
            if "invalid" in code or "number_invalid_format" in code:
                mm=re.search(r"[Aa]ttribute:?\s+([A-Z][A-Z_]+)",msg)
                if mm and not mm.group(1).startswith("MLM"): bad.add(mm.group(1))
            if "product_identifier.invalid_format" in code: bad.add("GTIN")
        if bad: attrs=[a for a in attrs if a["id"] not in bad]
        for mid in miss:
            if not any(a["id"]==mid for a in attrs):
                nv=num_val(mid,model)
                if nv: attrs.append({"id":mid,"value_name":nv})
                elif mid=="GTIN" and gtin: attrs.append({"id":"GTIN","value_name":gtin})
                else: attrs.append({"id":mid,"value_name":"No aplica"})
        body["attributes"]=attrs
        r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    if r.status_code in (200,201):
        nid=r.json().get("id")
        requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":seo_desc(color)},timeout=15)
        return nid, None
    return None, str(r.json())[:400]

# cargar stock_config si existe en Claribel (usar archivo separado)
CFG_FILE="stock_config_oficial.json"
try:
    with open(CFG_FILE) as f: sc=json.load(f)
except: sc={}

ok=0; err=0
for model,color,cpid,stock in PROD:
    print(f"\n=== {model} {color} $299 stock={stock} ===")
    nid,e=publish(model,color,cpid,stock)
    if nid:
        print(f"  OK -> {nid}")
        sc[nid]={"real_stock":stock,"sku":f"REACOND-{model.replace(' ','')}-{color.upper()}","label":f"{model} {color} Reacond (Claribel)","auto_replenish":True,"replenish_quantity":1,"min_visible_stock":1,"account":"oficial"}
        ok+=1
    else:
        print(f"  ERR: {e}")
        err+=1
    time.sleep(2)

with open(CFG_FILE,"w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print(f"\n=== {ok} OK, {err} ERR ===")
