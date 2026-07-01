"""
Clonar 23 items específicos de Mayrely Caamal → Mildred Guadalupe.
- 20 catálogo (catalog_listing) - reusar CPID + precio dado
- 3 tradicional USADOS - clonar completo
- Stock visible: 1
- Auto stock activo (priority_replenish qty=1)
- Precios respetados según lista del usuario
"""
import os, requests, json, time

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT_MC=os.environ["MELI_REFRESH_TOKEN_MC"]
RT_MI=os.environ["MELI_REFRESH_TOKEN_MILDRED"]
SB_URL=os.environ.get("SUPABASE_URL","")
SB_KEY=os.environ.get("SUPABASE_SERVICE_KEY","")

# 20 CATÁLOGO: (source_item_id, precio_target)
CATALOGO=[
    ("MLM3059642403",1199),  # Bose Soundlink Home Silver
    ("MLM3045612883",2290),  # JBL Charge 6 Negro
    ("MLM3045609843",499),   # JBL Go 4 Rosa Pálido/Turquesa
    ("MLM3045613145",1199),  # Beats Pill Negro Reacond
    ("MLM5569408564",1199),  # Beats Pill Rojo Reacond
    ("MLM3045615611",699),   # Sony SRS-XB100 Negro
    ("MLM5569282738",499),   # JBL Go 4 Celeste
    ("MLM3045514191",499),   # JBL Go 4 Negra
    ("MLM3045607131",499),   # JBL Go 4 Roja
    ("MLM5569359030",1199),  # Marshall Emberton Negro Reacond
    ("MLM5569400988",499),   # JBL Go 4 Camuflaje
    ("MLM3045609271",499),   # JBL Go 4 Rosa Dzyp
    ("MLM5569353088",499),   # JBL Go 4 Rojo
    ("MLM5569443994",1999),  # JBL Charge 6 Negro
    ("MLM5569353878",499),   # JBL Go 4 Rosado
    ("MLM5569444970",999),   # Marshall Willen II Reacond
    ("MLM5569443364",2050),  # JBL Charge 6 Negro Portátil
    ("MLM5569350350",504),   # JBL Go 4 Negro
    ("MLM3045606657",599),   # JBL Go 4 Camuflado
    ("MLM5569446604",690),   # Sony SRS-XB100 Negro
]

# 3 TRADICIONAL USADAS: (source_item_id, precio_target)
TRADICIONAL=[
    ("MLM5575746082",299),  # JBL Go 4 USADA
    ("MLM5586829422",499),  # JBL Charge 6 USADA
    ("MLM3054168351",399),  # JBL Clip 5 USADA
]

def get_token(rt):
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt},timeout=20).json()
    return r["access_token"], r.get("refresh_token",rt)

# Auth
AT_MC,_=get_token(RT_MC)
AT_MI,_=get_token(RT_MI)
H_MC={"Authorization":f"Bearer {AT_MC}","Content-Type":"application/json"}
H_MI={"Authorization":f"Bearer {AT_MI}","Content-Type":"application/json"}
me_mi=requests.get("https://api.mercadolibre.com/users/me",headers=H_MI,timeout=10).json()
print(f"Destino Mildred: {me_mi.get('nickname')} ({me_mi.get('id')})",flush=True)

results={"catalogo":[],"tradicional":[],"fail":[]}

# ============ CATÁLOGO ============
print(f"\n=== Publicando {len(CATALOGO)} CATÁLOGO ===",flush=True)
for src_id,price in CATALOGO:
    try:
        src=requests.get(f"https://api.mercadolibre.com/items/{src_id}?attributes=id,catalog_product_id,category_id,title",headers=H_MC,timeout=10).json()
        cpid=src.get("catalog_product_id")
        if not cpid:
            results["fail"].append({"src":src_id,"reason":"no CPID"})
            print(f"  {src_id} FAIL: no cpid",flush=True)
            continue
        payload={
            "catalog_listing":True,
            "catalog_product_id":cpid,
            "category_id":src.get("category_id","MLM59800"),
            "price":price,
            "currency_id":"MXN",
            "buying_mode":"buy_it_now",
            "listing_type_id":"gold_pro",
            "condition":"new",
            "available_quantity":1,
        }
        r=requests.post("https://api.mercadolibre.com/items",headers=H_MI,json=payload,timeout=30)
        if r.status_code in (200,201):
            new=r.json()
            results["catalogo"].append({"src":src_id,"new":new.get("id"),"cpid":cpid,"price":price,"status":new.get("status")})
            print(f"  {src_id} → {new.get('id')} ${price} status={new.get('status')}",flush=True)
        else:
            results["fail"].append({"src":src_id,"reason":r.text[:180]})
            print(f"  {src_id} FAIL {r.status_code}: {r.text[:120]}",flush=True)
        time.sleep(3)
    except Exception as e:
        results["fail"].append({"src":src_id,"reason":str(e)})
        print(f"  {src_id} EXC: {e}",flush=True)

# ============ TRADICIONAL USADAS ============
print(f"\n=== Publicando {len(TRADICIONAL)} TRADICIONAL USADAS ===",flush=True)
for src_id,price in TRADICIONAL:
    try:
        src=requests.get(f"https://api.mercadolibre.com/items/{src_id}?include_attributes=all",headers=H_MC,timeout=15).json()
        # Get description
        desc_r=requests.get(f"https://api.mercadolibre.com/items/{src_id}/description",headers=H_MC,timeout=10)
        desc_text=desc_r.json().get("plain_text","") if desc_r.status_code==200 else ""
        
        # Build payload
        attrs=[]
        for a in src.get("attributes",[]):
            aid=a.get("id"); v=a.get("value_name")
            if not aid or not v: continue
            if aid in ("ITEM_CONDITION","SELLER_SKU","UPC","UPC_ID","CATALOG_PRODUCT_ID","EMPTY_GTIN_REASON","IS_EMERGING_BRAND","IS_TOM_BRAND","IS_HIGHLIGHT_BRAND","AGE_GROUP"): continue
            attrs.append({"id":aid,"value_name":v})
        
        payload={
            "title":src.get("title"),
            "category_id":src.get("category_id"),
            "price":price,
            "currency_id":"MXN",
            "available_quantity":1,
            "buying_mode":"buy_it_now",
            "listing_type_id":"gold_pro",
            "condition":src.get("condition","used"),
            "pictures":[{"source":p.get("secure_url") or p.get("url")} for p in src.get("pictures",[])[:12]],
            "attributes":attrs,
            "sale_terms":src.get("sale_terms",[]),
        }
        r=requests.post("https://api.mercadolibre.com/items",headers=H_MI,json=payload,timeout=30)
        if r.status_code in (200,201):
            new=r.json()
            new_id=new.get("id")
            results["tradicional"].append({"src":src_id,"new":new_id,"price":price,"status":new.get("status")})
            print(f"  {src_id} → {new_id} ${price} status={new.get('status')}",flush=True)
            # Set description
            if desc_text and new_id:
                requests.post(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H_MI,json={"plain_text":desc_text},timeout=15)
        else:
            results["fail"].append({"src":src_id,"reason":r.text[:180]})
            print(f"  {src_id} FAIL {r.status_code}: {r.text[:120]}",flush=True)
        time.sleep(3)
    except Exception as e:
        results["fail"].append({"src":src_id,"reason":str(e)})
        print(f"  {src_id} EXC: {e}",flush=True)

# ============ Supabase: priority_replenish ============
print(f"\n=== Registrando en Supabase priority_replenish ===",flush=True)
if SB_URL and SB_KEY:
    SBH={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"return=minimal"}
    all_new=results["catalogo"]+results["tradicional"]
    for x in all_new:
        if x.get("new"):
            body={"account":"MILDRED","item_id":x["new"],"default_qty":1,"product_name":x.get("src",""),"reason":"Auto stock continuo - clonado desde Mayrely"}
            requests.post(f"{SB_URL}/rest/v1/meli_priority_replenish",headers=SBH,json=body,timeout=10)
    print(f"  Registradas {len(all_new)} entradas priority_replenish",flush=True)

# Summary
print(f"\n=== SUMMARY ===",flush=True)
print(f"CATÁLOGO OK: {len(results['catalogo'])} / {len(CATALOGO)}",flush=True)
print(f"TRADICIONAL OK: {len(results['tradicional'])} / {len(TRADICIONAL)}",flush=True)
print(f"FAILS: {len(results['fail'])}",flush=True)
print(json.dumps(results,indent=2),flush=True)

# Also write to Supabase for retrieval
if SB_URL and SB_KEY:
    SBH={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json"}
    for x in results["catalogo"]+results["tradicional"]:
        body={"account":"MILDRED","scope":"item","scope_value":x.get("new",""),"directive_type":"clone_from_mayrely","raw_user_message":f"Clonado {x.get('src')} → {x.get('new')} ${x.get('price')}"}
        requests.post(f"{SB_URL}/rest/v1/meli_user_directives",headers=SBH,json=body,timeout=10)
