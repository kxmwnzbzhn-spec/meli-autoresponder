import json
with open("stock_config.json") as f: sc=json.load(f)
IID="MLM2883448187"
cfg=sc[IID]
old=cfg["variations"].get("Negro",{}).get("stock","-")
cfg["variations"]["Negro"]={"stock":20,"orig_id":cfg["variations"].get("Negro",{}).get("orig_id","")}
cfg["real_stock"]=sum(v.get("stock",0) for v in cfg["variations"].values())
with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print(f"Negro: {old} -> 20")
print(f"Total: {cfg['real_stock']}")
