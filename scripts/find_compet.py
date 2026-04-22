import os,requests,time,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
SID=2681696373

# Por cada bocina, busco competidores en MELI search y sacamos el mejor precio
BOCINAS=[
    ("MLM2880763001","Charge 6","Azul",720),
    ("MLM2880774951","Charge 6","Roja",720),
    ("MLM2880762579","Charge 6","Camuflaje",720),
    ("MLM2880803051","Charge 6","Negra",720),
    ("MLM5223214318","Flip 7","Roja",640),
    ("MLM2880762535","Clip 5","Morada",690),
    ("MLM2880794089","Grip","Negra",565),
    ("MLM5223449418","Sony XB100","Negra",500),
    ("MLM2880762595","Go Essential 2","Azul",430),
    ("MLM2880775007","Go Essential 2","Roja",430),
    ("MLM2880763019","Go 4","Roja",430),
    ("MLM5223451400","Go 4","Rosa",430),
    ("MLM5223214798","Go 4","Azul Marino",430),
    ("MLM2880774949","Go 3","Negra",430),
]

STEP=10
changed=0; wins=0; floored=0

for iid,model,color,floor in BOCINAS:
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    if it.get("status")!="active":
        print(f"  SKIP {iid}: {it.get('status')}")
        continue
    cpid=it.get("catalog_product_id")
    our_price=int(it.get("price") or 0)
    
    # Buscar items similares via search
    if "Sony" in model:
        q="Sony SRS-XB100 "+color
    else:
        q=f"JBL {model} {color}"
    q=q.replace(" ","%20")
    search=requests.get(f"https://api.mercadolibre.com/sites/MLM/search?q={q}&condition=new&limit=50",headers=H,timeout=20).json()
    results=search.get("results",[])
    # Filtrar competidores: nuevos, condition=new, mismo modelo/color, no nuestros
    our_norm=f"{model} {color}".lower()
    model_key=model.lower()
    color_key=color.lower() if color.lower()!="azul marino" else "azul"
    competitors=[]
    for r_ in results:
        t=(r_.get("title") or "").lower()
        if r_.get("seller",{}).get("id")==SID: continue
        if r_.get("condition")!="new": continue
        if model_key not in t: continue
        if color_key not in t: continue
        # filtrar funda, case, cover, tester, repuesto
        if any(x in t for x in ["funda","case","cover","tester","bateria","cable","accesorio","repuesto"]): continue
        price=r_.get("price")
        if price and price<our_price*2:  # sanity check
            competitors.append({"id":r_.get("id"),"price":price,"title":r_.get("title")})
    
    # Ordenar por precio
    competitors.sort(key=lambda x:x["price"])
    cheapest = competitors[0] if competitors else None
    
    status="?"
    if not cheapest:
        status="sin competencia detectable"
        wins+=1
    elif cheapest["price"] > our_price:
        status=f"GANAMOS (mas barato: ${cheapest['price']} por {cheapest['id']})"
        wins+=1
    else:
        # perdemos
        candidate = our_price - STEP
        if candidate < floor:
            status=f"FLOOR ${floor} (competidor ${cheapest['price']})"
            floored+=1
        else:
            target = min(candidate, cheapest["price"]-1)
            if target < floor: target = floor
            new_price = target
            r2=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":new_price},timeout=20)
            if r2.status_code in (200,201):
                status=f"BAJAMOS ${our_price}→${new_price} (competidor ${cheapest['price']} por {cheapest['id']})"
                changed+=1
            else:
                status=f"ERR: {r2.status_code}"
    
    print(f"  {iid} [{model:<16} {color:<14}] floor=${floor:<4} $${our_price:<4} | {status}")
    time.sleep(0.3)

print(f"\n=== RESUMEN ===\nBajamos: {changed}\nGanamos: {wins}\nFloor: {floored}")
