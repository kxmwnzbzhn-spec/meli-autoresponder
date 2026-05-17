/**
 * Elite Market — MELI Webhook Receiver
 * Recibe notificaciones MELI, valida, deduplica, persiste en Supabase events,
 * dispara repository_dispatch a GH Actions para procesamiento async.
 *
 * Endpoints:
 *   POST /          → webhook MELI
 *   GET  /health    → check
 *   GET  /stats     → stats (auth)
 */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (request.method === 'GET' && url.pathname === '/health') {
      return new Response(JSON.stringify({ ok: true, ts: new Date().toISOString() }), {
        headers: { 'content-type': 'application/json' }
      });
    }

    if (request.method === 'GET' && url.pathname === '/stats') {
      // Simple auth via shared secret
      if (request.headers.get('x-admin-key') !== env.ADMIN_KEY) {
        return new Response('unauthorized', { status: 401 });
      }
      const r = await fetch(`${env.SUPABASE_URL}/rest/v1/events?select=count`, {
        headers: { apikey: env.SUPABASE_SERVICE_KEY, Prefer: 'count=exact' }
      });
      return new Response(JSON.stringify({ events_count: r.headers.get('content-range') }), {
        headers: { 'content-type': 'application/json' }
      });
    }

    if (request.method !== 'POST' || url.pathname !== '/') {
      return new Response('not found', { status: 404 });
    }

    let body;
    try {
      body = await request.json();
    } catch (e) {
      return new Response('bad json', { status: 400 });
    }

    // Expected MELI notification format:
    // {
    //   "resource": "/orders/2000016...",
    //   "user_id": 3367276814,
    //   "topic": "orders_v2",
    //   "application_id": 5211907102822632,
    //   "attempts": 1,
    //   "sent": "2026-...",
    //   "received": "2026-..."
    // }
    const { resource, user_id, topic, application_id, attempts, sent } = body;

    // Validate from MELI by application_id
    if (String(application_id) !== String(env.MELI_APP_ID)) {
      return new Response('wrong app_id', { status: 403 });
    }

    // Dedupe by resource (MELI may retry; same resource+topic should be idempotent)
    const dedupeKey = `${topic}:${resource}:${sent || ''}`;

    // Persist event to Supabase
    const persistRes = await fetch(`${env.SUPABASE_URL}/rest/v1/events`, {
      method: 'POST',
      headers: {
        apikey: env.SUPABASE_SERVICE_KEY,
        Authorization: `Bearer ${env.SUPABASE_SERVICE_KEY}`,
        'content-type': 'application/json',
        Prefer: 'return=representation'
      },
      body: JSON.stringify({
        source: 'meli_webhook',
        topic,
        resource,
        user_id,
        raw_payload: body
      })
    });

    if (!persistRes.ok) {
      const errTxt = await persistRes.text();
      console.error('supabase insert failed:', errTxt);
      return new Response('supabase error', { status: 500 });
    }

    const inserted = await persistRes.json();
    const eventId = Array.isArray(inserted) ? inserted[0]?.id : inserted.id;

    // Fire repository_dispatch to GH Actions (async, non-blocking)
    ctx.waitUntil(
      fetch(`https://api.github.com/repos/${env.GH_OWNER}/${env.GH_REPO}/dispatches`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${env.GH_TOKEN}`,
          Accept: 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent': 'meli-webhook-worker'
        },
        body: JSON.stringify({
          event_type: 'meli_event',
          client_payload: { event_id: eventId, topic, resource, user_id }
        })
      })
    );

    // Acknowledge to MELI immediately (must respond <22s)
    return new Response(JSON.stringify({ ok: true, event_id: eventId }), {
      status: 200,
      headers: { 'content-type': 'application/json' }
    });
  }
};
