import os, requests, json
import meli_token
CPID="MLM52113823"; DOM="MLM-PERFUMES"; API="https://api.mercadolibre.com"
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
T=meli_token.refresh(RT).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
PICS=["897724-MLM112154514469_052026","840560-MLM112155272235_052026",
      "751916-MLM111152110628_052026","606658-MLM112155475559_052026"]
TITLE="Perfume The Alchemia Lab Flor de Nopal Mexico en la Piel Eau de Parfum 100 ml Unisex"

p=requests.get(f"{API}/products/{CPID}",headers=H,timeout=20).json()
base=[]
for a in (p.get("attributes") or []):
    aid=a.get("id")
    if aid in ("BRAND","MPN"): continue
    vals=a.get("values") or []
    if vals and all(v.get("id") for v in vals): base.append({"id":aid,"values":[{"id":v["id"]} for v in vals]})
    elif a.get("value_id"): base.append({"id":aid,"value_id":a["value_id"]})
attrs=base+[{"id":"BRAND","values":[{"name":"The Alchemia Lab"}]},
            {"id":"MPN","values":[{"name":"TAL-FDN-100ML"}]}]

# 1) listar mis sugerencias existentes para el producto
print("=== existing suggestions (search) ===")
for q in (f"/catalog_suggestions/search?status=UNDER_REVIEW", f"/products/{CPID}/suggestions"):
    r=requests.get(f"{API}{q}",headers=H,timeout=20)
    print(f"  GET {q} -> {r.status_code} {r.text[:200]}")

# 2) intentar EDIT scoped al producto
print("\n=== POST /products/{cpid}/suggestions ===")
for body in [
    {"type":"EDIT","attributes":attrs,"pictures":[{"id":x} for x in PICS],"title":TITLE},
    {"domain_id":DOM,"type":"EDIT","attributes":attrs,"pictures":[{"id":x} for x in PICS],"title":TITLE},
]:
    r=requests.post(f"{API}/products/{CPID}/suggestions",headers=HJ,json=body,timeout=40)
    print(f"  http={r.status_code} {r.text[:260]}")
    if r.status_code<300: break
print("DONE")
