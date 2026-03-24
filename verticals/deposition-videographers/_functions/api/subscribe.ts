/**
 * Cloudflare Pages Function: Newsletter Subscribe
 *
 * POST /api/subscribe
 * Subscribes an email to the DepoHire newsletter list via Listmonk.
 */

import type { Env } from '../_types';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

function jsonResp(data: any, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders },
  });
}

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  let payload: any;
  try {
    payload = await request.json();
  } catch {
    return jsonResp({ error: 'Invalid JSON' }, 400);
  }

  const email = (payload.email || '').trim().toLowerCase();
  if (!email || !email.includes('@') || email.length < 5) {
    return jsonResp({ error: 'Valid email required' }, 400);
  }

  const name = (payload.name || '').trim();
  const city = (payload.city || '').trim();
  const listId = payload.list_id ? Number(payload.list_id) : null;

  // Guide delivery fields (optional)
  const guideTitle = (payload.guide_title || '').trim();
  const guidePdfUrl = (payload.guide_pdf_url || '').trim();

  const url = env.LISTMONK_URL || 'https://mail.firestick.io';
  const user = env.LISTMONK_USER || 'admin';
  const pass = env.LISTMONK_PASS || '';
  const authHeader = 'Basic ' + btoa(`${user}:${pass}`);

  // Listmonk list ID for DepoHire newsletter
  const DEPOHIRE_LIST_ID = 6;
  const lists = [DEPOHIRE_LIST_ID];
  if (listId && listId !== DEPOHIRE_LIST_ID) lists.push(listId);

  // Build subscriber attributes for segmentation
  const attribs: Record<string, any> = {};
  if (city) attribs.city = city;

  try {
    // Step 1: Create subscriber (or get existing)
    const resp = await fetch(`${url}/api/subscribers`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify({
        email,
        name: name || '',
        status: 'enabled',
        lists,
        attribs: Object.keys(attribs).length > 0 ? attribs : undefined,
        preconfirm_subscriptions: true,
      }),
    });

    let subscriberId: number | null = null;

    if (resp.ok) {
      try {
        const data = await resp.json() as any;
        subscriberId = data?.data?.id || null;
      } catch {}
    } else if (resp.status === 409) {
      // Subscriber already exists — look up their ID
      try {
        const lookupResp = await fetch(`${url}/api/subscribers?query=subscribers.email='${encodeURIComponent(email)}'&page=1&per_page=1`, {
          headers: { 'Authorization': authHeader },
        });
        if (lookupResp.ok) {
          const lookupData = await lookupResp.json() as any;
          subscriberId = lookupData?.data?.results?.[0]?.id || null;
        }
      } catch {}
    } else {
      const text = await resp.text();
      console.error(`Listmonk subscribe failed: ${resp.status} ${text}`);
      return jsonResp({ error: 'Subscription failed' }, 502);
    }

    // Step 2: Explicitly add subscriber to lists (Listmonk v6 workaround)
    if (subscriberId) {
      try {
        await fetch(`${url}/api/subscribers/lists`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': authHeader,
          },
          body: JSON.stringify({
            ids: [subscriberId],
            action: 'add',
            target_list_ids: lists,
            status: 'confirmed',
          }),
        });
      } catch (err) {
        console.error('Failed to add subscriber to lists:', err);
      }
    }

    // If this is a guide download request, send the delivery email
    if (guideTitle && guidePdfUrl) {
      try {
        // Listmonk transactional API — sends via the "guide-delivery" template
        const txResp = await fetch(`${url}/api/tx`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': authHeader,
          },
          body: JSON.stringify({
            subscriber_email: email,
            template_id: 7, // guide-delivery transactional template in Listmonk
            data: {
              name: name || 'there',
              guide_title: guideTitle,
              pdf_url: guidePdfUrl,
            },
            content_type: 'html',
            messenger: 'email',
          }),
        });

        if (!txResp.ok) {
          const txText = await txResp.text();
          console.error(`Guide delivery email failed: ${txResp.status} ${txText}`);
          // Don't fail the whole request — subscription succeeded
        }
      } catch (txErr) {
        console.error('Guide delivery email error:', txErr);
      }
    }

    return jsonResp({ status: 'ok' });
  } catch (err) {
    console.error('Subscribe error:', err);
    return jsonResp({ error: 'Service unavailable' }, 503);
  }
};

export const onRequestOptions: PagesFunction = async () => {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400',
    },
  });
};
