import os, requests, json, time

# Lista de reclamos a procesar - {account, claim_id}
CLAIMS = [
    {"account":"JUAN","claim_id":"5504040334"},
    {"account":"JUAN","claim_id":"5503148321"},
    {"account":"JUAN","claim_id":"5504305919"},
    {"account":"JUAN","claim_id":"5505763196"},
    {"account":"JUAN","claim_id":"5503293842"},
    {"account":"JUAN","claim_id":"5505836752"},
    {"account":"JUAN","claim_id":"5504093465"},
    {"account":"JUAN","claim_id":"5504849644"},
    {"account":"JUAN","claim_id":"5505490427"},
    {"account":"JUAN","claim_id":"5504303598"},
    {"account":"JUAN","claim_id":"5505745784"},
    {"account":"CLARIBEL","claim_id":"5504969300"},
    {"account":"CLARIBEL","claim_id":"5505476644"},
    {"account":"CLARIBEL","claim_id":"5505521577"},
    {"account":"CLARIBEL","claim_id":"5505510642"},
    {"account":"CLARIBEL","claim_id":"5505490761"},
    {"account":"CLARIBEL","claim_id":"5505555039"},
    {"account":"CLARIBEL","claim_id":"5505864377"},
    {"account":"CLARIBEL","claim_id":"5505372979"},
    {"account":"CLARIBEL","claim_id":"5505036637"},
    {"account":"CLARIBEL","claim_id":"5505050262"},
    {"account":"CLARIBEL","claim_id":"5505525280"},
    {"account":"CLARIBEL","claim_id":"5505527052"},
    {"account":"CLARIBEL","claim_id":"5505319701"},
    {"account":"CLARIBEL","claim_id":"5505453779"},
    {"account":"CLARIBEL","claim_id":"5505110602"},
    {"account":"CLARIBEL","claim_id":"5505495015"},
    {"account":"CLARIBEL","claim_id":"5505526338"},
    {"account":"CLARIBEL","claim_id":"5505786058"},
    {"account":"CLARIBEL","claim_id":"5505841015"},
    {"account":"RAYMUNDO","claim_id":"5504588559"},
    {"account":"RAYMUNDO","claim_id":"5505737022"},
    {"account":"RAYMUNDO","claim_id":"5505540653"},
    {"account":"RAYMUNDO","claim_id":"5505781510"},
    {"account":"RAYMUNDO","claim_id":"5505871506"},
    {"account":"RAYMUNDO","claim_id":"5505764139"},
    {"account":"RAYMUNDO","claim_id":"5505764359"},
    {"account":"RAYMUNDO","claim_id":"5505724192"},
    {"account":"RAYMUNDO","claim_id":"5505444213"},
]

TOKEN_ENVS = {
    "JUAN": "MELI_REFRESH_TOKEN",
    "CLARIBEL": "MELI_REFRESH_TOKEN_CLARIBEL",
    "RAYMUNDO": "MELI_REFRESH_TOKEN_RAYMUNDO",
}

# Playbook 5 puntos validado contra 5502336104
PLAYBOOK_MSG = """Hola, lamento mucho el inconveniente con tu compra. Quiero resolver esto de la mejor manera posible y necesito tu colaboración para entender exactamente qué pasó:

1) ¿El producto llegó físicamente a tus manos? Si no llegó, por favor verifica el comprobante de Mercado Envíos en tu cuenta — si Mercado Libre confirma entrega, la responsabilidad es de Mercado Envíos y debes abrir reclamo de transporte, no contra el vendedor.

2) Si SÍ llegó: por favor mándame fotos/video del producto recibido — específicamente del empaque, accesorios y la parte trasera donde aparece el modelo y serial. Esto nos sirve para validar que el producto que recibiste es el mismo que enviamos.

3) Confirma que el producto fue probado correctamente: ¿lo cargaste al menos 30 minutos antes de usarlo? ¿lo pareaste con bluetooth siguiendo las instrucciones? Muchos casos se resuelven simplemente con la primera carga completa.

4) Si confirmas defecto real de fábrica, procederemos a reemplazo o devolución sin problema, según tu preferencia, pero necesitamos las evidencias del punto 2 para activar la garantía con el proveedor.

5) Si tu motivo es "no es original" o "imitación": por favor revisa que la publicación que compraste indica claramente las condiciones del producto (nuevo / reacondicionado / sin caja, etc). Vendemos productos originales con garantía. Si tienes dudas sobre autenticidad puedo enviarte fotos de validación.

Esperamos tu respuesta para continuar. Saludos cordiales,
Equipo de Soporte"""

def get_token(env_key):
    rt = os.environ.get(env_key)
    if not rt:
        return None, "No env var"
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token",
        "client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],
        "refresh_token":rt
    }, timeout=15).json()
    return r.get("access_token"), r

# Cache tokens por cuenta
token_cache = {}
results = []
for c in CLAIMS:
    acc = c["account"]
    cid = c["claim_id"]
    if acc not in token_cache:
        env_key = TOKEN_ENVS.get(acc)
        if not env_key:
            results.append({"claim":cid, "account":acc, "ok":False, "err":"no env mapping"})
            print(f"  ✗ [{acc}] {cid}: sin token mapping")
            continue
        tok, raw = get_token(env_key)
        if not tok:
            results.append({"claim":cid, "account":acc, "ok":False, "err":f"oauth fail: {raw}"})
            print(f"  ✗ [{acc}] {cid}: oauth fail {raw}")
            token_cache[acc] = None
            continue
        token_cache[acc] = tok

    tok = token_cache[acc]
    if not tok:
        continue
    H = {"Authorization": f"Bearer {tok}", "Content-Type":"application/json"}

    try:
        r = requests.post(
            f"https://api.mercadolibre.com/post-purchase/v1/claims/{cid}/messages",
            headers=H,
            json={"message": PLAYBOOK_MSG},
            timeout=20
        )
        ok = r.status_code in (200, 201)
        results.append({"claim":cid, "account":acc, "ok":ok, "status":r.status_code, "resp":r.text[:200]})
        symbol = "✓" if ok else "✗"
        print(f"  {symbol} [{acc}] {cid}: {r.status_code}")
        time.sleep(0.4)
    except Exception as e:
        results.append({"claim":cid, "account":acc, "ok":False, "err":str(e)})
        print(f"  ✗ [{acc}] {cid}: ERR {e}")

# Summary
ok = sum(1 for r in results if r.get("ok"))
err = len(results) - ok
print(f"\n=== TOTAL: {ok}/{len(results)} enviados, {err} errores ===")

# Telegram
tg_t = os.environ.get("TELEGRAM_BOT_TOKEN"); tg_c = os.environ.get("TELEGRAM_CHAT_ID")
if tg_t and tg_c:
    msg = f"📋 Playbook batch enviado: {ok}/{len(results)} reclamos.\n"
    if err > 0:
        msg += f"\n❌ {err} errores:"
        for r in results:
            if not r.get("ok"):
                msg += f"\n  • [{r['account']}] {r['claim']}: {r.get('err') or r.get('status')}"
    requests.post(f"https://api.telegram.org/bot{tg_t}/sendMessage", data={"chat_id":tg_c, "text":msg}, timeout=10)
    print("TG sent")
