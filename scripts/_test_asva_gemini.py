import os, importlib.util, requests
spec = importlib.util.spec_from_file_location("aap","scripts/answer_asva_pro.py")
aap  = importlib.util.module_from_spec(spec); spec.loader.exec_module(aap)
import meli_token
r = meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])
at = r["access_token"] if isinstance(r,dict) else r.json()["access_token"]
H = {"Authorization": f"Bearer {at}"}
item = aap.fetch_item("MLM3849137034", H)
print("TITULO:", item["title"][:80])
for q in [
    "El perfume es fresco?",
    "Es para hombre o mujer?",
    "Cuanto dura el aroma?",
    "Cuantos ml viene?",
    "Es original?",
    "Se puede usar en oficina?",
    "Cual es la nota principal?",
]:
    print(f"\nQ: {q}")
    a = aap.gemini_answer(q, item)
    print(f"A: {a}")
