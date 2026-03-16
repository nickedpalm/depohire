import type { Env } from './_types';

export function generateToken(): string {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
}

export function corsHeaders(origin?: string) {
  return {
    'Access-Control-Allow-Origin': origin || 'https://depohire.com',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Credentials': 'true',
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
