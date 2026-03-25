/**
 * GET /api/photos/listings/slug/timestamp.jpg
 * Serve photos from R2 bucket. Public, no auth required.
 * Cached for 1 year (immutable filenames with timestamps).
 */
import type { Env } from '../../_types';

export const onRequestGet: PagesFunction<Env> = async ({ params, env }) => {
  if (!env.PHOTOS) {
    return new Response('Photo storage not configured', { status: 500 });
  }

  const path = Array.isArray(params.path) ? params.path.join('/') : params.path;
  if (!path) {
    return new Response('Not found', { status: 404 });
  }

  const object = await env.PHOTOS.get(path);
  if (!object) {
    return new Response('Not found', { status: 404 });
  }

  const headers = new Headers();
  headers.set('Content-Type', object.httpMetadata?.contentType || 'image/jpeg');
  headers.set('Cache-Control', 'public, max-age=31536000, immutable');
  headers.set('Access-Control-Allow-Origin', '*');

  return new Response(object.body, { headers });
};
