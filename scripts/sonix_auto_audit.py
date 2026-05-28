"""
Sonix Auto-Audit — cloud-native marketing engine.

Runs daily via GitHub Actions at 13:00 UTC (07:00 CDMX).
Pulls Meta Ads insights, applies scaling decisions per AUTOMATION_RULES,
executes budget changes, writes daily report.

Safety caps:
- HARD CAP: total daily account spend ≤ $1,500 MXN (150000 cents)
- PER-CYCLE: no campaign changes more than ±30%
- NEVER reactivate user-paused campaigns
- ABORT if postback workflow has been red for 3+ consecutive runs

Env vars required:
- META_CAPI_ACCESS_TOKEN (also used by postback workflow)
"""

import os, sys, json, requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ============================ CONFIG ============================
ACCOUNT_ID = "act_1689903372006934"
PIXEL_ID = "1520455545762550"
META_GRAPH = "https://graph.facebook.com/v21.0"
META_TOKEN = os.environ.get("META_CAPI_ACCESS_TOKEN")
HARD_CAP_TOTAL_CENTS = 150000  # $1,500 MXN
PER_CYCLE_CAP_PCT = 0.30

# Target CPA per campaign (in MXN dollars — script multiplies by 100 internally)
TARGETS = {
    "120245220932750238": {
        "name": "Bocina Roja $199",
        "target_cpa": 2.00,
        "type": "ABO",
        "adset_id": "120245312737330238",
    },
    "120245364929030238": {
        "name": "Dashcam DVR-3",
        "target_cpa": 2.50,
        "type": "CBO",
    },
    "120245910948200238": {
        "name": "BOFU Global",
        "target_cpa": 1.50,
        "type": "CBO",
    },
    "120245910947450238": {
        "name": "MOFU Global",
        "target_cpa": 3.00,
        "type": "CBO",
    },
    "120245981925150238": {
        "name": "Dashcam MOFU",
        "target_cpa": 3.50,
        "type": "CBO",
    },
    "120245981926030238": {
        "name": "Dashcam BOFU",
        "target_cpa": 2.00,
        "type": "CBO",
    },
}

# User-paused campaigns — NEVER reactivate
NEVER_REACTIVATE = {
    "120245420037700238",  # Go4 Wilbert
    "120245413757980238",  # Audífonos YC
    "120245394293630238",  # Secadora ASVA
}


# ============================ HELPERS ============================
def graph_get(endpoint, params=None):
    params = dict(params or {})
    params["access_token"] = META_TOKEN
    r = requests.get(f"{META_GRAPH}/{endpoint}", params=params, timeout=30)
    if r.status_code != 200:
        print(f"  GET {endpoint} -> {r.status_code}: {r.text[:200]}")
    return r.json() if r.status_code == 200 else {}


def graph_post(endpoint, data):
    data = dict(data)
    data["access_token"] = META_TOKEN
    r = requests.post(f"{META_GRAPH}/{endpoint}", data=data, timeout=30)
    return r.status_code, r.text


def get_active_campaigns():
    return graph_get(f"{ACCOUNT_ID}/campaigns", {
        "fields": "id,name,status,effective_status,daily_budget,objective",
        "effective_status": '["ACTIVE"]',
        "limit": 50,
    }).get("data", [])


def get_campaign_insights(cid, time_range_str="today"):
    """time_range_str: 'today', 'yesterday', 'last_7d'"""
    return graph_get(f"{cid}/insights", {
        "fields": "spend,clicks,impressions,ctr,reach,frequency,actions",
        "date_preset": time_range_str,
    }).get("data", [])


def get_adset_budget(adset_id):
    j = graph_get(adset_id, {"fields": "daily_budget,status"})
    return int(j.get("daily_budget", 0))


def get_postback_health():
    """Check if the postback workflow has been failing — abort scaling if 3+ red."""
    # Note: this checks GH Actions via Public API (works for public repos or with token).
    # For private repos, GITHUB_TOKEN env can be used (auto-injected in Actions context).
    try:
        gh_token = os.environ.get("GITHUB_TOKEN", "")
        headers = {"Authorization": f"token {gh_token}"} if gh_token else {}
        r = requests.get(
            "https://api.github.com/repos/kxmwnzbzhn-spec/meli-autoresponder/actions/workflows/meta_capi_purchase_postback.yml/runs",
            headers=headers,
            params={"per_page": 5},
            timeout=15,
        )
        if r.status_code != 200:
            return True, "Could not check postback health (continuing)"
        runs = r.json().get("workflow_runs", [])
        recent_3 = runs[:3]
        if not recent_3:
            return True, "no postback runs found"
        all_red = all(run.get("conclusion") == "failure" for run in recent_3)
        if all_red:
            return False, f"Postback workflow RED 3+ runs in a row — aborting scaling"
        return True, f"Postback workflow healthy (last 3: {[r.get('conclusion') for r in recent_3]})"
    except Exception as e:
        return True, f"postback health check failed: {e}"


# ============================ DECISION ENGINE ============================
def extract_metrics(insights_data):
    if not insights_data:
        return None
    d = insights_data[0]
    spend = float(d.get("spend", 0))
    ctr = float(d.get("ctr", 0))
    freq = float(d.get("frequency", 1))
    impressions = int(d.get("impressions", 0))
    clickouts = 0
    for a in d.get("actions", []):
        if a.get("action_type") in ("offsite_conversion.fb_pixel_custom",
                                     "offsite_conversion.fb_pixel_custom.ClickOut_Meli"):
            clickouts = max(clickouts, int(a.get("value", 0)))
    cpa = (spend / clickouts) if clickouts > 0 else None
    return {
        "spend": spend, "ctr": ctr, "freq": freq, "impressions": impressions,
        "clickouts": clickouts, "cpa": cpa,
    }


def decide(metrics, target_cpa, current_budget_cents):
    """Return (decision, new_budget_cents, reason)."""
    if not metrics or metrics["cpa"] is None:
        # Delivery zombie if budget > 0 but no impressions for the period
        if current_budget_cents > 0 and metrics and metrics["impressions"] == 0:
            return ("PAUSE", current_budget_cents, "zombie: 0 impressions w/ active budget")
        return ("HOLD", current_budget_cents, "no CPA data (insufficient sample)")

    cpa = metrics["cpa"]
    ctr = metrics["ctr"]
    freq = metrics["freq"]
    spend = metrics["spend"]
    spend_pct = (spend * 100) / current_budget_cents if current_budget_cents else 0

    # PAUSE — catastrophic
    if cpa > target_cpa * 2:
        return ("PAUSE", current_budget_cents, f"CPA ${cpa:.2f} > 2x target ${target_cpa:.2f}")
    if freq > 5:
        return ("PAUSE", current_budget_cents, f"frequency {freq:.2f} too high (audience burnout)")

    # SCALE+30 — winner with budget pressure
    if cpa < target_cpa * 0.6 and ctr > 5 and freq < 2.5 and spend_pct > 0.9:
        new_b = int(current_budget_cents * 1.3)
        return ("SCALE+30", new_b, f"CPA ${cpa:.2f} <60% target, CTR {ctr:.1f}%, budget tapped")

    # SCALE+15 — performing well
    if cpa < target_cpa * 0.85 and ctr > 4 and freq < 3:
        new_b = int(current_budget_cents * 1.15)
        return ("SCALE+15", new_b, f"CPA ${cpa:.2f} <85% target, CTR {ctr:.1f}%")

    # REDUCE-20 — under target
    if cpa > target_cpa * 1.3:
        new_b = int(current_budget_cents * 0.80)
        return ("REDUCE-20", new_b, f"CPA ${cpa:.2f} >1.3x target ${target_cpa:.2f}")

    # HOLD — within range
    return ("HOLD", current_budget_cents, f"CPA ${cpa:.2f} within ±15% target")


def execute_decision(cid, decision, new_budget_cents, target_info):
    """Apply the decision via Meta API. Returns (success, message)."""
    if decision == "HOLD":
        return True, "no change"

    if decision == "PAUSE":
        s, t = graph_post(cid, {"status": "PAUSED"})
        return s == 200, f"pause status={s}"

    # Budget changes — depends on ABO vs CBO
    endpoint_id = target_info.get("adset_id", cid) if target_info.get("type") == "ABO" else cid
    s, t = graph_post(endpoint_id, {"daily_budget": new_budget_cents})
    return s == 200, f"budget update status={s}"


# ============================ REPORT ============================
def write_report(decisions, postback_msg, today_str, total_after_cents, aborted=False):
    report_path = Path(f"reports/auto-audit-{today_str}.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        f.write(f"# Sonix Auto-Audit · {today_str}\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n")

        if aborted:
            f.write("## ⛔ AUDIT ABORTED\n\n")
            f.write(f"{postback_msg}\n\n")
            return

        f.write(f"**Postback health:** {postback_msg}\n\n")
        f.write(f"**Total new daily budget:** ${total_after_cents/100:.2f} MXN ")
        f.write(f"(cap: ${HARD_CAP_TOTAL_CENTS/100:.0f})\n\n")

        f.write("## Decisions\n\n")
        f.write("| Campaign | Decision | CPA 24h | CTR | Freq | Budget Before → After | Reason |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for d in decisions:
            m = d.get("metrics") or {}
            cpa = f"${m['cpa']:.2f}" if m.get('cpa') is not None else "—"
            ctr = f"{m.get('ctr', 0):.1f}%" if m else "—"
            freq = f"{m.get('freq', 0):.2f}" if m else "—"
            bb = f"${d['current_budget']/100:.0f}" if d.get('current_budget') else "—"
            ba = f"${d['new_budget']/100:.0f}" if d.get('new_budget') else "—"
            exec_status = "✅" if d.get("executed") else "⚠️" if d["decision"] != "HOLD" else "—"
            f.write(f"| {d['name']} | {d['decision']} {exec_status} | {cpa} | {ctr} | {freq} | {bb} → {ba} | {d['reason']} |\n")

        # Alerts
        alerts = [d for d in decisions if d["decision"] in ("PAUSE",) or "ALERT" in d.get("reason", "")]
        if alerts:
            f.write("\n## ⚠️ Alerts\n\n")
            for a in alerts:
                f.write(f"- **{a['name']}**: {a['reason']}\n")

    print(f"Report written: {report_path}")
    return report_path


# ============================ MAIN ============================
def main():
    print(f"=== Sonix Auto-Audit · {datetime.now(timezone.utc).isoformat()} ===")

    if not META_TOKEN:
        print("ERR: META_CAPI_ACCESS_TOKEN env var missing")
        sys.exit(1)

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Step 1: postback health check
    postback_ok, postback_msg = get_postback_health()
    print(f"Postback check: {postback_msg}")
    if not postback_ok:
        write_report([], postback_msg, today_str, 0, aborted=True)
        print("ABORTED: postback unhealthy, no scaling executed")
        sys.exit(2)

    # Step 2: get active campaigns
    campaigns = get_active_campaigns()
    print(f"Active campaigns: {len(campaigns)}")

    decisions = []
    total_new_budget = 0
    pending_executions = []

    for c in campaigns:
        cid = c["id"]
        name = c["name"]

        if cid in NEVER_REACTIVATE:
            print(f"  [{name}] SKIP — user-paused, never touch")
            continue

        target_info = TARGETS.get(cid)
        if not target_info:
            decisions.append({
                "name": name, "cid": cid, "decision": "UNKNOWN_TARGET",
                "reason": "No target_cpa defined in TARGETS — review CLAUDE.md AUTOMATION_RULES",
                "current_budget": int(c.get("daily_budget", 0)),
                "new_budget": int(c.get("daily_budget", 0)),
                "metrics": None,
            })
            continue

        # Budget lookup — ABO uses adset budget, CBO uses campaign
        if target_info["type"] == "ABO":
            current_budget = get_adset_budget(target_info["adset_id"])
        else:
            current_budget = int(c.get("daily_budget", 0))

        # Pull insights
        insights = get_campaign_insights(cid, "yesterday")
        metrics = extract_metrics(insights)

        decision, new_budget, reason = decide(metrics, target_info["target_cpa"], current_budget)

        # Apply per-cycle cap
        if current_budget > 0:
            max_delta = int(current_budget * PER_CYCLE_CAP_PCT)
            if abs(new_budget - current_budget) > max_delta:
                new_budget = current_budget + (max_delta if new_budget > current_budget else -max_delta)
                reason += " (capped at ±30%)"

        decisions.append({
            "name": name, "cid": cid, "decision": decision,
            "current_budget": current_budget, "new_budget": new_budget,
            "metrics": metrics, "reason": reason, "target_info": target_info,
        })

        if decision != "HOLD":
            pending_executions.append(decisions[-1])

        total_new_budget += new_budget
        print(f"  [{name}] {decision}: ${current_budget/100:.0f} → ${new_budget/100:.0f} ({reason})")

    # Step 3: hard cap enforcement
    if total_new_budget > HARD_CAP_TOTAL_CENTS:
        print(f"!! Total budget ${total_new_budget/100:.0f} exceeds cap ${HARD_CAP_TOTAL_CENTS/100:.0f} — proportional reduction")
        # Proportionally reduce SCALE decisions to fit cap
        ratio = HARD_CAP_TOTAL_CENTS / total_new_budget
        for d in pending_executions:
            if d["decision"].startswith("SCALE"):
                d["new_budget"] = int(d["new_budget"] * ratio)
                d["reason"] += " (hard-cap reduced)"
        total_new_budget = sum(d.get("new_budget", 0) for d in decisions)

    # Step 4: execute
    for d in pending_executions:
        success, msg = execute_decision(d["cid"], d["decision"], d["new_budget"], d.get("target_info") or {})
        d["executed"] = success
        d["execute_msg"] = msg
        print(f"  EXEC [{d['name']}] {d['decision']}: {'OK' if success else 'FAILED'} ({msg})")

    # Step 5: write report
    report_path = write_report(decisions, postback_msg, today_str, total_new_budget)

    # Step 6: exit code — non-zero only if critical needs attention
    pauses = [d for d in decisions if d["decision"] == "PAUSE"]
    if pauses:
        print(f"⚠️ {len(pauses)} campaign(s) auto-paused — see report")
        sys.exit(3)  # non-fatal but notable

    print(f"\nAudit complete · {len(pending_executions)} change(s) executed · total spend now ${total_new_budget/100:.0f}/day")


if __name__ == "__main__":
    main()
