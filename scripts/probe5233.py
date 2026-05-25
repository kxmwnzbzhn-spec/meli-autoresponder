import os, json, requests, meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}
ID="5233454100"
def sec(t): print(f"\n=== {t} ===")
# probar como catalog_suggestion
sec(f"GET /catalog_suggestions/{ID}")
r=requests.get(f"{API}/catalog_suggestions/{ID}",headers=H,timeout=20)
print("status",r.status_code)
if r.status_code==200:
    d=r.json()
    print("title:",d.get("title"))
    print("type:",d.get("type"),"| status:",d.get("status"),"| domain:",d.get("domain_id"))
    print("catalog_product_id:",d.get("catalog_product_id"))
    print("seller_id:",d.get("seller_id"))
    print("pictures:",len(d.get("pictures") or []))
    if d.get("reasons") or d.get("errors"):
        print("reasons/errors:",json.dumps(d.get("reasons") or d.get("errors"),ensure_ascii=False)[:600])
    print("attributes:")
    for a in d.get("attributes",[]):
        vs=", ".join(v.get("name","?") for v in (a.get("values") or []))
        print(f"  [{a.get('id')}] {a.get('name')} = {vs}")
else:
    print("body:",r.text[:300])
    # probar como item
    sec(f"GET /items/MLM{ID}")
    r2=requests.get(f"{API}/items/MLM{ID}",headers=H,timeout=15)
    print("status",r2.status_code, r2.text[:200])
