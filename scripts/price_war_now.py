import os,requests,time,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Bocinas activas + floor por modelo
BOCINAS=[
    # (id, model, color, cpid, floor)
    ("MLM2880763001","Charge 6","Azul",None,720),
    ("MLM2880774951","Charge 6","Roja","MLM46455780",720),
    ("MLM2880762579","Charge 6","Camuflaje",None,720),
    ("MLM2880803051","Charge 6","Negra",None,720),
    ("MLM5223214318","Flip 7","Roja",None,640),
    ("MLM2880762535","Clip 5","Morada",None,690),
    ("MLM2880794089","Grip","Negra",None,565),
    ("MLM5223449418","Sony XB100","Negra","MLM25912333",500),
    ("MLM2880762595","Go Essential 2","Azul",None,430),
    ("MLM2880775007","Go Essential 2","Roja",None,430),
    ("MLM2880763019","Go 4","Roja",None,430),
    ("MLM5223451400","Go 4","Rosa",None,430),
    ("MLM5223214798","Go 4","Azul Marino",None,430),
    ("MLM2880774949","Go 3","Negra",None,430),
]

STEP=10
changed=0; same=0; floored=0; errs=0

for iid,model,color,cpid_hint,floor in BOCINAS:
    # 1) Traer item
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    if it.get("status")!="active":
        print(f"  SKIP {iid} [{model} {color}] status={it.get('status')}")
        continue
    cpid = it.get("catalog_product_id") or cpid_hint
    our_price = int(it.get("price") or 0)
    if not cpid:
        print(f"  NOCPID {iid} [{model} {color}] price=${our_price}")
        continue
    # 2) Traer buy_box_winner del catalog product
    pr=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
    bbw=pr.get("buy_box_winner") or {}
    bbw_price=bbw.get("price")
    bbw_item=bbw.get("item_id")
    bbw_seller=bbw.get("seller_id")
    # 3) Analizar
    status="?"
    new_price=our_price
    if bbw_item==iid:
        status="GANAMOS ✓"
        same+=1
    elif bbw_price is None:
        status="sin BBW"
        same+=1
    elif bbw_price > our_price:
        status=f"GANAMOS (BBW ${bbw_price}, nosotros ${our_price})"
        same+=1
    else:
        # perdemos - bajar
        candidate = our_price - STEP
        if candidate < floor:
            status=f"FLOOR alcanzado ${floor} (BBW ${bbw_price})"
            floored+=1
        else:
            # bajar a bbw_price - 1 si está arriba del floor, si no step
            target = min(candidate, bbw_price - 1) if bbw_price - 1 >= floor else candidate
            if target < floor: target=floor
            new_price=target
            r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":new_price},timeout=20)
            if r.status_code in (200,201):
                status=f"BAJAMOS ${our_price} → ${new_price} (BBW ${bbw_price})"
                changed+=1
            else:
                status=f"ERR updating: {r.status_code} {r.text[:100]}"
                errs+=1
    print(f"  {iid} [{model:<16} {color:<14}] floor=${floor:<4} ${our_price:<4} {status}")
    time.sleep(0.5)

print(f"\n=== RESUMEN ===")
print(f"Bajamos precio: {changed}")
print(f"Ya ganamos o sin info: {same}")
print(f"En floor: {floored}")
print(f"Errores: {errs}")
