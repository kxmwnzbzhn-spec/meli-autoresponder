import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

with open("stock_config.json") as f: sc=json.load(f)

# SOLO catalog listings — stock de Bodega Electronica (NUEVOS)
# NO tocar reacondicionados que vienen de Devolución
CATALOG_NUEVO=[
    # (id, model, color, stock_nuevo_bodega)
    ("MLM2880865909","Charge 6","Azul",2),
    ("MLM2880865911","Charge 6","Rojo",2),
    ("MLM2880877603","Charge 6","Camuflaje",3),
    ("MLM2880877609","Charge 6","Negro",9),
    # Flip 7 — user clarifico: Morado 202, Azul 82, Negro 12 (Rojo sin stock nuevo)
    ("MLM2880754185","Flip 7","Negra",12),        # catalog pending_documentation
    ("MLM2880898001","Flip 7","Azul",82),          # catalog activa
    ("MLM2880758743","Flip 7","Morada",202),       # catalog pending_documentation
    ("MLM2880865907","Flip 7","Rojo",0),           # sin stock nuevo
    # Clip 5
    ("MLM2880766045","Clip 5","Negra",209),        # MLM2746814465
    ("MLM5223655448","Clip 5","Morado",240),       # 197254936427 user clarifico
    ("MLM2880754229","Clip 5","Rosa",3),           # MLM4827365256 Rosa Chicle
    # Grip
    ("MLM2880865935","Grip","Negro",243),
    # Go 4
    ("MLM2880766117","Go 4","Negra",25),           # MLM44710240Negro
    ("MLM2880877631","Go 4","Rosa",128),           # MLM2747154907
    ("MLM2880898041","Go 4","Azul",0),             # MLM2747206677 = 0
    ("MLM2880762615","Go 4","Camuflaje",12),
    ("MLM2880898033","Go 4","Rojo",0),             # no hay stock nuevo
    # Go 3
    ("MLM2880898049","Go 3","Negro",905),
]

print("=== CATALOG NUEVO (Bodega Electronica) ===")
for iid,m,c,stock in CATALOG_NUEVO:
    old=sc.get(iid,{}).get("real_stock","?")
    sc[iid]={
        "real_stock": stock,
        "sku": f"CAT-NEW-{m.replace(' ','')}-{c.upper()}",
        "label": f"Catalog NEW {m} {c}",
        "auto_replenish": stock>0,
        "replenish_quantity": 1,
        "min_visible_stock": 1,
        "deleted": False,
        "source":"bodega_electronica"
    }
    print(f"  {iid} [{m:<10} {c:<12}] {old} -> {stock}")

# Actualizar visible en MELI
print("\n=== MELI available_quantity ===")
for iid,m,c,stock in CATALOG_NUEVO:
    visible = 1 if stock>0 else 0
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    if it.get("status") in ("active","paused"):
        cur=it.get("available_quantity",0)
        if cur!=visible:
            r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"available_quantity":visible},timeout=20)
            print(f"  {iid}: {cur}->{visible} {r.status_code}")

# Verificar que reacondicionados NO tengan cambios de stock_config
REACOND_CHECK=[
    ("MLM5223653274","Flip 7 Negro reacond",179),
    ("MLM5223547784","Flip 7 Azul reacond",63),
    ("MLM2880875371","Flip 7 Morado reacond",59),
    ("MLM2880863639","Flip 7 Rojo reacond",35),
]
print("\n=== REACONDICIONADOS (Devolucion) - sin cambios ===")
for iid,lbl,exp in REACOND_CHECK:
    s=sc.get(iid,{}).get("real_stock","?")
    print(f"  {iid} [{lbl}] stock={s} (esperado {exp})")

with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print("\nstock_config.json actualizado")
