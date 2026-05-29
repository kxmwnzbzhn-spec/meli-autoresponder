"""
Sonix Meli Listing Health Monitor â cloud-native uptime watcher.

Runs every 30 min via GitHub Actions.
Checks each MELI listing URL referenced by active landings:
- HTTP 200?
- Not paused / finalized?
- Price matches expected?

If anomaly: opens GitHub issue + (future) auto-pauses corresponding adset.
"""

import os, sys, json, re, requests
from datetime import datetime, timezone
from pathlib import Path

# Active product â (landing slug, expected MELI item URL, expected price MXN, Meta adset to pause if broken)
PRODUCTS = {
    "bocina_roja": {
        "name": "Bocina 35W Rojo $199 (REMATE)",
        "meli_url": "https://www.mercadolibre.com.mx/bocina-bluetooth-portatil-impermeable-ip67-bass-35w-rojo/up/MLMU3924350212",
        "expected_price": 199,  # Note: user must update Meli to $199 to match landing rematazo
        "expected_price_fallback": 298,  # legacy if not yet updated
        "adset_to_pause": "120245312737330238",
    },
    "dashcam": {
        "name": "Dashcam DVR-3",
        "meli_url": "https://www.mercadolibre.com.mx/dvr-3-camara-para-auto-hd-1080p-frente-y-cabina-gravacion-loop-doble-lente-vision-nocturna-pir-ssensor-q9-de-1080-p/p/MLM45458769?pdp_filters=item_id:MLM2943284461",
        "expected_price": 298,
        "adset_to_pause": "120245412226100238",
    },
}

# Cache for last known good state (committed to repo)
STATE_FILE = Path(".sonix-meli-state.json")
ALERT_THRESHOLD_CONSECUTIVE = 3  # only alert after N failed checks in a row


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def fetch_meli(url):
    """Meli serves JS-shell to bots; fetch best-effort and parse what we can."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "es-MX,es;q=0.9",
    }
    try:
        r = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        return r.status_code, r.text[:50000]  # first 50KB
    except Exception as e:
        return 0, str(e)


def parse_meli_health(html, expected_price=None):
    """Heuristic parsing: look for price, pause signals, item availability."""
    if not html:
        return {"ok": False, "issue": "empty response"}

    lower = html.lower()

    # Pause / availability signals
    if "publicaciÃ³n pausada" in lower or "publicacion pausada" in lower:
        return {"ok": False, "issue": "publicaciÃ³n pausada"}
    if "no estÃ¡ disponible" in lower or "publicaciÃ³n inactiva" in lower:
        return {"ok": False, "issue": "no disponible"}
    if "no se encontrÃ³ la publicaciÃ³n" in lower:
        return {"ok": False, "issue": "publicaciÃ³n no encontrada"}

    # Price extraction
    price_match = re.search(r'meta\s+itemprop="price"\s+content="(\d+(?:\.\d+)?)"', html)
    found_price = None
    if price_match:
        found_price = int(float(price_match.group(1)))

    if expected_price and found_price and found_price != expected_price:
        # Also accept fallback price as warning
        return {
            "ok": True,
            "issue": f"price mismatch: expected ${expected_price}, found ${found_price}",
            "found_price": found_price,
            "warning": True,
        }

    return {"ok": True, "found_price": found_price}


def create_github_issue(title, body):
    """Open a GitHub issue via the API. Uses GITHUB_TOKEN auto-injected in Actions."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print(f"  [no GITHUB_TOKEN â skipping issue creation]")
        return False
    r = requests.post(
        "https://api.github.com/repos/kxmwnzbzhn-spec/meli-autoresponder/issues",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        },
        json={"title": title, "body": body, "labels": ["sonix-monitor", "automated"]},
        timeout=15,
    )
    return r.status_code == 201


def pause_adset(adset_id):
    token = os.environ.get("META_ADS_TOKEN") or os.environ.get("META_CAPI_ACCESS_TOKEN", "")
    if not token:
        return False
    r = requests.post(
        f"https://graph.facebook.com/v21.0/{adset_id}",
        data={"status": "PAUSED", "access_token": token},
        timeout=15,
    )
    return r.status_code == 200


def main():
    print(f"=== Sonix Meli Health Â· {datetime.now(timezone.utc).isoformat()} ===")
    state = load_state()
    any_critical = False

    for slug, prod in PRODUCTS.items():
        url = prod["meli_url"]
        print(f"\n[{slug}] {prod['name']}")
        print(f"  URL: {url[:80]}...")

        status_code, html = fetch_meli(url)
        print(f"  HTTP: {status_code}")

        if status_code != 200:
            state.setdefault(slug, {"failures": 0})
            state[slug]["failures"] += 1
            print(f"  CONSECUTIVE FAILURES: {state[slug]['failures']}")

            if state[slug]["failures"] >= ALERT_THRESHOLD_CONSECUTIVE:
                any_critical = True
                title = f"ð´ Meli listing down: {prod['name']}"
                body = (f"Listing {url} ha respondido con HTTP {status_code} "
                        f"en {state[slug]['failures']} checks consecutivos.\n\n"
                        f"Auto-pausando adset `{prod['adset_to_pause']}`.\n\n"
                        f"Revisa Meli seller account o el item_id correspondiente.")
                if create_github_issue(title, body):
                    print(f"  Issue opened")
                if pause_adset(prod["adset_to_pause"]):
                    print(f"  Adset {prod['adset_to_pause']} PAUSED")
            continue

        health = parse_meli_health(html, prod.get("expected_price"))
        print(f"  Health: {health}")

        if not health["ok"]:
            state.setdefault(slug, {"failures": 0})
            state[slug]["failures"] += 1

            if state[slug]["failures"] >= ALERT_THRESHOLD_CONSECUTIVE:
                any_critical = True
                title = f"ð´ Meli listing problem: {prod['name']}"
                body = (f"Listing {url}\n\n"
                        f"Issue: **{health.get('issue')}**\n\n"
                        f"Detectado {state[slug]['failures']} veces consecutivas.\n"
                        f"Auto-pausando adset `{prod['adset_to_pause']}`.")
                if create_github_issue(title, body):
                    print(f"  Issue opened")
                if pause_adset(prod["adset_to_pause"]):
                    print(f"  Adset {prod['adset_to_pause']} PAUSED")
        else:
            # Healthy â reset counter
            state[slug] = {"failures": 0, "last_good": datetime.now(timezone.utc).isoformat()}
            if health.get("warning"):
                print(f"  â ï¸ Warning (non-critical): {health.get('issue')}")

    save_state(state)
    sys.exit(2 if any_critical else 0)


if __name__ == "__main__":
    main()
