/**
 * POST /api/stripe-webhook
 *
 * Handles Stripe webhook events:
 * - checkout.session.completed → activate Featured status
 * - customer.subscription.deleted → deactivate Featured status
 *
 * Stripe sends the listing slug via client_reference_id on the Payment Link.
 */

interface Env {
  LEADS_DB: D1Database;
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
}

// Verify Stripe webhook signature using Web Crypto API
async function verifyStripeSignature(
  payload: string,
  sigHeader: string,
  secret: string
): Promise<boolean> {
  const parts = sigHeader.split(',').reduce((acc, part) => {
    const [key, val] = part.split('=');
    acc[key] = val;
    return acc;
  }, {} as Record<string, string>);

  const timestamp = parts['t'];
  const signature = parts['v1'];

  if (!timestamp || !signature) return false;

  // Reject if timestamp is more than 5 minutes old
  const age = Math.floor(Date.now() / 1000) - parseInt(timestamp);
  if (age > 300) return false;

  const signedPayload = `${timestamp}.${payload}`;
  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const sig = await crypto.subtle.sign(
    'HMAC',
    key,
    new TextEncoder().encode(signedPayload)
  );

  const expected = Array.from(new Uint8Array(sig))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');

  // Constant-time comparison to prevent timing attacks
  const a = new TextEncoder().encode(expected);
  const b = new TextEncoder().encode(signature);
  if (a.byteLength !== b.byteLength) return false;
  return crypto.subtle.timingSafeEqual(a, b);
}

async function handleCheckoutCompleted(session: any, db: D1Database) {
  const listingSlug = session.client_reference_id;
  const customerEmail = session.customer_details?.email || session.customer_email;
  const customerId = session.customer;
  const subscriptionId = session.subscription;

  if (!listingSlug) {
    console.error('Stripe checkout: no client_reference_id (listing slug)');
    return;
  }

  console.log(`Featured activation: slug=${listingSlug} email=${customerEmail} sub=${subscriptionId}`);

  // Verify the listing is claimed and the customer email matches the owner
  const claim = await db.prepare(
    `SELECT cl.id, cl.provider_id, cl.data_json, p.email as provider_email
     FROM claimed_listings cl
     JOIN providers p ON p.id = cl.provider_id
     WHERE cl.listing_slug = ?`
  ).bind(listingSlug).first<{ id: number; provider_id: number; data_json: string; provider_email: string }>();

  if (!claim) {
    console.error(`Stripe checkout: listing ${listingSlug} is not claimed — cannot activate Featured`);
    return;
  }

  // Verify email matches (case-insensitive)
  if (customerEmail && claim.provider_email &&
      customerEmail.toLowerCase() !== claim.provider_email.toLowerCase()) {
    console.error(`Stripe checkout: email mismatch — Stripe: ${customerEmail}, provider: ${claim.provider_email}, slug: ${listingSlug}`);
    return;
  }

  // Record subscription with provider_id
  await db.prepare(
    `INSERT INTO subscriptions (listing_slug, provider_id, stripe_customer_id, stripe_subscription_id, customer_email, plan, status, created_at)
     VALUES (?, ?, ?, ?, ?, 'featured', 'active', ?)`
  ).bind(listingSlug, claim.provider_id, customerId, subscriptionId, customerEmail, new Date().toISOString()).run();

  // Update claimed_listings data_json to set featured=true
  let data: Record<string, any> = {};
  try { data = JSON.parse(claim.data_json || '{}'); } catch {}
  data.featured = true;
  data.stripe_subscription_id = subscriptionId;
  await db.prepare(
    `UPDATE claimed_listings SET data_json = ? WHERE id = ?`
  ).bind(JSON.stringify(data), claim.id).run();
}

async function handleSubscriptionDeleted(subscription: any, db: D1Database) {
  const subscriptionId = subscription.id;

  console.log(`Featured deactivation: sub=${subscriptionId}`);

  // Find which listing this subscription belongs to
  const sub = await db.prepare(
    `SELECT listing_slug FROM subscriptions WHERE stripe_subscription_id = ?`
  ).bind(subscriptionId).first<{ listing_slug: string }>();

  if (!sub) {
    console.error(`No subscription found for ${subscriptionId}`);
    return;
  }

  // Mark subscription canceled
  await db.prepare(
    `UPDATE subscriptions SET status = 'canceled', canceled_at = ? WHERE stripe_subscription_id = ?`
  ).bind(new Date().toISOString(), subscriptionId).run();

  // Check if any other active subscription exists for this listing
  const activeCount = await db.prepare(
    `SELECT COUNT(*) as cnt FROM subscriptions WHERE listing_slug = ? AND status = 'active'`
  ).bind(sub.listing_slug).first<{ cnt: number }>();

  if (activeCount && activeCount.cnt > 0) return; // Still has an active sub

  // Remove featured flag from claimed_listings
  const existing = await db.prepare(
    `SELECT data_json FROM claimed_listings WHERE listing_slug = ?`
  ).bind(sub.listing_slug).first<{ data_json: string }>();

  if (existing) {
    const data = JSON.parse(existing.data_json || '{}');
    data.featured = false;
    delete data.stripe_subscription_id;
    await db.prepare(
      `UPDATE claimed_listings SET data_json = ? WHERE listing_slug = ?`
    ).bind(JSON.stringify(data), sub.listing_slug).run();
  }
}

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const webhookSecret = env.STRIPE_WEBHOOK_SECRET;
  if (!webhookSecret) {
    console.error('STRIPE_WEBHOOK_SECRET not configured');
    return new Response('Server misconfigured', { status: 500 });
  }

  const body = await request.text();
  const sigHeader = request.headers.get('stripe-signature') || '';

  const valid = await verifyStripeSignature(body, sigHeader, webhookSecret);
  if (!valid) {
    console.error('Invalid Stripe webhook signature');
    return new Response('Invalid signature', { status: 401 });
  }

  const event = JSON.parse(body);
  console.log(`Stripe event: ${event.type} id=${event.id}`);

  // Idempotency: skip already-processed events
  try {
    const existing = await env.LEADS_DB.prepare(
      `SELECT id FROM processed_events WHERE event_id = ?`
    ).bind(event.id).first();
    if (existing) {
      console.log(`Duplicate event ${event.id}, skipping`);
      return new Response(JSON.stringify({ received: true, duplicate: true }), {
        status: 200, headers: { 'Content-Type': 'application/json' },
      });
    }
  } catch {
    // Table may not exist yet — continue processing
  }

  try {
    switch (event.type) {
      case 'checkout.session.completed':
        await handleCheckoutCompleted(event.data.object, env.LEADS_DB);
        break;

      case 'customer.subscription.deleted':
        await handleSubscriptionDeleted(event.data.object, env.LEADS_DB);
        break;

      default:
        console.log(`Unhandled event type: ${event.type}`);
    }
    // Record processed event for idempotency
    try {
      await env.LEADS_DB.prepare(
        `INSERT OR IGNORE INTO processed_events (event_id, event_type, processed_at) VALUES (?, ?, ?)`
      ).bind(event.id, event.type, new Date().toISOString()).run();
    } catch {}
  } catch (err) {
    console.error(`Webhook handler error: ${err}`);
    // Still return 200 so Stripe doesn't retry
  }

  return new Response(JSON.stringify({ received: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
};
