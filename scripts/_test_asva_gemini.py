"""DRY: curl directo Gemini + comparar."""
import os, json, requests
GK = os.environ["GEMINI_API_KEY"]
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
body = {
    "contents": [{"role":"user","parts":[{"text":"Responde una frase: el cielo es azul?"}]}],
    "generationConfig": {"temperature":0.3,"maxOutputTokens":200,"thinkingConfig":{"thinkingBudget":0}}
}
r = requests.post(f"{url}?key={GK}", json=body, timeout=30)
print("HTTP", r.status_code)
print("BODY:", r.text[:2000])
