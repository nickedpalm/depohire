/**
 * GET /provider/verify/:code
 * Friendly magic link URL — delegates to the same verification logic as /api/auth/verify
 */
import type { Env } from '../../_types';
import { generateToken, sessionCookie } from '../../_auth';
import { getListingContact, domainsMatch } from '../../_listings';
import { normalizePhone, maskPhone, generateCode, sendVerificationSMS } from '../../_twilio';
import { notifyAdminPendingClaim } from '../../_admin';

export const onRequestGet: PagesFunction<Env> = async ({ params, request, env }) => {
  const token = params.code as string;

  if (!token || token.length < 6) {
    return redirectWithError('Invalid link');
  }

  const now = new Date().toISOString();

  // Look up magic link by token
  const link = await env.LEADS_DB.prepare(
    `SELECT id, email, listing_slug, expires_at, used FROM magic_links WHERE token = ?`
  ).bind(token).first<{ id: number; email: string; listing_slug: string | null; expires_at: string; used: number }>();

  if (!link) return redirectWithError('Invalid or expired link');
  if (link.used) return redirectWithError('This link has already been used');
  if (link.expires_at < now) return redirectWithError('This link has expired. Please request a new one.');

  // Mark link as used
  await env.LEADS_DB.prepare(
    `UPDATE magic_links SET used = 1 WHERE id = ?`
  ).bind(link.id).run();

  // Find or create provider
  let provider = await env.LEADS_DB.prepare(
    `SELECT id, email, name FROM providers WHERE email = ?`
  ).bind(link.email).first<{ id: number; email: string; name: string }>();

  if (!provider) {
    const result = await env.LEADS_DB.prepare(
      `INSERT INTO providers (email, name, created_at) VALUES (?, '', ?)`
    ).bind(link.email, now).run();
    provider = { id: result.meta.last_row_id as number, email: link.email, name: '' };
  }

  // Create session (30 days)
  const sessionToken = generateToken();
  const expiresAt = new Date(Date.now() + 30 * 24 * 3600 * 1000).toISOString();
  await env.LEADS_DB.prepare(
    `INSERT INTO sessions (provider_id, token, created_at, expires_at) VALUES (?, ?, ?, ?)`
  ).bind(provider.id, sessionToken, now, expiresAt).run();

  const cookie = sessionCookie(sessionToken);

  // No listing to claim — just go to dashboard
  if (!link.listing_slug) {
    return redirect('/provider/dashboard', cookie);
  }

  const slug = link.listing_slug;

  // Check if already claimed
  const existingClaim = await env.LEADS_DB.prepare(
    `SELECT id, provider_id, verification_status FROM claimed_listings WHERE listing_slug = ?`
  ).bind(slug).first<{ id: number; provider_id: number; verification_status: string }>();

  if (existingClaim) {
    if (existingClaim.provider_id === provider.id) {
      return redirect(`/provider/dashboard?listing=${slug}`, cookie);
    }
    if (existingClaim.verification_status === 'verified') {
      return redirectWithError('This listing has already been claimed by another provider.');
    }
  }

  // Fetch listing contact info for verification
  const contact = await getListingContact(slug, request.url);

  // PATH 1: Domain match → auto-approve
  if (contact && domainsMatch(provider.email, contact.website_domain)) {
    await claimListing(env, provider.id, slug, now, 'verified', 'domain_match');
    return redirect(`/provider/dashboard?listing=${slug}`, cookie);
  }

  // PATH 2: SMS verification
  const phone = contact?.phone ? normalizePhone(contact.phone) : null;
  if (phone) {
    const code = generateCode();
    const codeExpiry = new Date(Date.now() + 10 * 60 * 1000).toISOString();

    await env.LEADS_DB.prepare(
      `INSERT INTO verification_codes (provider_id, listing_slug, code, phone_sent_to, created_at, expires_at)
       VALUES (?, ?, ?, ?, ?, ?)`
    ).bind(provider.id, slug, code, phone, now, codeExpiry).run();

    const sent = await sendVerificationSMS(phone, code, env);
    if (sent) {
      const phoneLast2 = phone.slice(-2);
      return redirect(`/provider/verify-phone?listing=${slug}&phone=${phoneLast2}`, cookie);
    }
    console.error(`SMS send failed for ${slug}, falling through to manual review`);
  }

  // PATH 3: Manual review
  const reason = !contact
    ? 'Listing contact data not available'
    : !phone
      ? 'No phone number on listing'
      : 'SMS delivery failed';

  await claimListing(env, provider.id, slug, now, 'pending_review', 'pending');

  await env.LEADS_DB.prepare(
    `INSERT INTO pending_claims (provider_id, listing_slug, reason, created_at)
     VALUES (?, ?, ?, ?)`
  ).bind(provider.id, slug, reason, now).run();

  try {
    await notifyAdminPendingClaim(env, provider.email, slug, reason);
  } catch (err) {
    console.error('Admin notification failed:', err);
  }

  return redirect(`/provider/claim-pending?listing=${slug}`, cookie);
};

async function claimListing(
  env: Env,
  providerId: number,
  slug: string,
  now: string,
  status: string,
  method: string,
) {
  const existing = await env.LEADS_DB.prepare(
    `SELECT id, provider_id, verification_status FROM claimed_listings WHERE listing_slug = ?`
  ).bind(slug).first<{ id: number; provider_id: number; verification_status: string }>();

  if (existing && existing.provider_id === providerId) {
    await env.LEADS_DB.prepare(
      `UPDATE claimed_listings SET verification_status = ?, verification_method = ? WHERE id = ?`
    ).bind(status, method, existing.id).run();
  } else if (!existing || existing.verification_status !== 'verified') {
    if (existing) {
      await env.LEADS_DB.prepare(`DELETE FROM claimed_listings WHERE id = ?`).bind(existing.id).run();
    }
    await env.LEADS_DB.prepare(
      `INSERT INTO claimed_listings (provider_id, listing_slug, claimed_at, data_json, verification_status, verification_method)
       VALUES (?, ?, ?, '{}', ?, ?)`
    ).bind(providerId, slug, now, status, method).run();
  }
}

function redirect(location: string, cookie?: string) {
  const headers: Record<string, string> = { 'Location': location };
  if (cookie) headers['Set-Cookie'] = cookie;
  return new Response(null, { status: 302, headers });
}

function redirectWithError(message: string) {
  return new Response(null, {
    status: 302,
    headers: { 'Location': `/provider/login?error=${encodeURIComponent(message)}` },
  });
}
