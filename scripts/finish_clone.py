import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H_JUAN={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_OFICIAL"]}).json()
H_CLA={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

try:
    with open("stock_config_oficial.json") as f: sc=json.load(f)
except: sc={}
already_cloned = {v.get("cloned_from") for v in sc.values() if v.get("cloned_from")}

BLINDAJE_PERF="""

===== AVISO IMPORTANTE =====
Producto 100% ORIGINAL con factura autorizada. RECLAMOS: Solo por producto dañado o diferente. NO por percepcion subjetiva de aroma, duracion ni preferencias. Video desempaque requerido. Al comprar aceptas estas condiciones."""

BLINDAJE_BOC="""

===== IMPORTANTE LEE ANTES DE COMPRAR =====
REACONDICIONADA. Revisada y probada. Garantia 30 dias por defecto funcional. NO aceptamos reclamos por audio subjetivo ni por app oficial (es OEM, NO compat con app JBL Portable). Video desempaque obligatorio."""

def get_cat_attrs(cat_id, H):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15)
    return r.json() if r.status_code==200 else []

def num_val(aid,model):
    NS={
        "Charge 6":{"bat":(28,"h"),"pwr":(40,"W"),"minf":(60,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
        "Flip 7":{"bat":(16,"h"),"pwr":(35,"W"),"minf":(60,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
        "Clip 5":{"bat":(12,"h"),"pwr":(7,"W"),"minf":(110,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
        "Grip":{"bat":(12,"h"),"pwr":(8,"W"),"minf":(110,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(0.5,"%"),"volt":(5,"V")},
        "Go 4":{"bat":(7,"h"),"pwr":(4.2,"W"),"minf":(180,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
        "Go 3":{"bat":(5,"h"),"pwr":(4.2,"W"),"minf":(110,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
        "Go Essential 2":{"bat":(7,"h"),"pwr":(3.1,"W"),"minf":(180,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
        "Sony XB100":{"bat":(16,"h"),"pwr":(10,"W"),"minf":(100,"Hz"),"maxf":(20,"kHz"),"imp":(4,"Ω"),"dis":(1,"%"),"volt":(5,"V")},
    }
    M={"MAX_BATTERY_AUTONOMY":"bat","POWER_OUTPUT_RMS":"pwr","MAX_POWER":"pwr","MIN_FREQUENCY_RESPONSE":"minf","MAX_FREQUENCY_RESPONSE":"maxf","INPUT_IMPEDANCE":"imp","DISTORTION":"dis","BATTERY_VOLTAGE":"volt"}
    k=M.get(aid); sp=NS.get(model,{})
    if k and k in sp: n,u=sp[k]; return f"{n} {u}"
    return None

GTINS={
    ("Flip 7","Negro"):"6925281992384",("Flip 7","Negra"):"6925281992384",
    ("Flip 7","Azul"):"6925281992407",("Flip 7","Morado"):"6925281992414",
    ("Flip 7","Morada"):"6925281992414",("Flip 7","Rojo"):"6925281992391",
    ("Flip 7","Roja"):"6925281992391",
    ("Go 4","Negro"):"6925281995194",("Go 4","Negra"):"6925281995194",
    ("Go 4","Rojo"):"6925281995200",("Go 4","Roja"):"6925281995200",
    ("Go 4","Camuflaje"):"6925281995217",("Go 4","Rosa"):"6925281995224",
    ("Go 4","Azul"):"6925281995231",("Go 4","Azul Marino"):"6925281995231",
    ("Clip 5","Negro"):"6925281993954",("Clip 5","Negra"):"6925281993954",
    ("Clip 5","Morado"):"6925281993961",("Clip 5","Morada"):"6925281993961",
    ("Clip 5","Rosa"):"6925281993978",
    ("Charge 6","Rojo"):"6925281943225",("Charge 6","Roja"):"6925281943225",
    ("Charge 6","Azul"):"6925281943140",("Charge 6","Camuflaje"):"6925281943102",
    ("Charge 6","Negro"):"6925281943119",("Charge 6","Negra"):"6925281943119",
    ("Grip","Negro"):"6925281979880",("Grip","Negra"):"6925281979880",
    ("Go 3","Negro"):"6925281981975",("Go 3","Negra"):"6925281981975",
    ("Sony XB100","Negro"):"4548736143616",("Sony XB100","Negra"):"4548736143616",
}

def parse_model_color(title):
    t=title.lower()
    model=None; color=None
    if "charge 6" in t: model="Charge 6"
    elif "flip 7" in t: model="Flip 7"
    elif "clip 5" in t: model="Clip 5"
    elif "grip" in t: model="Grip"
    elif "go essential" in t: model="Go Essential 2"
    elif "go 4" in t: model="Go 4"
    elif "go 3" in t: model="Go 3"
    elif "xb100" in t or "sony srs" in t: model="Sony XB100"
    # prio colores "completos" antes
    for raw,nrm in [("azul marino","Azul Marino"),("camuflaje","Camuflaje"),("morado","Morado"),("morada","Morada"),("violeta","Morada"),("negra","Negra"),("negro","Negro"),("rojo","Rojo"),("roja","Roja"),("rosa","Rosa"),("azul","Azul")]:
        if raw in t and "bluetooth" not in (raw): color=nrm; break
    return model,color

def publish_bocina(full_juan):
    iid=full_juan.get("id")
    title=full_juan.get("title","")
    price=full_juan.get("price")
    cat_id=full_juan.get("category_id") or "MLM59800"
    cpid=full_juan.get("catalog_product_id")
    cond=full_juan.get("condition","used")
    pics=[p["url"] for p in (full_juan.get("pictures") or []) if p.get("url")]
    
    model,color = parse_model_color(title)
    if not model or not color:
        return None, f"no model/color parsed from {title[:40]}"
    
    gtin = GTINS.get((model,color))
    attrs=[
        {"id":"BRAND","value_name":"Sony" if "Sony" in model else "JBL"},
        {"id":"COLOR","value_name":color},
        {"id":"MODEL","value_name":model},
    ]
    if gtin: attrs.append({"id":"GTIN","value_name":gtin})
    if cond=="new":
        attrs.append({"id":"ITEM_CONDITION","value_name":"Nuevo"})
    
    cat_attrs=get_cat_attrs(cat_id,H_CLA)
    seen={a["id"] for a in attrs}
    BAD={"EAN","UPC","MPN","SELLER_SKU","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT"}
    if cond=="used": BAD=BAD|{"ITEM_CONDITION"}
    
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
            attrs.append({"id":aid,"value_name":f"JBL{model.replace(' ','')}" if "Sony" not in model else "SRS-XB100"}); seen.add(aid); continue
        BY={"IS_SMART","WITH_BLUETOOTH","HAS_BLUETOOTH","IS_PORTABLE","IS_RECHARGEABLE","IS_WIRELESS","INCLUDES_CABLE","INCLUDES_BATTERY"}
        BN={"IS_DUAL_VOICE_COIL","IS_DUAL_VOICE_ASSISTANTS","WITH_HANDLE","HAS_FM_RADIO","HAS_LED_LIGHTS","WITH_AUX","HAS_SD_MEMORY_INPUT","IS_WATERPROOF"}
        if vt=="boolean":
            attrs.append({"id":aid,"value_name":"Si" if aid in BY else ("No" if aid in BN else "No")}); seen.add(aid); continue
        if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
        elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
        else: attrs.append({"id":aid,"value_name":"No aplica"})
        seen.add(aid)
    
    body={
        "site_id":"MLM","title":title[:60],"category_id":cat_id,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","condition":cond,"listing_type_id":"gold_pro",
        "catalog_listing":False,"attributes":attrs,
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}]
    }
    if cpid: body["catalog_product_id"]=cpid
    if pics: body["pictures"]=[{"source":u} for u in pics[:10]]
    
    r=requests.post("https://api.mercadolibre.com/items",headers=H_CLA,json=body,timeout=30)
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
                    if m_.startswith("MLM") or m_ in BAD: continue
                    if re.match(r'^[A-Z][A-Z_]+$',m_): miss.add(m_)
            if "invalid" in code or "omitted" in code or "number_invalid_format" in code:
                mm=re.search(r"[Aa]ttribute:?\s+([A-Z][A-Z_]+)",msg)
                if mm and not mm.group(1).startswith("MLM"): bad.add(mm.group(1))
            if "product_identifier.invalid_format" in code: bad.add("GTIN")
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
        body["attributes"]=attrs
        r=requests.post("https://api.mercadolibre.com/items",headers=H_CLA,json=body,timeout=30)
    
    if r.status_code in (200,201):
        nid=r.json().get("id")
        desc=f"{title} - REACONDICIONADA. Sonido potente, garantia 30 dias, envio gratis."+BLINDAJE_BOC
        requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H_CLA,json={"plain_text":desc},timeout=15)
        return nid, None
    return None, str(r.json())[:400]

def publish_perfume(full_juan):
    iid=full_juan.get("id")
    title=full_juan.get("title","")[:60]
    price=full_juan.get("price")
    cat_id=full_juan.get("category_id") or "MLM159230"
    cpid=full_juan.get("catalog_product_id")
    pics=[p["url"] for p in (full_juan.get("pictures") or []) if p.get("url")]
    attrs_raw=full_juan.get("attributes") or []
    
    BAD={"SELLER_SKU","MPN","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT"}
    attrs=[]
    for a in attrs_raw:
        aid=a.get("id")
        if aid in BAD: continue
        vid=a.get("value_id"); vn=a.get("value_name")
        if not vid and not vn: continue
        e={"id":aid}
        if vid: e["value_id"]=vid
        if vn: e["value_name"]=vn
        attrs.append(e)
    
    # Sale terms with business_conditions
    sale_terms=[
        {"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 dias"},
    ]
    
    body={
        "site_id":"MLM","title":title,"category_id":cat_id,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","condition":"new","listing_type_id":"gold_pro",
        "catalog_listing":False,"attributes":attrs,
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
        "sale_terms":sale_terms
    }
    if cpid: body["catalog_product_id"]=cpid
    if pics: body["pictures"]=[{"source":u} for u in pics[:10]]
    
    r=requests.post("https://api.mercadolibre.com/items",headers=H_CLA,json=body,timeout=30)
    retry=0
    while r.status_code not in (200,201) and retry<5:
        retry+=1
        try: j=r.json()
        except: break
        bad=set(); miss=set(); bad_sale=False
        for c in j.get("cause",[]):
            msg=c.get("message","") or ""; code=c.get("code","") or ""
            if "business_condition" in code.lower() or "business_condition" in msg.lower():
                bad_sale=True
            if "missing" in code:
                for m_ in re.findall(r"\[([A-Z][A-Z_0-9]+)\]",msg):
                    if m_.startswith("MLM") or m_ in BAD: continue
                    miss.add(m_)
            if "invalid" in code or "omitted" in code:
                mm=re.search(r"[Aa]ttribute:?\s+([A-Z][A-Z_]+)",msg)
                if mm and not mm.group(1).startswith("MLM"): bad.add(mm.group(1))
        if bad_sale:
            body["sale_terms"]=[]
        if bad: attrs=[a for a in attrs if a["id"] not in bad]
        for mid in miss:
            if not any(a["id"]==mid for a in attrs):
                attrs.append({"id":mid,"value_name":"No aplica"})
        body["attributes"]=attrs
        r=requests.post("https://api.mercadolibre.com/items",headers=H_CLA,json=body,timeout=30)
    
    if r.status_code in (200,201):
        nid=r.json().get("id")
        dr=requests.get(f"https://api.mercadolibre.com/items/{iid}/description",headers=H_JUAN,timeout=15)
        desc=""
        if dr.status_code==200:
            try: desc=dr.json().get("plain_text","")
            except: pass
        if not desc: desc=f"{title} - 100% original con factura. Garantia 30 dias. Envio GRATIS."
        if "AVISO IMPORTANTE" not in desc: desc += BLINDAJE_PERF
        requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H_CLA,json={"plain_text":desc},timeout=15)
        return nid, None
    return None, str(r.json())[:400]

# ETAPA 1: perfumes pendientes
print("=== ETAPA 1: Perfumes pendientes ===")
with open("juan_perfumes.json") as f: perfumes=json.load(f)
def norm(s): return " ".join(s.lower().split())
seen={}
for p in perfumes:
    t=norm(p.get("title",""))
    if t in seen:
        if seen[t].get("status")!="active" and p.get("status")=="active": seen[t]=p
    else: seen[t]=p
uniq=[p for p in seen.values() if p.get("id") not in already_cloned]
print(f"Perfumes pendientes: {len(uniq)}")
MAX_PER=int(os.environ.get("MAX_PERF",20))
ok_p=0; err_p=0
for p in uniq[:MAX_PER]:
    full=requests.get(f"https://api.mercadolibre.com/items/{p.get('id')}",headers=H_JUAN,timeout=15).json()
    nid,err=publish_perfume(full)
    if nid:
        print(f"  OK {p.get('id')} -> {nid}")
        sc[nid]={"real_stock":1,"label":p.get("title","")[:50],"auto_replenish":False,"account":"oficial","cloned_from":p.get("id")}
        ok_p+=1
    else:
        print(f"  ERR {p.get('id')}: {err[:180]}")
        err_p+=1
    time.sleep(2)

# ETAPA 2: bocinas tradicionales
print(f"\n=== ETAPA 2: Bocinas tradicionales ===")
with open("juan_bocinas.json") as f: bocinas=json.load(f)
seen={}
for b in bocinas:
    t=norm(b.get("title",""))
    if t in seen:
        if seen[t].get("status")!="active" and b.get("status")=="active": seen[t]=b
    else: seen[t]=b
# Solo tradicionales
uniq_b=[b for b in seen.values() if not b.get("catalog_listing") and b.get("id") not in already_cloned and b.get("id") not in {v.get("cloned_from") for v in sc.values()}]
print(f"Bocinas tradicionales pendientes: {len(uniq_b)}")
MAX_BOC=int(os.environ.get("MAX_BOC",20))
ok_b=0; err_b=0
for b in uniq_b[:MAX_BOC]:
    full=requests.get(f"https://api.mercadolibre.com/items/{b.get('id')}",headers=H_JUAN,timeout=15).json()
    nid,err=publish_bocina(full)
    if nid:
        print(f"  OK {b.get('id')} -> {nid}")
        sc[nid]={"real_stock":1,"label":b.get("title","")[:50],"auto_replenish":False,"account":"oficial","cloned_from":b.get("id")}
        ok_b+=1
    else:
        print(f"  ERR {b.get('id')}: {err[:180]}")
        err_b+=1
    time.sleep(2)

with open("stock_config_oficial.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print(f"\n=== TOTAL: Perfumes {ok_p}/{ok_p+err_p} OK, Bocinas {ok_b}/{ok_b+err_b} OK ===")
