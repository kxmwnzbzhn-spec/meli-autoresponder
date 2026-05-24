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
    if vals and all(v.get("id") for v in vals):
        base.append({"id":aid,"values":[{"id":v["id"]} for v in vals]})
    elif a.get("value_id"):
        base.append({"id":aid,"value_id":a["value_id"]})
newvals=[{"id":"BRAND","values":[{"name":"The Alchemia Lab"}]},
         {"id":"MPN","values":[{"name":"TAL-FDN-100ML"}]}]

for ttype in ("EDIT",):
    body={"domain_id":DOM,"catalog_product_id":CPID,"type":ttype,
          "attributes":base+newvals,"pictures":[{"id":x} for x in PICS],"title":TITLE}
    r=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
    print(f"=== type={ttype} -> http={r.status_code} ===")
    try:
        j=r.json()
        if r.status_code<300:
            print("  id:",j.get("id"),"| type:",j.get("type"),"| status:",j.get("status"),
                  "| catalog_product_id:",j.get("catalog_product_id"))
        else:
            for c in (j.get("cause") or [{}]): print("  cause:",c.get("code"),c.get("message","")[:80])
    except Exception:
        print("  ",r.text[:300])
print("DONE")
