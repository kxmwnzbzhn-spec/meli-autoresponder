#!/usr/bin/env python3
"""Ajustar stock por variación.
Inputs por env:
  STOCK_TARGETS = JSON string
   [{"item_id":"MLM5244765752","mode":"all_colors","real":20,"visible":1},
    {"item_id":"1599970057545363","color":"negro","real":50,"visible":1}]
  Para cada item: probar refresh_tokens disponibles para encontrar dueño,
  listar variaciones, mostrar IDs, y actualizar:
    - en MELI: available_quantity = visible
    - en stock_config_<owner>.json: real_stock=real, min_visible=visible
"""
import os, json, requests, sys
API="https://api.mercadolibre.com"
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

ACCOUNTS = {
 "WILBERT":"MELI_REFRESH_TOKEN_WILBERT",
 "RAYMUNDO":"MELI_REFRESH_TOKEN_RAYMUNDO",
 "JUAN":"MELI_REFRESH_TOKEN",
 "CLARIBEL":"MELI_REFRESH_TOKEN_CLARIBEL",
 "ASVA":"MELI_REFRESH_TOKEN_ASVA",
 "DILCIE":"MELI_REFRESH_TOKEN_DILCIE",
 "MILDRED":"MELI_REFRESH_TOKEN_MILDRED",
 "BREN":"MELI_REFRESH_TOKEN_BREN",
 "YC_NEW":"MELI_REFRESH_TOKEN_YC_NEW",
}

def refresh(rt):
    r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
        "client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt},timeout=20)
    return r.json().get("access_token")

def fetch_item(token, iid):
    r=requests.get(f"{API}/items/{iid}",headers={"Authorization":f"Bearer {token}"},timeout=15)
    return r.status_code, r.json() if r.status_code==200 else r.text

# Cargar targets
TARGETS=json.loads(os.environ.get("STOCK_TARGETS","[]"))
if not TARGETS:
    print("Sin TARGETS"); sys.exit(0)

# Probar cada cuenta para cada item
for tgt in TARGETS:
    iid=tgt["item_id"]
    print(f"\n=== Buscando dueño de {iid} ===")
    found=None
    for acc,envk in ACCOUNTS.items():
        rt=os.environ.get(envk)
        if not rt: continue
        tok=refresh(rt)
        if not tok: continue
        sc, body = fetch_item(tok, iid)
        if sc==200:
            seller=body.get("seller_id") or (body.get("seller",{}) or {}).get("id")
            # filtrar: si el item es del seller de la cuenta, es nuestro
            me=requests.get(f"{API}/users/me",headers={"Authorization":f"Bearer {tok}"}).json()
            if me.get("id")==seller:
                found=(acc,tok,body); break
    if not found:
        print(f"  NO se encontró {iid} en ninguna cuenta o no es nuestro")
        continue
    acc,tok,body=found
    print(f"  Cuenta: {acc} (seller_id={body.get('seller_id')})")
    print(f"  Title: {body.get('title','')[:60]}")
    print(f"  Status: {body.get('status')}  catalog: {body.get('catalog_listing')} cpid={body.get('catalog_product_id')}")
    print(f"  Total stock actual: {body.get('available_quantity')}")
    vars_ = body.get("variations",[])
    print(f"  Variaciones: {len(vars_)}")
    for v in vars_:
        attrs=v.get("attribute_combinations",[])
        color = next((a.get("value_name") for a in attrs if a.get("name","").lower()=="color"), "?")
        print(f"    var_id={v.get('id')}  color={color}  qty={v.get('available_quantity')}  price={v.get('price')}")
    # Aplicar cambios
    mode=tgt.get("mode")
    color_target=tgt.get("color","").lower()
    real=tgt["real"]; visible=tgt["visible"]
    H={"Authorization":f"Bearer {tok}","Content-Type":"application/json"}
    if vars_:
        new_vars=[]
        for v in vars_:
            attrs=v.get("attribute_combinations",[])
            color = next((a.get("value_name","") for a in attrs if a.get("name","").lower()=="color"), "")
            apply = (mode=="all_colors") or (color_target and color.lower()==color_target)
            if apply:
                new_vars.append({"id":v["id"],"available_quantity":visible})
                print(f"    → {color} qty→{visible}")
        if new_vars:
            r=requests.put(f"{API}/items/{iid}",headers=H,json={"variations":new_vars},timeout=20)
            print(f"    PUT variations: {r.status_code} {r.text[:200]}")
    else:
        # sin variaciones — directo
        r=requests.put(f"{API}/items/{iid}",headers=H,json={"available_quantity":visible},timeout=15)
        print(f"  PUT qty={visible}: {r.status_code} {r.text[:200]}")
