import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H_JUAN={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_OFICIAL"]}).json()
H_CLA={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
print(f"Claribel: {requests.get('https://api.mercadolibre.com/users/me',headers=H_CLA).json().get('nickname')}")

# Cargar perfumes Juan y dedupear inline
with open("juan_perfumes.json") as f: perfumes=json.load(f)
def norm(s): return " ".join(s.lower().split())
seen={}
for p in perfumes:
    t=norm(p.get("title",""))
    if t in seen:
        if seen[t].get("status")!="active" and p.get("status")=="active": seen[t]=p
    else:
        seen[t]=p
uniq=list(seen.values())
print(f"Total perfumes unicos: {len(uniq)}")

try:
    with open("stock_config_oficial.json") as f: sc=json.load(f)
except: sc={}

# Evitar re-subir si ya clonamos
already_cloned_from = {v.get("cloned_from") for v in sc.values() if v.get("cloned_from")}
uniq = [p for p in uniq if p.get("id") not in already_cloned_from]
print(f"Pendientes de clonar: {len(uniq)}")

BLINDAJE="""

===== AVISO IMPORTANTE =====
Producto 100% ORIGINAL con factura de comercializadora autorizada.
RECLAMOS: Solo aceptamos cambios por producto dañado en envio o diferente al anunciado. NO por percepcion subjetiva de aroma, duracion o preferencias personales. Devoluciones requieren video sin cortes del desempaque. Al comprar aceptas estas condiciones."""

START=int(os.environ.get("START",0))
BATCH=15
END=min(START+BATCH,len(uniq))
print(f"Clonando {START}..{END-1} de {len(uniq)}")

ok=0; err=0
for idx,p in enumerate(uniq[START:END]):
    iid=p.get("id")
    full=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H_JUAN,timeout=15).json()
    dreq=requests.get(f"https://api.mercadolibre.com/items/{iid}/description",headers=H_JUAN,timeout=15)
    desc=""
    if dreq.status_code==200:
        try: desc=dreq.json().get("plain_text","")
        except: pass
    
    title=full.get("title","")[:60]
    price=full.get("price")
    cat_id=full.get("category_id") or "MLM159230"
    cpid=full.get("catalog_product_id")
    pics=[pp["url"] for pp in (full.get("pictures") or []) if pp.get("url")]
    attrs_raw=full.get("attributes") or []
    
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
    
    if not desc:
        desc=f"{title} - 100% original con factura. Garantia 30 dias. Envio GRATIS."
    if "AVISO IMPORTANTE" not in desc: desc += BLINDAJE
    
    body={
        "site_id":"MLM","title":title,"category_id":cat_id,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","condition":"new","listing_type_id":"gold_pro",
        "catalog_listing":False,"attributes":attrs,
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]},
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantia del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 dias"}]
    }
    if cpid: body["catalog_product_id"]=cpid
    if pics: body["pictures"]=[{"source":u} for u in pics[:10]]
    
    r=requests.post("https://api.mercadolibre.com/items",headers=H_CLA,json=body,timeout=30)
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
                    miss.add(m_)
            if "invalid" in code or "omitted" in code:
                mm=re.search(r"[Aa]ttribute:?\s+([A-Z][A-Z_]+)",msg)
                if mm and not mm.group(1).startswith("MLM"): bad.add(mm.group(1))
            if "product_identifier.invalid_format" in code: bad.add("GTIN")
        if bad: attrs=[a for a in attrs if a["id"] not in bad]
        for mid in miss:
            if not any(a["id"]==mid for a in attrs):
                attrs.append({"id":mid,"value_name":"No aplica"})
        body["attributes"]=attrs
        r=requests.post("https://api.mercadolibre.com/items",headers=H_CLA,json=body,timeout=30)
    
    if r.status_code in (200,201):
        nid=r.json().get("id")
        requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H_CLA,json={"plain_text":desc},timeout=15)
        print(f"  OK {iid} -> {nid} | {title[:40]}")
        sc[nid]={"real_stock":1,"label":title[:50],"auto_replenish":False,"min_visible_stock":1,"account":"oficial","cloned_from":iid}
        ok+=1
    else:
        print(f"  ERR {iid} {title[:40]}: {str(r.json())[:200]}")
        err+=1
    time.sleep(2)

with open("stock_config_oficial.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print(f"\n{ok} OK, {err} ERR de {END-START} intentados")
