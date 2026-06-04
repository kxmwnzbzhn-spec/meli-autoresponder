"""DRY: probar Gemini con un item real (Alma de Tenochtitlán) y la pregunta 'El perfume es fresco?'"""
import os, sys, json, requests, importlib.util

spec = importlib.util.spec_from_file_location("aap","scripts/answer_asva_pro.py")
aap  = importlib.util.module_from_spec(spec); spec.loader.exec_module(aap)

import meli_token
r = meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])
at = r["access_token"] if isinstance(r,dict) else r.json()["access_token"]
H  = {"Authorization": f"Bearer {at}"}

IID = "MLM3849137034"  # Alma de Tenochtitlan
item = aap.fetch_item(IID, H)
print("TITULO:", item["title"])
print("STATUS:", item["status"])
print("CONDITION:", item["condition"])
print("ATTRS keys:", list(item["attributes"].keys())[:15])
print("DESC (200 chars):", (item["description"] or "")[:200])
print()
print("--- Gemini test 1 ---")
print("Q: El perfume es fresco?")
print("A:", aap.gemini_answer("El perfume es fresco?", item))
print()
print("--- Gemini test 2 ---")
print("Q: Es para hombre o mujer?")
print("A:", aap.gemini_answer("Es para hombre o mujer?", item))
print()
print("--- Gemini test 3 ---")
print("Q: Cuanto dura el aroma?")
print("A:", aap.gemini_answer("Cuanto dura el aroma?", item))
