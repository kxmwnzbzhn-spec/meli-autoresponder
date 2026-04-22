import os,json
with open("stock_config.json") as f: sc=json.load(f)

ALLOWED={"MLM5227773714","MLM5223214798","MLM2880763019","MLM2880762615","MLM5223451400"}

# Por cada entrada del stock_config de Juan, si no esta en ALLOWED, auto_replenish=false
changed=0; kept=0
for iid, cfg in sc.items():
    if not isinstance(cfg,dict): continue
    # Saltar si es cuenta oficial (Claribel) - el stock config de Juan es stock_config.json, oficial es stock_config_oficial.json
    if iid in ALLOWED:
        cfg["auto_replenish"]=True
        cfg["deleted"]=False
        if cfg.get("real_stock",0)<10:
            cfg["real_stock"]=10  # al menos 10 stock default
        kept+=1
    else:
        if cfg.get("auto_replenish",False):
            cfg["auto_replenish"]=False
            changed+=1

# Asegurar que los 5 ALLOWED existan en el config
for iid in ALLOWED:
    if iid not in sc:
        sc[iid]={
            "real_stock":10,
            "sku":f"GO4-{iid}",
            "label":f"Go 4 {iid}",
            "auto_replenish":True,
            "replenish_quantity":1,
            "min_visible_stock":1,
            "deleted":False,
        }
        kept+=1

with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print(f"Bot restringido: {kept} con auto_replenish=ON (Go 4 permitidas), {changed} apagados (resto)")
print(f"\nPermitidas:")
for iid in ALLOWED:
    c=sc.get(iid,{})
    print(f"  {iid} | stock_real={c.get('real_stock')} | auto_replenish={c.get('auto_replenish')}")
