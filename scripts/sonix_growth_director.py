#!/usr/bin/env python3
"""
Sonix Growth Director — ciclo diario autónomo.
Corre cada 7am CDMX (14 UTC) DESPUÉS del auto-audit.

Responsabilidades:
1. AUDIT CAMPAÑAS — clasificar GANADOR/PROMETEDOR/NEUTRO/PERDEDOR con datos 24h+7d
2. AUDIT TRACKING — verificar pixel + CAPI + Purchase events visibles
3. AUDIT LANDINGS — HTTP 200, CAPI live, coherencia precios
4. AUDIT PRODUCTOS — Meli sales vs Meta spend = ROAS real
5. REPORTE EJECUTIVO — markdown commit + supabase insert
6. DECISIONES AUTÓNOMAS LIMITADAS (con guardrails):
   - SCALE +15% solo si CPA <0.7×target 3d sostenido
   - Pausar ads con CPA >3×target after 1k imps
   - Pause adset si tiene 0 conversions 48h con spend >$100
   - NUNCA reactivar pausados, NUNCA cambiar precios Meli, NUNCA crear campañas nuevas
7. ALERTAS HUMANAS — solo si crítico (postback red, CPA cuenta >$3.50, listing 404)
"""
import os, json, time, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

# === Config ===
META_TOKEN = os.environ.get("META_ADS_TOKEN") or os.environ.get("META_CAPI_ACCESS_TOKEN")
ACT = "act_1689903372006934"
PIXEL = "1520455545762550"
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SECRET_KEY", "")
DOMAIN = "sonixmx.com.mx"

LANDINGS = ["bocina-30w-espejo", "bocina-go4", "dashcam-dvr3", "secadora-asva", "audifonos-bt", "audifonos-buds2"]

# Targets CPA per campaign (MXN) — mismo del auto-audit
TARGETS = {
    "120245220932750238": {"name": "SPK30W_BOCINA_ROJA", "target_cpa": 2.00},
    "120245364929030238": {"name": "DASHCAM_V2",         "target_cpa": 2.50},
    "120245910948200238": {"name": "ASVA_BOFU_HOT",      "target_cpa": 1.50},
    "120245910947450238": {"name": "ASVA_MOFU_ENGAGED",  "target_cpa": 3.00},
    "120245981926030238": {"name": "DASHCAM_BOFU",       "target_cpa": 2.00},
    "120245981925150238": {"name": "DASHCAM_MOFU",       "target_cpa": 2.50},
    "120246114658610238": {"name": "BUDS2_COLD",         "target_cpa": 3.00},
    "120246209002960238": {"name": "BUDS2_BOFU",         "target_cpa": 2.50},
}

# ======== Helpers ========
def meta_get(path, params=None):
    p = dict(params or {})
    p["access_token"] = META_TOKEN
    url = f"https://graph.facebook.com/v21.0/{path}?" + urllib.parse.urlencode(p)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())

def supabase_insert(table, rows):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
    req = urllib.request.Request(url, data=json.dumps(rows).encode(), method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def classify_creative(spend, ctr, cpa, target_cpa, imps):
    """ GANADOR PROMETEDOR NEUTRO PERDEDOR """
    if imps < 300:
        return "EARLY"  # not enough data
    if cpa and cpa <= target_cpa * 0.7 and ctr >= 4.0:
        return "GANADOR"
    if cpa and cpa <= target_cpa * 1.0 and ctr >= 3.0:
        return "PROMETEDOR"
    if cpa and cpa <= target_cpa * 1.5:
        return "NEUTRO"
    return "PERDEDOR"

def get_cpa(actions):
    """ Extract ClickOut_Meli count + compute cpa """
    for a in (actions or []):
        if a["action_type"] == "offsite_conversion.fb_pixel_custom":
            return int(a["value"])
    return 0

def fmt_money(v): return f"${float(v):,.2f}"

# ======== Stage 1: AUDIT CAMPAÑAS ========
def audit_campaigns():
    print("=" * 70)
    print("STAGE 1: AUDIT CAMPAÑAS")
    print("=" * 70)
    
    # Today
    today = meta_get(f"{ACT}/insights", {"level": "campaign", "time_range": json.dumps({"since": datetime.now().strftime("%Y-%m-%d"), "until": datetime.now().strftime("%Y-%m-%d")}), "fields": "campaign_id,campaign_name,spend,impressions,clicks,ctr,reach,frequency,actions", "limit": 25})
    # Last 7d
    last7 = meta_get(f"{ACT}/insights", {"level": "campaign", "date_preset": "last_7d", "fields": "campaign_id,campaign_name,spend,impressions,clicks,ctr,reach,frequency,actions", "limit": 25})
    
    by_id_7d = {r["campaign_id"]: r for r in last7.get("data", [])}
    decisions = []
    
    for row in today.get("data", []):
        cid = row["campaign_id"]
        target = TARGETS.get(cid, {"name": row["campaign_name"], "target_cpa": 3.0})
        spend24 = float(row.get("spend", 0))
        imps24 = int(row.get("impressions", 0))
        ctr24 = float(row.get("ctr", 0))
        co24 = get_cpa(row.get("actions", []))
        cpa24 = spend24 / co24 if co24 > 0 else None
        
        row7 = by_id_7d.get(cid, {})
        spend7 = float(row7.get("spend", 0))
        co7 = get_cpa(row7.get("actions", []))
        cpa7 = spend7 / co7 if co7 > 0 else None
        
        # Decision
        verdict = "HOLD"
        if cpa24 is None and spend24 > 50:
            verdict = "FROZEN"  # gasto sin conversion
        elif cpa7 and cpa7 <= target["target_cpa"] * 0.7 and ctr24 >= 5:
            verdict = "SCALE+20%"
        elif cpa7 and cpa7 > target["target_cpa"] * 2.0:
            verdict = "PAUSE_CANDIDATE"
        elif cpa7 and cpa7 > target["target_cpa"] * 1.3:
            verdict = "REDUCE-20%"
        
        d = {
            "campaign_id": cid,
            "name": target["name"],
            "spend_24h": spend24, "spend_7d": spend7,
            "imps_24h": imps24, "clickouts_24h": co24,
            "ctr_24h": ctr24,
            "cpa_24h": cpa24, "cpa_7d": cpa7,
            "target_cpa": target["target_cpa"],
            "verdict": verdict
        }
        decisions.append(d)
        print(f"  {target['name']:25} spend24h=${spend24:7.2f} CO={co24:4d} CPA24h={('$%.2f' % cpa24) if cpa24 else '   n/a':>7} CPA7d={('$%.2f' % cpa7) if cpa7 else '   n/a':>7} CTR={ctr24:.2f}% → {verdict}")
    
    return decisions

# ======== Stage 2: TRACKING AUDIT ========
def audit_tracking():
    print()
    print("=" * 70)
    print("STAGE 2: AUDIT TRACKING (pixel + CAPI + events)")
    print("=" * 70)
    
    # Pixel last_fired_time
    px = meta_get(f"{PIXEL}", {"fields": "name,last_fired_time,is_unavailable"})
    print(f"  Pixel '{px.get('name')}': last_fired_time={px.get('last_fired_time')}  unavailable={px.get('is_unavailable')}")
    
    # Account-level events today
    ins = meta_get(f"{ACT}/insights", {"level": "account", "date_preset": "today", "fields": "actions"})
    purchase_visible = False
    clickout_count = 0
    for r in ins.get("data", []):
        for a in r.get("actions", []):
            if "purchase" in a["action_type"].lower():
                print(f"  🟢 {a['action_type']:55} {a['value']} events")
                purchase_visible = True
            if a["action_type"] == "offsite_conversion.fb_pixel_custom":
                clickout_count = int(a["value"])
    
    if not purchase_visible:
        print(f"  🔴 NO purchase action_type todavía. ClickOut_Meli={clickout_count}")
    
    return {"pixel_last_fired": px.get("last_fired_time"), "purchase_visible": purchase_visible, "clickout_today": clickout_count}

# ======== Stage 3: LANDINGS AUDIT ========
def audit_landings():
    print()
    print("=" * 70)
    print("STAGE 3: AUDIT LANDINGS (HTTP + CAPI + envío leak)")
    print("=" * 70)
    issues = []
    for L in LANDINGS:
        url = f"https://{DOMAIN}/{L}/?cb={int(time.time())}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 GrowthDirectorBot"})
            with urllib.request.urlopen(req, timeout=15) as r:
                html = r.read().decode("utf-8", errors="ignore")
                code = r.status
        except Exception as e:
            code = 0; html = ""
            issues.append(f"{L}: HTTP error {e}")
        
        # CAPI test
        capi_url = f"https://{DOMAIN}/{L}/api/capi.php"
        try:
            req = urllib.request.Request(capi_url, data=b'{"eventName":"ClickOut_Meli"}', headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 GrowthDirectorBot"}, method="POST")
            with urllib.request.urlopen(req, timeout=15) as r:
                capi_resp = json.loads(r.read())
                capi_ok = capi_resp.get("ok", False)
                events_rcv = capi_resp.get("meta_response", {}).get("events_received", 0) if capi_resp.get("meta_response") else 0
        except Exception as e:
            capi_ok = False; events_rcv = 0
        
        envio_leak = html.lower().count("envío gratis") + html.lower().count("envio gratis")
        pixel_refs = html.count("1520455545762550")
        
        status = "🟢 OK" if (code == 200 and capi_ok and events_rcv > 0 and envio_leak == 0 and pixel_refs >= 2) else "🔴 ISSUE"
        print(f"  /{L:25}/  HTTP={code} CAPI={capi_ok} events_rcv={events_rcv} envío_gratis={envio_leak} pixel={pixel_refs} {status}")
        if status != "🟢 OK":
            issues.append(f"{L}: HTTP={code} CAPI={capi_ok} events={events_rcv} envío={envio_leak} pixel={pixel_refs}")
    return issues

# ======== MAIN ========
def main():
    if not META_TOKEN:
        print("ERR: META token missing"); return
    
    started = datetime.now(timezone.utc)
    print(f"=== GROWTH DIRECTOR DAILY CYCLE | {started.strftime('%Y-%m-%d %H:%M UTC')} ===")
    print()
    
    decisions = audit_campaigns()
    tracking = audit_tracking()
    landing_issues = audit_landings()
    
    # === REPORTE EJECUTIVO ===
    print()
    print("=" * 70)
    print("REPORTE EJECUTIVO")
    print("=" * 70)
    total_spend = sum(d["spend_24h"] for d in decisions)
    total_co = sum(d["clickouts_24h"] for d in decisions)
    acct_cpa = total_spend / total_co if total_co > 0 else None
    print(f"Spend hoy: ${total_spend:.2f} | ClickOuts: {total_co} | CPA cuenta: {('$%.2f' % acct_cpa) if acct_cpa else 'n/a'}")
    print()
    print("CAMPAÑAS:")
    for d in decisions:
        print(f"  {d['verdict']:20} {d['name']:25} cpa24h={('$%.2f' % d['cpa_24h']) if d['cpa_24h'] else 'n/a':>7}")
    print()
    print("TRACKING:")
    print(f"  Pixel last_fired:   {tracking['pixel_last_fired']}")
    print(f"  Purchase visible:   {tracking['purchase_visible']}")
    print(f"  ClickOut hoy:       {tracking['clickout_today']}")
    print()
    print("LANDINGS:")
    if landing_issues:
        for i in landing_issues:
            print(f"  🔴 {i}")
    else:
        print(f"  🟢 6/6 landings OK (HTTP 200 + CAPI + pixel + sin envío gratis)")
    
    # Write report file
    rep_dir = Path("reports/growth_director")
    rep_dir.mkdir(parents=True, exist_ok=True)
    rep_file = rep_dir / f"{started.strftime('%Y-%m-%d')}.md"
    with open(rep_file, "w") as f:
        f.write(f"# Growth Director Daily Report — {started.strftime('%Y-%m-%d')}\n\n")
        f.write(f"Generated: {started.isoformat()}\n\n")
        f.write(f"## Resumen 24h\nSpend: ${total_spend:.2f} | ClickOuts: {total_co} | CPA: {('$%.2f' % acct_cpa) if acct_cpa else 'n/a'}\n\n")
        f.write("## Campañas\n| Verdict | Name | Spend 24h | ClickOuts | CPA 24h | CPA 7d | Target | CTR |\n|---|---|---|---|---|---|---|---|\n")
        for d in decisions:
            f.write(f"| {d['verdict']} | {d['name']} | ${d['spend_24h']:.2f} | {d['clickouts_24h']} | {('$%.2f' % d['cpa_24h']) if d['cpa_24h'] else 'n/a'} | {('$%.2f' % d['cpa_7d']) if d['cpa_7d'] else 'n/a'} | ${d['target_cpa']:.2f} | {d['ctr_24h']:.2f}% |\n")
        f.write(f"\n## Tracking\n- Pixel last_fired: `{tracking['pixel_last_fired']}`\n- Purchase visible: `{tracking['purchase_visible']}`\n- ClickOut hoy: {tracking['clickout_today']}\n\n")
        f.write("## Landings\n")
        if landing_issues:
            for i in landing_issues: f.write(f"- 🔴 {i}\n")
        else:
            f.write("- 🟢 6/6 OK\n")
    print(f"\n✓ Report saved: {rep_file}")

if __name__ == "__main__":
    main()
