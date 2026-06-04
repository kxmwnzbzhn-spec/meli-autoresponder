import os, json, importlib.util, requests, sys
spec = importlib.util.spec_from_file_location("aap","scripts/answer_asva_pro.py")
aap  = importlib.util.module_from_spec(spec); spec.loader.exec_module(aap)
import meli_token
r = meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])
at = r["access_token"] if isinstance(r,dict) else r.json()["access_token"]
H = {"Authorization": f"Bearer {at}"}
item = aap.fetch_item("MLM3849137034", H)

# Replicar exact lo que envia el script
attrs_keep = {}
KEYS = ["BRAND","MODEL","GENDER","FRAGRANCE_TYPE","OLFACTORY_FAMILY","ITEM_VOLUME","ITEM_VOLUME_UNIT","SIZE","COLOR","MATERIAL"]
for k in KEYS:
    v = item["attributes"].get(k)
    if v: attrs_keep[k] = v

ctx = f"TITULO: {item['title']}\nATRIBUTOS: {json.dumps(attrs_keep, ensure_ascii=False)}\nDESCRIPCION:\n{item['description']}"
q = "El perfume es fresco?"
user_prompt = f"{ctx}\n\nPREGUNTA DEL COMPRADOR:\n{q}\n\nResponde."

body = {
    "system_instruction": {"parts":[{"text": aap.SYSTEM_PROMPT}]},
    "contents":[{"role":"user","parts":[{"text": user_prompt}]}],
    "generationConfig":{"temperature":0.3,"maxOutputTokens":600,"candidateCount":1,"thinkingConfig":{"thinkingBudget":0}}
}
GK = os.environ["GEMINI_API_KEY"]
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
print("--- BODY enviado (truncado a 1000) ---")
print(json.dumps(body, ensure_ascii=False)[:1000])
print()
r = requests.post(f"{url}?key={GK}", json=body, timeout=40)
print("HTTP", r.status_code)
print("RAW RESPONSE:")
print(r.text[:3000])
sys.stdout.flush()
