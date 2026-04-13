import type { Env } from './_types';

export const SLUG_RE = /^[a-z0-9][a-z0-9-]*$/;

const COOKIE_NAME = 'df_session'; // generic cookie name for all verticals

export function generateToken(): string {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
}

/** Short alphanumeric code for user-facing URLs (less suspicious to Chrome Safe Browsing) */
export function generateShortCode(length = 8): string {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789';
  const bytes = new Uint8Array(length);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, b => chars[b % chars.length]).join('');
}

/**
 * Build allowed origins list from SITE_DOMAIN env var.
 * Always allows localhost for development.
 */
function getAllowedOrigins(domain?: string): string[] {
  const origins = [
    'http://localhost:4321',
    'http://localhost:3000',
  ];
  if (domain) {
    origins.push(`https://${domain}`);
    origins.push(`https://www.${domain}`);
  }
  return origins;
}

export function isAllowedOrigin(origin: string | null | undefined, domain?: string): string | null {
  if (!origin) return null;
  const allowed = getAllowedOrigins(domain);
  if (allowed.includes(origin)) return origin;
  // Allow *.domain subdomains (e.g. staging, preview deploys)
  if (domain && new RegExp(`^https://[a-z0-9-]+\\.${domain.replace('.', '\\.')}$`).test(origin)) return origin;
  // Allow Cloudflare Pages preview deploys
  if (/^https:\/\/[a-z0-9-]+\.pages\.dev$/.test(origin)) return origin;
  return null;
}

export function corsHeaders(origin?: string, env?: Env) {
  const domain = env?.SITE_DOMAIN;
  const defaultOrigin = domain ? `https://${domain}` : 'https://localhost:4321';
  const allowedOrigin = isAllowedOrigin(origin, domain) || defaultOrigin;
  return {
    'Access-Control-Allow-Origin': allowedOrigin,
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Credentials': 'true',
    'Vary': 'Origin',
  };
}

export function optionsResponse(origin?: string, env?: Env) {
  return new Response(null, {
    status: 204,
    headers: { ...corsHeaders(origin, env), 'Access-Control-Max-Age': '86400' },
  });
}

export function jsonResponse(data: any, status = 200, origin?: string, env?: Env) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders(origin, env) },
  });
}

export function sessionCookie(token: string, maxAge = 30 * 24 * 3600) {
  return `${COOKIE_NAME}=${token}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${maxAge}`;
}

export function getSessionToken(request: Request): string | null {
  const cookie = request.headers.get('Cookie') || '';
  const re = new RegExp(`${COOKIE_NAME}=([a-f0-9]{64})`);
  const match = cookie.match(re);
  return match ? match[1] : null;
}

export async function verifyTurnstile(token: string, secret: string, ip?: string): Promise<boolean> {
  if (!secret) return true; // Skip if no secret configured (dev mode)
  if (!token) return false;
  const body: Record<string, string> = { secret, response: token };
  if (ip) body.remoteip = ip;
  try {
    const resp = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const result = await resp.json<{ success: boolean }>();
    return result.success === true;
  } catch {
    console.error('Turnstile verification failed');
    return false;
  }
}

export async function getProvider(db: D1Database, request: Request) {
  const token = getSessionToken(request);
  if (!token) return null;

  const row = await db.prepare(
    `SELECT p.id, p.email, p.name FROM sessions s
     JOIN providers p ON p.id = s.provider_id
     WHERE s.token = ? AND s.expires_at > ?`
  ).bind(token, new Date().toISOString()).first<{ id: number; email: string; name: string }>();

  return row || null;
}

/**
 * Helper to get site config from env with sensible defaults.
 */
export function getSiteConfig(env: Env) {
  const name = env.SITE_NAME || 'Directory';
  const domain = env.SITE_DOMAIN || 'localhost';
  return {
    name,
    domain,
    tagline: env.SITE_TAGLINE || '',
    fromEmail: env.SITE_FROM_EMAIL || `${name} <noreply@${domain}>`,
    address: env.COMPANY_ADDRESS || '',
    listmonkUrl: env.LISTMONK_URL || 'https://mail.firestick.io',
    listmonkUser: env.LISTMONK_USER || 'admin',
    listmonkPass: env.LISTMONK_PASS || '',
    listId: parseInt(env.LISTMONK_LIST_ID || '0') || 0,
    magicLinkTemplateId: parseInt(env.LISTMONK_MAGICLINK_TEMPLATE_ID || '0') || 0,
    guideTemplateId: parseInt(env.LISTMONK_GUIDE_TEMPLATE_ID || '0') || 0,
    passthroughTemplateId: parseInt(env.LISTMONK_PASSTHROUGH_TEMPLATE_ID || '0') || 0,
    hashSalt: env.HASH_SALT || `${domain}-salt-${new Date().getFullYear()}`,
  };
}
