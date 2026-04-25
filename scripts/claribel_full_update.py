import os, requests, json
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN_CLARIBEL","")

# 5 nuevos items
NEW_ITEMS = {
    "MLM2890840987": {"label":"Go 4 Azul Catálogo","price":499,"cpid":"MLM44710367"},
    "MLM5245310484": {"label":"Go 4 Roja Catálogo","price":499,"cpid":"MLM44710313"},
    "MLM5245310490": {"label":"Go 4 Camuflaje Catálogo","price":499,"cpid":"MLM37361021"},
    "MLM5245310494": {"label":"Go 4 Celeste/Aqua Catálogo","price":499,"cpid":"MLM61262890"},
    "MLM5245310498": {"label":"Sony SRS-XB100 Negro Catálogo","price":549,"cpid":"MLM25912333"},
}

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
at = r.json()["access_token"]
H = {"Authorization":f"Bearer {at}", "Content-Type":"application/json"}

# Update stock_config_claribel.json
try:
    with open("stock_config_claribel.json") as f:
        cfg = json.load(f)
except:
    cfg = {}

for iid, info in NEW_ITEMS.items():
    cfg[iid] = {
        "line": "Catalog-499",
        "label": info["label"],
        "price": info["price"],
        "catalog_product_id": info["cpid"],
        "auto_replenish": True,
        "min_visible": 1,
        "real_stock": 10,
        "daily_reset_to": 10,
        "active": True,
        "condition": "new",
        "type": "catalog_no_variations"
    }

with open("stock_config_claribel.json","w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
print(f"stock_config_claribel.json: {len(cfg)} items totales")
print(json.dumps({k:v for k,v in cfg.items() if k in NEW_ITEMS}, indent=2, ensure_ascii=False))
