import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Cargar stock_config
with open("stock_config.json") as f: sc=json.load(f)

# Catalog listings (NUEVA) -> stock NUEVO desde Bodega Electronica
# Disponible real (columna Disponible)
STOCK_UPDATES=[
    # id_meli, model, color, new_stock
    ("MLM2880865909","Charge 6","Azul",2),        # charge6 Azul JBL
    ("MLM2880865911","Charge 6","Rojo",2),        # CHARGE6 ROJO JBL
    ("MLM2880877603","Charge 6","Camuflaje",3),   # JBLCHARGE6CAMUFLAJE
    ("MLM2880877609","Charge 6","Negro",9),       # JBLCHARGE6NEGRO
    ("MLM2880865935","Grip","Negro",243),         # BOCINA GRIP NEGRO JBL
    ("MLM2880898049","Go 3","Negro",905),         # MLM2732813905
    ("MLM2880877631","Go 4","Rosa",128),          # MLM2747154907 Rosa Chicle
    ("MLM2880898041","Go 4","Azul",0),            # MLM2747206677 Azul - sin stock
    ("MLM5223655448","Clip 5","Morado",11),       # sin cambio (no hay nuevo Morado en Bodega)
    ("MLM2880766117","Go 4","Negra",25),          # MLM44710240Negro
]
# Para los catalog pending_documentation
PENDING=[
    ("MLM2880754185","Flip 7","Negra",179),    # desde devolucion (no hay new en Bodega)
    ("MLM2880758743","Flip 7","Morada",59),
    ("MLM2880766045","Clip 5","Negra",209),    # MLM2746814465 = 209 new
    ("MLM2880754229","Clip 5","Rosa",3),       # MLM4827365256 Rosa Chicle = 3
    ("MLM2880762615","Go 4","Camuflaje",12),
]

print("=== ACTUALIZACION CATALOG STOCK ===")
for iid,m,c,newstock in STOCK_UPDATES:
    old=sc.get(iid,{}).get("real_stock","?")
    sc[iid]={
        "real_stock": newstock,
        "sku": sc.get(iid,{}).get("sku",f"CAT-{m.replace(' ','')}-{c.upper()}"),
        "label": f"Catalog {m} {c}",
        "auto_replenish": True if newstock>0 else False,
        "replenish_quantity": 1,
        "min_visible_stock": 1,
    }
    print(f"  {iid} [{m:<10} {c:<12}] {old} -> {newstock}")

print("\n=== PENDING DOCUMENTATION ===")
for iid,m,c,newstock in PENDING:
    old=sc.get(iid,{}).get("real_stock","?")
    sc[iid]={
        "real_stock": newstock,
        "sku": f"CAT-{m.replace(' ','')}-{c.upper()}",
        "label": f"Pending {m} {c}",
        "auto_replenish": True,
        "replenish_quantity": 1,
        "min_visible_stock": 1,
        "deleted": False,
    }
    print(f"  {iid} [{m:<10} {c:<12}] {old} -> {newstock}")

# Actualizar available_quantity en MELI (solo para items active, min(1, new))
# Visible = 1 siempre (o 0 si stock 0)
print("\n=== MELI available_quantity ===")
for iid,m,c,newstock in STOCK_UPDATES:
    visible = 1 if newstock>0 else 0
    item=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    current_status=item.get("status")
    current_qty=item.get("available_quantity",0)
    if current_status=="active" and current_qty!=visible:
        r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"available_quantity":visible},timeout=20)
        print(f"  {iid}: qty {current_qty}->{visible} {r.status_code}")

with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print("\nstock_config.json guardado")
