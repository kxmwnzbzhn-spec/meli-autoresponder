import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}"}

CPID = "MLM44710313"
print(f"=== Catálogo {CPID} ===")
prod = requests.get(f"https://api.mercadolibre.com/products/{CPID}", headers=H).json()
print(f"  name: {prod.get('name')}")
print(f"  status: {prod.get('status')}")
print(f"  attributes:")
for a in prod.get("attributes", []):
    if a.get("id") in ("BRAND","MODEL","DETAILED_MODEL","MANUFACTURER","COLOR","LINE","MODEL_NAME"):
        print(f"    {a.get('id'):20} = {a.get('value_name')} (id={a.get('value_id')})")

# Buscar otros catalog products para JBL Go 4 Rojo
print(f"\n=== Buscar catálogos JBL Go 4 Rojo ===")
search = requests.get("https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q=jbl+go+4+rojo&limit=15", headers=H).json()
for p in search.get("results", [])[:10]:
    pid = p.get("id")
    name = p.get("name","")[:60]
    # Get details
    pp = requests.get(f"https://api.mercadolibre.com/products/{pid}", headers=H).json()
    dm = ""
    for a in pp.get("attributes", []):
        if a.get("id") == "DETAILED_MODEL":
            dm = a.get("value_name","")
            break
    print(f"  {pid:>20} DM='{dm}' | {name}")
