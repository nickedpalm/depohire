/**
 * FILE LOCATION: functions/subscribe.ts
 * Cloudflare Pages Function — handles POST /subscribe from all forms
 *
 * LISTMONK LIST IDs (mail.firestick.io):
 *   3  = Firestick.io Weekly       (2,331 subscribers — existing)
 *   5  = Firestick.io Newsletter
 *   6  = DepoHire Newsletter
 *   30 = DepoHire Leads            ← quote forms, city page CTAs
 *   31 = DepoHire Blog             ← blog sidebar email capture
 *   32 = Firestick.io Leads
 *   33 = DepoHire Provider Interest ← /advertise/ page signups
 *   34 = Lead Magnet Downloads     ← exit intent, checklist downloads
 *
 * CLOUDFLARE PAGES ENV VARS (set per project in dashboard):
 *   LISTMONK_URL      = https://mail.firestick.io
 *   LISTMONK_API_KEY  = YWRtaW46ZmlyZXN0aWNrMjAyNg==
 *
 * SOURCE → LIST ID ROUTING:
 *   city-quote-form      → 30 (DepoHire Leads)
 *   listing-quote-form   → 30 (DepoHire Leads)
 *   blog-sidebar         → 31 (DepoHire Blog)
 *   exit-intent          → 34 (Lead Magnet Downloads)
 *   provider-signup      → 33 (DepoHire Provider Interest)
 *   default              → 6  (DepoHire Newsletter)
 */

interface Env {
  LISTMONK_URL: string;
  LISTMONK_API_KEY: string;
}

// Route source → list ID
const SOURCE_TO_LIST: Record<string, number> = {
  'city-quote-form':    30,
  'listing-quote-form': 30,
  'blog-sidebar':       31,
  'exit-intent':        34,
  'provider-signup':    33,
};
const DEFAULT_LIST = 6; // DepoHire Newsletter

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const cors = {
    'Access-Control-Allow-Origin': '*',
    'Content-Type': 'application/json',
  };

  try {
    const body = await request.json() as Record<string, string>;
    const { email, name, city, source, caseType, tags: extraTags } = body;

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return new Response(JSON.stringify({ ok: false, error: 'Invalid email' }), { status: 400, headers: cors });
    }

    const base = env.LISTMONK_URL?.replace(/\/$/, '');
    const apiKey = env.LISTMONK_API_KEY;

    if (!base || !apiKey) {
      console.error('Missing LISTMONK_URL or LISTMONK_API_KEY');
      return new Response(JSON.stringify({ ok: false, error: 'Server config error' }), { status: 500, headers: cors });
    }

    const listId = SOURCE_TO_LIST[source] ?? DEFAULT_LIST;

    // Build tags
    const tags: string[] = [`source:${source || 'web'}`, 'domain:depohire'];
    if (city) tags.push(`city:${city.toLowerCase().replace(/\s+/g, '-')}`);
    if (caseType) tags.push(`case-type:${caseType}`);
    if (extraTags) tags.push(...extraTags.split(',').map((t: string) => t.trim()).filter(Boolean));

    const res = await fetch(`${base}/api/subscribers`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Basic ${apiKey}`,
      },
      body: JSON.stringify({
        email,
        name: name || email.split('@')[0],
        status: 'enabled',
        lists: [listId],
        attribs: {
          city: city || '',
          source: source || 'web',
          case_type: caseType || '',
          domain: 'depohire',
        },
        preconfirm_subscriptions: true,
        tags,
      }),
    });

    // 409 = already subscribed — still a success
    if (res.status === 409) {
      return new Response(JSON.stringify({ ok: true, already: true }), { headers: cors });
    }

    if (!res.ok) {
      const err = await res.text();
      console.error('Listmonk error:', err);
      return new Response(JSON.stringify({ ok: false, error: 'Subscription failed' }), { status: 500, headers: cors });
    }

    return new Response(JSON.stringify({ ok: true }), { headers: cors });

  } catch (err) {
    console.error('Subscribe function error:', err);
    return new Response(JSON.stringify({ ok: false, error: 'Server error' }), { status: 500, headers: cors });
  }
};

export const onRequestOptions: PagesFunction = async () =>
  new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
