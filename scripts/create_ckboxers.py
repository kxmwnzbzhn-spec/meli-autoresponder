import os, json, requests, meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
# 1) leer producto fuente
p=requests.get(f"{API}/products/MLM65349937",headers=H,timeout=20).json()
print("src name:",p.get("name"),"| domain:",p.get("domain_id"))
pics=[{"id":pp["id"]} for pp in (p.get("pictures") or []) if pp.get("id")][:10]
if not pics:
    pics=[{"url":pp.get("url")} for pp in (p.get("pictures") or []) if pp.get("url")][:10]
print("fotos:",len(pics))
src={a.get("id"):a.get("value_name") for a in p.get("attributes",[])}
print("src attrs:",src)

TITLE=("Paquete 3 Boxers Calvin Klein Microfibra Hombre Talla L | Calzoncillos Boxer Brief Cómodos Importados Comodidad Premium")
ATTRS=[
 {"id":"BRAND","values":[{"name":"Calvin Klein"}]},
 {"id":"MODEL","values":[{"name":"Brief"}]},
 {"id":"GENDER","values":[{"name":"Hombre"}]},
 {"id":"SIZE","values":[{"name":"L"}]},
 {"id":"ITEMS_PER_PACK","values":[{"name":"3"}]},
 {"id":"GTIN","values":[{"name": src.get("GTIN") or "028035188036"}]},
]
body={"site_id":"MLM","domain_id":"MLM-UNDERPANTS","type":"EDIT","title":TITLE,"attributes":ATTRS,"pictures":pics}
print("\nBODY:",json.dumps(body,ensure_ascii=False)[:900])
r=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
print("\nPOST http",r.status_code)
print(json.dumps(r.json(),ensure_ascii=False)[:1500])
