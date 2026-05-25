import os, json, requests, meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}
r=requests.get(f"{API}/domains/MLM-SPORTSWEAR_SETS/technical_specs",headers=H,timeout=20)
print("status",r.status_code)
req=[]
def tags_of(n):
    t=n.get("tags")
    if isinstance(t,dict): return [k for k,v in t.items() if v]
    if isinstance(t,list): return t
    return []
def walk(n):
    if isinstance(n,dict):
        if n.get("id") and ("tags" in n or "values" in n or "value_type" in n):
            tg=tags_of(n)
            if any(x in tg for x in ("required","catalog_required","conditional_required")):
                vals=", ".join(x.get("name","?") for x in (n.get("values") or [])[:8])
                req.append(f"[{n.get('id')}] {n.get('name')} {tg} {('| '+vals) if vals else ''}")
        for v in n.values(): walk(v)
    elif isinstance(n,list):
        for v in n: walk(v)
walk(r.json())
print("OBLIGATORIOS:")
for x in req: print("  ",x)
