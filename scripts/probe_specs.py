import os, requests, json
import meli_token

CPID = "MLM52113823"; DOM = "MLM-PERFUMES"
API = "https://api.mercadolibre.com"
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]
T = meli_token.refresh(RT).json()["access_token"]
H = {"Authorization": f"Bearer {T}"}

p = requests.get(f"{API}/products/{CPID}", headers=H, timeout=20).json()
cur = {a.get("id"): a.get("value_name") for a in (p.get("attributes") or [])}
print("=== CURRENT PRODUCT ATTRS ===")
for k, v in cur.items():
    print(f"  {k} = {v}")
print("short_description:", json.dumps((p.get('short_description') or '')[:200], ensure_ascii=False))

ts = requests.get(f"{API}/domains/{DOM}/technical_specs", headers=H, timeout=30).json()

def walk(node, out):
    if isinstance(node, dict):
        if node.get("id") and ("value_type" in node or "tags" in node or "values" in node):
            out.append(node)
        for v in node.values():
            walk(v, out)
    elif isinstance(node, list):
        for v in node:
            walk(v, out)

attrs = []
walk(ts, attrs)
seen = set()
print("\n=== DOMAIN ATTRS (id | name | tags | filled? | sample values) ===")
for a in attrs:
    aid = a.get("id")
    if not aid or aid in seen: continue
    seen.add(aid)
    tags = a.get("tags") or {}
    tagstr = ",".join(k for k, v in tags.items() if v) if isinstance(tags, dict) else str(tags)
    vals = a.get("values") or []
    sample = " | ".join((v.get("name") or "")[:18] for v in vals[:6])
    filled = "FILLED" if aid in cur else "----"
    print(f"  {aid:24} {(a.get('name') or '')[:26]:26} [{tagstr[:34]:34}] {filled:6} {('('+str(len(vals))+'v) ' if vals else '')}{sample}")
print("DONE")
