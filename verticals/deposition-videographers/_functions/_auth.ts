import type { Env } from './_types';

export const SLUG_RE = /^[a-z0-9][a-z0-9-]*$/;

export function generateToken(): string {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
}

const ALLOWED_ORIGINS = [
  'https://depohire.com',
  'https://www.depohire.com',
  'http://localhost:4321',
  'http://localhost:3000',
];

export function isAllowedOrigin(origin: string | null | undefined): string | null {
  if (!origin) return null;
  if (ALLOWED_ORIGINS.includes(origin)) return origin;
  // Allow *.depohire.com subdomains (e.g. staging, preview deploys)
  if (/^https:\/\/[a-z0-9-]+\.depohire\.com$/.test(origin)) return origin;
  return null;
}

export function corsHeaders(origin?: string, env?: { SITE_DOMAIN?: string }) {
  const defaultOrigin = env?.SITE_DOMAIN ? `https://${env.SITE_DOMAIN}` : 'https://depohire.com';
  const allowedOrigin = isAllowedOrigin(origin) || defaultOrigin;
  return {
    'Access-Control-Allow-Origin': allowedOrigin,
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Credentials': 'true',
    'Vary': 'Origin',
  };
}

export function optionsResponse(origin?: string) {
  return new Response(null, {
    status: 204,
    headers: { ...corsHeaders(origin), 'Access-Control-Max-Age': '86400' },
  });
}

export function jsonResponse(data: any, status = 200, origin?: string) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
  });
}

export function sessionCookie(token: string, maxAge = 30 * 24 * 3600) {
  return `depohire_session=${token}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${maxAge}`;
}

export function getSessionToken(request: Request): string | null {
  const cookie = request.headers.get('Cookie') || '';
  const match = cookie.match(/depohire_session=([a-f0-9]{64})/);
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
