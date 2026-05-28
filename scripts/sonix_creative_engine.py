"""
Sonix Creative Engine — autonomous ad creative generation + rotation + fatigue detection.

Pipeline:
1. DETECT FATIGUE: scan active ads, flag those with frequency > 4 OR CTR -30% vs 7d baseline
2. CHECK BENCH: count un-deployed creatives in /assets/creative-bench/{product}/
3. GENERATE: if bench < 5, call PIL templater + (optional) Nano Banana Imagen API
4. ROTATE: pause fatigued ad → upload fresh creative → create new ad ACTIVE
5. LOG: write decisions to /reports/creative-engine-YYYY-MM-DD.md

Env vars:
- META_CAPI_ACCESS_TOKEN (Meta Ads API)
- GEMINI_API_KEY (Nano Banana / Imagen via Google AI Studio)
- GITHUB_TOKEN (for committing bench updates)

Runs daily via GitHub Actions at 08:00 CDMX (14:00 UTC), after the budget audit.
"""

import os, sys, json, requests, hashlib, random, time
from datetime import datetime, timezone
from pathlib import Path
from io import BytesIO

# ============================ CONFIG ============================
ACCOUNT_ID = "act_1689903372006934"
META_GRAPH = "https://graph.facebook.com/v21.0"
META_TOKEN = os.environ.get("META_CAPI_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_IMAGE_MODEL = "imagen-4.0-generate-001"  # Nano Banana = Imagen via Gemini
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_IMAGE_MODEL}:predict"

# Per-product creative config
PRODUCTS = {
    "bocina_roja": {
        "name": "Bocina Bluetooth 35W IP67 Rojo $199",
        "adset_id": "120245312737330238",
        "campaign_id": "120245220932750238",
        "page_id": "477739852100670",
        "link_url": "https://sonixmx.com.mx/bocina-30w-espejo/",
        "price_now": 199,
        "price_was": 599,
        "source_photos": ["assets/source/rojo_life1.jpg", "assets/source/rojo_life2.jpg", "assets/source/rojo_life3.jpg"],
        "imagen_prompts": [
            "Red portable Bluetooth speaker on beach sand at sunset, cinematic lighting, IP67 waterproof outdoor lifestyle",
            "Red Bluetooth speaker on a pool edge with water droplets, summer party vibe, vibrant",
            "Red Bluetooth speaker on a wooden table at sunset with friends in background blurred, social lifestyle",
            "Red waterproof speaker on rocks by the ocean, dramatic light, adventure aesthetic",
            "Red Bluetooth speaker on a colorful Mexican market table, vibrant culture",
        ],
        "headlines_pool": [
            "REMATE FINAL · $199",
            "BOCINA ROJA $199",
            "67% OFF · ÚLTIMAS",
            "$199 · ANTES $599",
            "REMATAZO ROJO",
            "BLUETOOTH 35W $199",
            "IP67 · BLUETOOTH 5.3",
            "LIQUIDACIÓN $199",
            "STOCK FINAL ROJO",
            "AHORRAS $400",
        ],
    },
    "dashcam": {
        "name": "Dashcam DVR-3 3 Cámaras Full HD",
        "adset_id": "120245412226100238",
        "campaign_id": "120245364929030238",
        "page_id": "477739852100670",
        "link_url": "https://sonixmx.com.mx/dashcam-dvr3/",
        "price_now": 298,
        "price_was": 899,
        "source_photos": ["assets/source/dvr3_life1.jpg", "assets/source/dvr3_life2.jpg", "assets/source/dvr3_life3.jpg"],
        "imagen_prompts": [
            "Dashcam mounted on car windshield during sunset drive on highway, three lens camera, cinematic",
            "Dashcam interior of luxury car cockpit at night with city lights, futuristic tech aesthetic",
            "Dashcam recording road accident scene with clear evidence overlay, safety theme",
            "Dashcam closeup mounted on rearview mirror, modern car interior",
            "Dashcam in pickup truck during rainstorm, dramatic weather, durability theme",
        ],
        "headlines_pool": [
            "DASHCAM 3 CÁMARAS $298",
            "TU TESTIGO 24/7",
            "50% OFF · $298",
            "FULL HD 1080p $298",
            "EVIDENCIA EN VIDEO",
            "$298 · ANTES $599",
            "GRABACIÓN AUTOMÁTICA",
            "PROTÉGETE EN LA CARRETERA",
            "DVR-3 PRO $298",
            "VISIÓN NOCTURNA $298",
        ],
    },
    "buds2": {
        "name": "Asva Buds 2 TWS Bluetooth 5.3 $149",
        "adset_id": None,  # No adset yet, will be created
        "campaign_id": None,
        "page_id": "477739852100670",
        "link_url": "https://sonixmx.com.mx/audifonos-buds2/",
        "price_now": 149,
        "price_was": 399,
        "source_photos": ["assets/source/buds_hero.jpg", "assets/source/buds_case.jpg"],
        "imagen_prompts": [
            "White wireless earbuds in charging case on minimalist white surface, Apple-style clean photography",
            "Person wearing white earbuds while jogging in city, lifestyle action shot",
            "White earbuds on a desk next to iPhone and coffee, work from home aesthetic",
            "Macro closeup of white earbud showing acoustic detail, premium product photography",
            "White earbuds on gym equipment, fitness lifestyle, sporty",
        ],
        "headlines_pool": [
            "BUDS 2 · $149",
            "INALÁMBRICOS $149",
            "BLUETOOTH 5.3 $149",
            "30H BATERÍA $149",
            "$149 · TWS BLANCOS",
            "SIN CABLES $149",
            "DRIVER 13MM",
            "TUS BUDS · $149",
            "CONTROL TÁCTIL",
            "$149 ASVA BUDS",
        ],
    },
}

# Fatigue thresholds
FATIGUE_FREQ_THRESHOLD = 4.0    # frequency > 4 = audience burnout
FATIGUE_CTR_DROP_PCT = 0.30     # CTR fell 30% vs 7d baseline = fatigue

BENCH_DIR = Path("assets/creative-bench")
SOURCE_DIR = Path("assets/source")
BENCH_TARGET = 30               # target inventory per product
BENCH_MIN = 5                   # generate more when below this


# ============================ META API HELPERS ============================
def graph_get(endpoint, params=None):
    p = dict(params or {})
    p["access_token"] = META_TOKEN
    r = requests.get(f"{META_GRAPH}/{endpoint}", params=p, timeout=30)
    return r.json() if r.status_code == 200 else {}

def graph_post(endpoint, data, files=None):
    d = dict(data)
    d["access_token"] = META_TOKEN
    r = requests.post(f"{META_GRAPH}/{endpoint}", data=d, files=files, timeout=60)
    return r.status_code, r.json() if r.headers.get("content-type","").startswith("application/json") else r.text


# ============================ FATIGUE DETECTION ============================
def detect_fatigue(adset_id):
    """Return list of fatigued ad_ids in this adset."""
    ads = graph_get(f"{adset_id}/ads", {
        "fields": "id,name,effective_status,creative",
        "limit": 50,
    }).get("data", [])

    fatigued = []
    for ad in ads:
        if ad.get("effective_status") != "ACTIVE":
            continue
        # Pull insights last 1d and last 7d
        ins_1d = graph_get(f"{ad['id']}/insights", {
            "fields": "ctr,frequency,impressions",
            "date_preset": "yesterday",
        }).get("data", [])
        ins_7d = graph_get(f"{ad['id']}/insights", {
            "fields": "ctr,frequency,impressions",
            "date_preset": "last_7d",
        }).get("data", [])

        if not ins_1d:
            continue
        d1 = ins_1d[0]
        ctr1 = float(d1.get("ctr", 0))
        freq1 = float(d1.get("frequency", 0))
        imp1 = int(d1.get("impressions", 0))

        ctr7 = float(ins_7d[0].get("ctr", 0)) if ins_7d else ctr1

        reason = None
        if freq1 > FATIGUE_FREQ_THRESHOLD:
            reason = f"frequency {freq1:.2f} > {FATIGUE_FREQ_THRESHOLD}"
        elif ctr7 > 0 and (ctr1 / ctr7) < (1 - FATIGUE_CTR_DROP_PCT) and imp1 > 500:
            reason = f"CTR dropped {(1 - ctr1/ctr7)*100:.0f}% vs 7d baseline ({ctr7:.1f}% → {ctr1:.1f}%)"

        if reason:
            fatigued.append({
                "ad_id": ad["id"],
                "name": ad.get("name", ""),
                "creative_id": ad.get("creative", {}).get("id"),
                "reason": reason,
            })

    return fatigued


# ============================ CREATIVE GENERATION ============================
def imagen_generate(prompt, n=1):
    """Call Google's Imagen via Gemini API. Returns list of bytes (PNG)."""
    if not GEMINI_API_KEY:
        print("    [GEMINI_API_KEY not set — skipping AI generation]")
        return []
    try:
        r = requests.post(
            f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}",
            json={
                "instances": [{"prompt": prompt}],
                "parameters": {"sampleCount": n, "aspectRatio": "4:5", "safetyFilterLevel": "block_few"},
            },
            timeout=60,
        )
        if r.status_code != 200:
            print(f"    [Imagen API error {r.status_code}: {r.text[:200]}]")
            return []
        data = r.json()
        images = []
        for pred in data.get("predictions", []):
            import base64
            b64 = pred.get("bytesBase64Encoded")
            if b64:
                images.append(base64.b64decode(b64))
        return images
    except Exception as e:
        print(f"    [Imagen exception: {e}]")
        return []


def pil_template_overlay(source_path, headline, price_now, price_was, output_path, style="editorial"):
    """Apply PIL text overlay to a source photo. Returns success bool."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("    [PIL not available]")
        return False

    try:
        F_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        F_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        # Try fallback
        if not Path(F_BOLD).exists():
            F_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            F_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

        W, H = 1080, 1350
        im = Image.open(source_path).convert("RGB")

        # Fit-cover crop
        iw, ih = im.size
        s = max(W/iw, H/ih)
        nw, nh = int(iw*s), int(ih*s)
        im = im.resize((nw, nh), Image.LANCZOS)
        left = (nw - W) // 2
        top = (nh - H) // 2
        im = im.crop((left, top, left+W, top+H))

        d = ImageDraw.Draw(im, "RGBA")

        # Dark gradient bottom for legibility
        for y in range(H - 400, H):
            a = int(220 * ((y - (H - 400)) / 400) ** 2)
            d.rectangle([(0, y), (W, y+1)], fill=(0, 0, 0, a))

        # Top accent bar
        d.rectangle([(0, 0), (W, 80)], fill=(220, 38, 38, 230))
        font_top = ImageFont.truetype(F_BOLD, 28)
        d.text((40, 22), "ASVA ELECTRONICS · MERCADO LIBRE", font=font_top, fill=(255,255,255))

        # Headline bottom-left
        font_hl = ImageFont.truetype(F_BOLD, 80)
        d.text((50, H - 350), headline, font=font_hl, fill=(255,255,255))

        # Price block
        font_now = ImageFont.truetype(F_BOLD, 140)
        font_was = ImageFont.truetype(F_REG, 40)
        d.text((50, H - 240), f"${price_now}", font=font_now, fill=(255, 80, 70))
        d.text((50, H - 80), f"antes ${price_was}", font=font_was, fill=(200, 200, 200))
        # Strike through "was"
        bbox = d.textbbox((50, H - 80), f"antes ${price_was}", font=font_was)
        d.line([(bbox[0], (bbox[1]+bbox[3])//2), (bbox[2], (bbox[1]+bbox[3])//2)], fill=(200,200,200), width=3)

        im.save(output_path, quality=92, optimize=True)
        return True
    except Exception as e:
        print(f"    [PIL template error: {e}]")
        return False


def ensure_bench(product_slug, prod):
    """Make sure bench has at least BENCH_MIN creatives. Generate if not."""
    bench = BENCH_DIR / product_slug
    bench.mkdir(parents=True, exist_ok=True)
    existing = list(bench.glob("*.jpg")) + list(bench.glob("*.png"))
    print(f"  [{product_slug}] bench size: {len(existing)} / target {BENCH_TARGET}")

    if len(existing) >= BENCH_MIN:
        return existing

    needed = BENCH_TARGET - len(existing)
    print(f"  [{product_slug}] generating {needed} new creatives...")

    created = []
    # Strategy 1: PIL templater from source photos × headlines pool
    for i in range(min(needed, 15)):
        source = random.choice(prod["source_photos"])
        if not Path(source).exists():
            print(f"    skip — source not found: {source}")
            continue
        headline = random.choice(prod["headlines_pool"])
        out_path = bench / f"pil_{i:03d}_{hashlib.md5(headline.encode()).hexdigest()[:6]}.jpg"
        if pil_template_overlay(source, headline, prod["price_now"], prod["price_was"], out_path):
            created.append(out_path)
            print(f"    ✓ PIL: {out_path.name}")

    # Strategy 2: Imagen (Nano Banana) if budget remaining
    remaining = needed - len(created)
    if remaining > 0 and GEMINI_API_KEY:
        prompts = prod.get("imagen_prompts", [])
        for i, prompt in enumerate(prompts[:remaining]):
            print(f"    Imagen prompt {i+1}/{min(remaining, len(prompts))}: {prompt[:60]}...")
            images = imagen_generate(prompt, n=1)
            for j, img_bytes in enumerate(images):
                out_path = bench / f"ai_{i:03d}_{j}.png"
                out_path.write_bytes(img_bytes)
                # Post-process with PIL: add price overlay
                final_path = bench / f"ai_{i:03d}_{j}_final.jpg"
                headline = random.choice(prod["headlines_pool"])
                if pil_template_overlay(out_path, headline, prod["price_now"], prod["price_was"], final_path):
                    created.append(final_path)
                    out_path.unlink()  # remove un-overlayed version
                    print(f"    ✓ AI: {final_path.name}")
            time.sleep(1)  # rate limit

    print(f"  [{product_slug}] bench now: {len(existing) + len(created)}")
    return existing + created


def deploy_creative_to_meta(image_path, prod):
    """Upload to Meta + create ad_creative + create ad. Returns ad_id or None."""
    if not prod.get("adset_id"):
        return None
    # Upload image
    with open(image_path, "rb") as fh:
        files = {"file": (image_path.name, fh, "image/jpeg")}
        status, resp = graph_post(f"{ACCOUNT_ID}/adimages", {}, files=files)
    if status != 200:
        print(f"    upload failed: {resp}")
        return None
    image_hash = list(resp.get("images", {}).values())[0].get("hash")
    if not image_hash:
        return None

    # Create ad_creative
    creative_payload = {
        "name": f"AUTO_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image_path.stem}",
        "object_story_spec": json.dumps({
            "page_id": prod["page_id"],
            "link_data": {
                "link": prod["link_url"],
                "message": f"{prod['name']} — ahorras ${prod['price_was']-prod['price_now']} en Mercado Libre con envío gratis.",
                "name": prod["name"][:40],
                "image_hash": image_hash,
                "call_to_action": {"type": "SHOP_NOW"},
            },
        }),
    }
    status, resp = graph_post(f"{ACCOUNT_ID}/adcreatives", creative_payload)
    if status != 200:
        print(f"    creative failed: {resp}")
        return None
    creative_id = resp.get("id")

    # Create ad
    ad_payload = {
        "name": f"AUTO_{image_path.stem}",
        "adset_id": prod["adset_id"],
        "creative": json.dumps({"creative_id": creative_id}),
        "status": "ACTIVE",
    }
    status, resp = graph_post(f"{ACCOUNT_ID}/ads", ad_payload)
    return resp.get("id") if status == 200 else None


# ============================ MAIN ============================
def main():
    print(f"=== Sonix Creative Engine · {datetime.now(timezone.utc).isoformat()} ===")
    if not META_TOKEN:
        print("ERR: META_CAPI_ACCESS_TOKEN missing"); sys.exit(1)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report = []

    for slug, prod in PRODUCTS.items():
        print(f"\n--- {slug} · {prod['name']} ---")

        # Step 1: ensure bench has enough creatives
        bench = ensure_bench(slug, prod)

        # Step 2: detect fatigue (only if adset exists)
        if not prod.get("adset_id"):
            print(f"  no adset — skipping fatigue check")
            continue

        fatigued = detect_fatigue(prod["adset_id"])
        print(f"  fatigued ads: {len(fatigued)}")

        for fad in fatigued:
            # Pick a fresh creative from bench
            if not bench:
                print(f"    bench empty — cannot refresh")
                continue
            fresh = random.choice(bench)

            # Pause fatigued ad
            ps, _ = graph_post(fad["ad_id"], {"status": "PAUSED"})
            print(f"    paused {fad['name']} ({fad['reason']}) status={ps}")

            # Deploy fresh
            new_ad = deploy_creative_to_meta(fresh, prod)
            if new_ad:
                print(f"    new ad created: {new_ad} from {fresh.name}")
                report.append({
                    "product": slug,
                    "paused": fad["name"],
                    "reason": fad["reason"],
                    "new_ad": new_ad,
                    "creative_file": fresh.name,
                })
                # Move used creative out of bench
                used = fresh.parent / "used" / fresh.name
                used.parent.mkdir(exist_ok=True)
                fresh.rename(used)

    # Write report
    rp = Path(f"reports/creative-engine-{today}.md")
    rp.parent.mkdir(parents=True, exist_ok=True)
    with open(rp, "w") as f:
        f.write(f"# Sonix Creative Engine · {today}\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n")
        if not report:
            f.write("No fatigued ads detected, no refresh needed.\n")
        else:
            f.write("| Producto | Pausado | Razón | Reemplazado por | Nuevo ad |\n|---|---|---|---|---|\n")
            for r in report:
                f.write(f"| {r['product']} | {r['paused']} | {r['reason']} | {r['creative_file']} | {r['new_ad']} |\n")

    print(f"\nDone. Refreshed {len(report)} ad(s). Report: {rp}")


if __name__ == "__main__":
    main()
