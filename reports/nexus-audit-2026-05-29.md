# NEXUS Audit · 2026-05-29 (manual override via Cowork session)

**Engine:** NEXUS (Cowork MCP path — Pipeboard Pro)
**Postback health:** ✅ Verde (5+ runs consecutivos)
**Data window:** Yesterday (2026-05-28 full day) + Today in-progress (2026-05-29)

## Decisiones aplicadas

| Campaña | Estado | CPA 24h | CTR | Freq | Budget Before → After | Razón |
|---|---|---|---|---|---|---|
| 🔴 Bocina Roja $199 (ABO winner) | ✅ SCALE+15 | $1.26 | 6.81% | 1.30 | $400 → **$460** | CPA 63% target, CTR 6.8%, budget tapped (spent 141%) |
| 🚗 Dashcam DVR-3 (CBO) | ✅ SCALE+15 | $1.98 | 6.49% | 1.23 | $288 → **$331** | CPA 79% target, CTR sólido |
| 📍 MOFU Global | ✅ REDUCE-20 | $4.36 | 5.77% | 1.14 | $60 → **$48** | CPA 145% target, audiencia visitante no convierte como esperado |
| 🎯 BOFU Global | ⚠️ **PAUSE** | $3.11 | 6.68% → 3.51% hoy | 1.16 | $100 → $0 | CPA 207% target + CTR colapsando = audiencia ClickOut saturada. Reconstruir con nuevos creativos o nueva ventana 7d. |
| 🚗 Dashcam MOFU | ➖ HOLD | $3.15 | 9.83% | 1.04 | $40 | Dentro de target $3.50. CTR brutal. |
| 🚗 Dashcam BOFU | ➖ HOLD | $1.83 | 8.91% | 1.06 | $60 | Dentro de target $2.00. Performando bien. |

## Saldo neto

- Spend antes: **$948/día**
- Spend después: **$939/día** (-$9, ahorra del BOFU pausado + REDUCE MOFU; reasigna a TOFU winners)
- Hard cap $1,500 MXN: 63% utilizado, headroom para escalar más cuando los winners reciban el bump

## Observaciones NEXUS

1. **Bocina Roja $199 es el rey absoluto.** CPA $1.26 vs target $2.00 = la mejor unit economics del cluster. ROAS implícito Meli >8x. Si stock aguanta, escalable a $600-700/día sin perder eficiencia.
2. **BOFU Global muerto** — la audiencia ClickOut 14d se está agotando (creada hace 4 días, mucho overlap con buyers). Necesita o creativos nuevos (refresh para reactivar interés) o ventana audiencia más fresca (ClickOut 7d en lugar de 14d).
3. **Dashcam BOFU específico vivo** — la audiencia targeted al landing dashcam funciona mucho mejor que el global. Confirma tesis: per-product retargeting > global.
4. **MOFU global cuestionable** — visitantes que no clickearon a Meli probablemente no van a comprar. Considerar pausar también o re-orientar a engaged users con video views.
5. **Próxima decisión** (24h): si Bocina sostiene CPA <$1.50 mañana → segundo SCALE+15 hasta $530.

## Próximos pasos auto-ejecutados (sin requerir tu input)

- Daily 7am CDMX: NEXUS audit + ejecución vía Cowork session (Pipeboard Pro)
- Cada hora: Postback Meli → Pixel (GH Actions)
- Cada 30 min: Meli health check (GH Actions)
- TBD: Creative engine (cuando GEMINI_API_KEY se agregue)

## Bloqueadores pendientes (tuyos cuando quieras)

1. Listing Meli MLMU3924350212 sigue en $298 — bajar a $199 para coincidir con landing
2. GEMINI_API_KEY como secret en repo para activar creative engine en cloud
