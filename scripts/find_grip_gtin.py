import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}

# Catalog Grip MLM61785271 - ver atributos y children
for cpid in ["MLM61785271"]:
    print(f"=== {cpid} ===")
    p=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H).json()
    print(f"  name: {p.get('name','')[:80]}")
    for a in (p.get("attributes") or []):
        if "GTIN" in (a.get("id") or "") or a.get("id") in ("GTIN","EAN","UPC","SELLER_SKU"):
            print(f"    {a.get('id')}: {a.get('value_name')}")
    for kid in (p.get("children_ids") or [])[:5]:
        pk=requests.get(f"https://api.mercadolibre.com/products/{kid}",headers=H).json()
        print(f"\n  CHILD {kid}: {pk.get('name','')[:60]}")
        for a in (pk.get("attributes") or []):
            if a.get("id") in ("GTIN","EAN","UPC","COLOR","SELLER_SKU"):
                print(f"    {a.get('id')}: {a.get('value_name')}")

# Tambien ver items activos con Grip y sus GTINs
print("\n=== ITEMS activos JBL Grip con GTIN ===")
s=requests.get("https://api.mercadolibre.com/sites/MLM/search?q=JBL+Grip&category=MLM59800&limit=10",headers=H).json()
for r_ in (s.get("results") or [])[:10]:
    if "Grip" in r_.get("title","") and "JBL" in r_.get("title",""):
        iid=r_.get("id")
        d=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=attributes,title",headers=H).json()
        for a in (d.get("attributes") or []):
            if a.get("id")=="GTIN":
                print(f"  {iid} [{d.get('title','')[:45]}]: GTIN={a.get('value_name')}")
                break
