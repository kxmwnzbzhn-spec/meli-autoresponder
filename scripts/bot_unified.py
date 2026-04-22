import json
with open("stock_config.json") as f: sc=json.load(f)

ALLOWED={"MLM2883448187"}
OLD_5={"MLM5227773714","MLM5223214798","MLM2880763019","MLM2880762615","MLM5223451400"}

# Apagar las 5 viejas (por si acaso)
for iid in OLD_5:
    if iid in sc:
        sc[iid]["auto_replenish"]=False
        sc[iid]["deleted"]=True
        sc[iid]["real_stock"]=0
        print(f"  OFF {iid}")

# Activar SOLO la nueva unificada
if "MLM2883448187" in sc:
    sc["MLM2883448187"]["auto_replenish"]=True
    sc["MLM2883448187"]["deleted"]=False
    print(f"  ON MLM2883448187 stock={sc['MLM2883448187'].get('real_stock')}")

# Apagar todo lo demas por si queda algun otro prendido
for iid,cfg in sc.items():
    if not isinstance(cfg,dict): continue
    if iid in ALLOWED: continue
    if iid in OLD_5: continue
    if cfg.get("auto_replenish",False):
        cfg["auto_replenish"]=False
        print(f"  OFF extra {iid}")

with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print("\n=== Verificacion ===")
for iid,cfg in sc.items():
    if isinstance(cfg,dict) and cfg.get("auto_replenish",False):
        print(f"  ON {iid} stock={cfg.get('real_stock')} label={cfg.get('label','')[:40]}")
