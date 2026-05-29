import os, requests, time, json
API="https://api.mercadolibre.com"

# Plan generado desde Supabase: meli_catalog_strategy x listings (mejor fuente)
# Cada entrada: (alegra_ref, sku, cpid, source_mlm, source_secret, claribel_existing_mlm, claribel_status)
PLAN=[
 ("ELEC-009","JBL-GO4-CAMUFLAJE","MLM37361021","MLM2890856611","MELI_REFRESH_TOKEN_JUAN",None,None),
 ("ELEC-009","JBL-GO4-CAMUFLAJE","MLM43902928","MLM5351937060","MELI_REFRESH_TOKEN_WILBERT",None,None),
 ("ELEC-010","JBL-GO4-ROJO","MLM44710313","MLM5354755946","MELI_REFRESH_TOKEN_WILBERT",None,None),
 ("ELEC-010","JBL-GO4-ROJO","MLM45577570","MLM2904767843","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-010","JBL-GO4-ROJO","MLM46998439","MLM2904693425","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-010","JBL-GO4-ROJO","MLM47119316","MLM2910768369","MELI_REFRESH_TOKEN_WILBERT",None,None),
 ("ELEC-010","JBL-GO4-ROJO","MLM48666693","MLM2904680353","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-010","JBL-GO4-ROJO","MLM58850976","MLM2904704725","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-010","JBL-GO4-ROJO","MLM64389753","MLM2914422351","MELI_REFRESH_TOKEN_WILBERT",None,None),
 ("ELEC-011","JBL-CLIP5-AZUL","MLM37110751","MLM2904687747","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-011","JBL-CLIP5-AZUL","MLM40329314","MLM2904765865","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-011","JBL-CLIP5-AZUL","MLM58592190","MLM2967312395","MELI_REFRESH_TOKEN_CLARIBEL","MLM2967312395","active"),
 ("ELEC-011","JBL-CLIP5-AZUL","MLM61825899","MLM2904678391","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-012","JBL-CLIP5-MORADO","MLM44573520","MLM2904678397","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-012","JBL-CLIP5-MORADO","MLM44712007","MLM2904691313","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-012","JBL-CLIP5-MORADO","MLM44714111","MLM2967312403","MELI_REFRESH_TOKEN_CLARIBEL","MLM2967312403","active"),
 ("ELEC-012","JBL-CLIP5-MORADO","MLM45586155","MLM2904678413","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-012","JBL-CLIP5-MORADO","MLM47145951","MLM2904702707","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-012","JBL-CLIP5-MORADO","MLM49054893","MLM2904702703","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-013","JBL-GO3-NEGRO","MLM29147620","MLM2910806881","MELI_REFRESH_TOKEN_WILBERT",None,None),
 ("ELEC-013","JBL-GO3-NEGRO","MLM37158857","MLM2904680453","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-013","JBL-GO3-NEGRO","MLM37197513","MLM2904767915","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-013","JBL-GO3-NEGRO","MLM44709174","MLM2910806845","MELI_REFRESH_TOKEN_WILBERT",None,None),
 ("ELEC-013","JBL-GO3-NEGRO","MLM44709179","MLM2967299579","MELI_REFRESH_TOKEN_CLARIBEL","MLM2967299579","active"),
 ("ELEC-013","JBL-GO3-NEGRO","MLM44710730","MLM2904767905","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-013","JBL-GO3-NEGRO","MLM44728420","MLM2904680479","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-013","JBL-GO3-NEGRO","MLM44744958","MLM2904693443","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-013","JBL-GO3-NEGRO","MLM44799641","MLM2904704727","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-013","JBL-GO3-NEGRO","MLM46039390","MLM2904693461","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-014","SONY-XB100-NEGRO","MLM25912333","MLM5245310498","MELI_REFRESH_TOKEN_CLARIBEL","MLM5245310498","active"),
 ("ELEC-018","JBL-CLIP5-CAMUFLAJE","MLM44712057","MLM5337919270","MELI_REFRESH_TOKEN_WILBERT",None,None),
 ("ELEC-018","JBL-CLIP5-CAMUFLAJE","MLM44714150","MLM2904674811","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-018","JBL-CLIP5-CAMUFLAJE","MLM48157832","MLM5337919282","MELI_REFRESH_TOKEN_WILBERT",None,None),
 ("ELEC-018","JBL-CLIP5-CAMUFLAJE","MLM58616124","MLM5337919290","MELI_REFRESH_TOKEN_WILBERT",None,None),
 ("ELEC-021","BOSE-SOUNDLINK-HOME-NEGRO","MLM49963786","MLM5297098664","MELI_REFRESH_TOKEN_WILBERT",None,None),
 ("ELEC-025","BOSE-SOUNDLINK-HOME-SILVER","MLM50131488","MLM5297087174","MELI_REFRESH_TOKEN_WILBERT",None,None),
 ("ELEC-027","JBL-GO4-ROSA","MLM2019694299","MLM5244765752","MELI_REFRESH_TOKEN_JUAN",None,None),
 ("ELEC-027","JBL-GO4-ROSA","MLM45530822","MLM5246077448","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-027","JBL-GO4-ROSA","MLM45700101","MLM2910768325","MELI_REFRESH_TOKEN_WILBERT",None,None),
 ("ELEC-027","JBL-GO4-ROSA","MLM65831856","MLM2910768335","MELI_REFRESH_TOKEN_WILBERT",None,None),
 ("ELEC-029","JBL-CLIP5-ROSA","MLM63875183","MLM2904691353","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-029","JBL-CLIP5-ROSA","MLM64288232","MLM2904765913","MELI_REFRESH_TOKEN_RAYMUNDO",None,None),
 ("ELEC-030","JBL-GO4-AQUA","MLM61262890","MLM2910457917","MELI_REFRESH_TOKEN_WILBERT",None,None),
]

# Tokens cache
TOK={}
NEWRT={}
def get_h(secret_env):
    if secret_env in TOK: return TOK[secret_env]
    r=requests.post(f"{API}/oauth/token",data={
        "grant_type":"refresh_token",
        "client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],
        "refresh_token":os.environ[secret_env]
    },timeout=20).json()
    NEWRT[secret_env]=r.get("refresh_token")
    H={"Authorization":f"Bearer {r['access_token']}"}
    TOK[secret_env]=H
    return H

HC=get_h("MELI_REFRESH_TOKEN_CLARIBEL")
HJC={**HC,"Content-Type":"application/json"}
print(f"Tokens loaded. NEW_RT: {NEWRT}")

results={"published":[],"reactivated":[],"sku_set":[],"failed":[]}
for idx,(alegra,sku,cpid,src_mlm,src_secret,clb_mlm,clb_status) in enumerate(PLAN,1):
    prefix=f"[{idx}/{len(PLAN)}] {alegra} {sku} {cpid}"
    # Case A: Claribel already has it -> reactivate + set SKU
    if clb_mlm:
        # verify live status
        g=requests.get(f"{API}/items/{clb_mlm}",headers=HC,timeout=20).json()
        live_st=g.get("status")
        # set SELLER_SKU
        requests.put(f"{API}/items/{clb_mlm}",headers=HJC,json={"attributes":[{"id":"SELLER_SKU","value_name":alegra}]},timeout=20)
        if live_st!="active":
            r2=requests.put(f"{API}/items/{clb_mlm}",headers=HJC,json={"status":"active","available_quantity":1},timeout=30)
            if r2.status_code in (200,201):
                results["reactivated"].append((alegra,cpid,clb_mlm))
                print(f"  {prefix} -> REACTIVATED {clb_mlm} (was {live_st})")
            else:
                results["failed"].append((alegra,cpid,clb_mlm,f"reactivate {r2.status_code} {r2.text[:120]}"))
                print(f"  {prefix} -> ERR {r2.status_code} {r2.text[:120]}")
        else:
            results["sku_set"].append((alegra,cpid,clb_mlm))
            print(f"  {prefix} -> already active {clb_mlm}, SKU set")
        time.sleep(0.4)
        continue
    
    # Case B: publish new in Claribel using source item to get category_id + title + price
    H_src=get_h(src_secret)
    src=requests.get(f"{API}/items/{src_mlm}",headers=H_src,params={"attributes":"title,category_id,price,domain_id"},timeout=20).json()
    cat=src.get("category_id")
    title=(src.get("title") or "")[:60]
    price=src.get("price") or 499
    if not cat:
        results["failed"].append((alegra,cpid,None,f"no_cat_from_src_{src_mlm}"))
        print(f"  {prefix} -> SKIP no cat from src {src_mlm}")
        continue
    payload={
        "site_id":"MLM","title":title,"category_id":cat,
        "price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now",
        "listing_type_id":"gold_pro","condition":"new",
        "catalog_product_id":cpid,"catalog_listing":True,
        "shipping":{"mode":"me2","free_shipping":True},
        "attributes":[{"id":"SELLER_SKU","value_name":alegra}]
    }
    r=requests.post(f"{API}/items",headers=HJC,json=payload,timeout=40)
    if r.status_code in (200,201):
        d=r.json()
        results["published"].append((alegra,cpid,d["id"],d.get("status"),d.get("price")))
        print(f"  {prefix} -> PUB {d['id']} ${d.get('price')} ({d.get('status')})")
    else:
        results["failed"].append((alegra,cpid,None,f"{r.status_code} {r.text[:250]}"))
        print(f"  {prefix} -> FAIL {r.status_code} {r.text[:250]}")
    time.sleep(1.0)

print(f"\n=== RESUMEN === published={len(results['published'])} reactivated={len(results['reactivated'])} sku_set={len(results['sku_set'])} failed={len(results['failed'])}")
print(f"\nNEW_RTS={json.dumps(NEWRT)}")
print(f"\n--- FAIL detail ---")
for sku,cp,iid,err in results["failed"]:
    print(f"  {sku} {cp} -> {err[:250]}")
