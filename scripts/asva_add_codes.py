import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Codigos de barras reales de cada caja (SKU fabricante + EAN/UPC)
CODES={
    "Negro":  {"id":"MLM5233480022","sku":"JBLFLIP7BLK","ean":"1200130019272","upc":"050036407250","jan":"4968929223527"},
    "Azul":   {"id":"MLM5233454100","sku":"JBLFLIP7BLU","ean":"1200130019289","upc":"050036407267","jan":"4968929223534"},
    "Rojo":   {"id":"MLM2886030837","sku":"JBLFLIP7RED","ean":"1200130019296","upc":"050036407274","jan":"4968929223541"},
    "Morado": {"id":"MLM2886136351","sku":"JBLFLIP7PUR","ean":"1200130019319","upc":"050036407298","jan":"4968929223565"},
}

for color,info in CODES.items():
    iid=info["id"]
    # obtener atributos actuales
    cur=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=attributes",headers=H).json()
    attrs=cur.get("attributes") or []
    keep=[a for a in attrs if a.get("id") not in ("SELLER_SKU","GTIN","EAN","UPC","ALPHANUMERIC_MODEL")]
    # añadir codigos
    keep.append({"id":"SELLER_SKU","value_name":info["sku"]})
    keep.append({"id":"GTIN","value_name":info["ean"]})
    keep.append({"id":"ALPHANUMERIC_MODEL","value_name":info["sku"]})
    body={"attributes":keep}
    rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body,timeout=30)
    print(f"{color} {iid}: {rp.status_code}")
    if rp.status_code not in (200,201):
        print(f"  err: {rp.text[:500]}")
        # fallback: solo SELLER_SKU
        body2={"attributes":[a for a in keep if a.get("id") not in ("GTIN","ALPHANUMERIC_MODEL")]}
        rp2=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body2,timeout=30)
        print(f"  retry solo SELLER_SKU: {rp2.status_code}")
        if rp2.status_code not in (200,201):
            print(f"    err2: {rp2.text[:400]}")
    time.sleep(1)
