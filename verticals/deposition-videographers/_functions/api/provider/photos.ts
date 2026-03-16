/**
 * POST /api/provider/photos — upload a photo for a claimed listing
 * DELETE /api/provider/photos — remove a photo
 *
 * Upload: multipart/form-data with fields: listing_slug, file
 * Delete: JSON body with: listing_slug, photo_id
 */
import type { Env } from '../../_types';
import { getProvider, jsonResponse, optionsResponse } from '../../_auth';

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_PHOTOS_PER_LISTING = 8;

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;
  const provider = await getProvider(env.LEADS_DB, request);
  if (!provider) return jsonResponse({ error: 'Unauthorized' }, 401, origin);

  if (!env.PHOTOS) {
    return jsonResponse({ error: 'Photo storage not configured' }, 500, origin);
  }

  let formData: FormData;
  try {
    formData = await request.formData();
  } catch {
    return jsonResponse({ error: 'Expected multipart form data' }, 400, origin);
  }

  const slug = formData.get('listing_slug') as string;
  const file = formData.get('file') as File | null;

  if (!slug || !file) {
    return jsonResponse({ error: 'listing_slug and file are required' }, 400, origin);
  }

  // Verify ownership
  const claim = await env.LEADS_DB.prepare(
    `SELECT id FROM claimed_listings WHERE provider_id = ? AND listing_slug = ?`
  ).bind(provider.id, slug).first();

  if (!claim) return jsonResponse({ error: 'Listing not claimed by you' }, 403, origin);

  // Validate file
  if (!ALLOWED_TYPES.includes(file.type)) {
    return jsonResponse({ error: 'Only JPEG, PNG, and WebP images are allowed' }, 400, origin);
  }

  if (file.size > MAX_FILE_SIZE) {
    return jsonResponse({ error: 'File must be under 5MB' }, 400, origin);
  }

  // Check photo count
  const countResult = await env.LEADS_DB.prepare(
    `SELECT COUNT(*) as cnt FROM provider_photos WHERE listing_slug = ?`
  ).bind(slug).first<{ cnt: number }>();

  if (countResult && countResult.cnt >= MAX_PHOTOS_PER_LISTING) {
    return jsonResponse({ error: `Maximum ${MAX_PHOTOS_PER_LISTING} photos per listing` }, 400, origin);
  }

  // Upload to R2
  const ext = file.type === 'image/png' ? 'png' : file.type === 'image/webp' ? 'webp' : 'jpg';
  const timestamp = Date.now();
  const r2Key = `listings/${slug}/${timestamp}.${ext}`;

  const arrayBuffer = await file.arrayBuffer();
  await env.PHOTOS.put(r2Key, arrayBuffer, {
    httpMetadata: { contentType: file.type },
  });

  // Save to DB
  const nextOrder = (countResult?.cnt || 0) + 1;
  const now = new Date().toISOString();

  await env.LEADS_DB.prepare(
    `INSERT INTO provider_photos (provider_id, listing_slug, r2_key, filename, uploaded_at, sort_order)
     VALUES (?, ?, ?, ?, ?, ?)`
  ).bind(provider.id, slug, r2Key, file.name, now, nextOrder).run();

  return jsonResponse({
    ok: true,
    photo: {
      r2_key: r2Key,
      url: `/api/photos/${r2Key}`,
      filename: file.name,
      uploaded_at: now,
    },
  }, 200, origin);
};

export const onRequestDelete: PagesFunction<Env> = async ({ request, env }) => {
  const origin = request.headers.get('Origin') || undefined;
  const provider = await getProvider(env.LEADS_DB, request);
  if (!provider) return jsonResponse({ error: 'Unauthorized' }, 401, origin);

  let payload: any;
  try { payload = await request.json(); } catch {
    return jsonResponse({ error: 'Invalid JSON' }, 400, origin);
  }

  const { photo_id } = payload;
  if (!photo_id) return jsonResponse({ error: 'photo_id is required' }, 400, origin);

  const photo = await env.LEADS_DB.prepare(
    `SELECT id, r2_key FROM provider_photos WHERE id = ? AND provider_id = ?`
  ).bind(photo_id, provider.id).first<{ id: number; r2_key: string }>();

  if (!photo) return jsonResponse({ error: 'Photo not found' }, 404, origin);

  // Delete from R2
  if (env.PHOTOS) {
    await env.PHOTOS.delete(photo.r2_key);
  }

  // Delete from DB
  await env.LEADS_DB.prepare(`DELETE FROM provider_photos WHERE id = ?`).bind(photo.id).run();

  return jsonResponse({ ok: true }, 200, origin);
};

export const onRequestOptions: PagesFunction = async ({ request }) => {
  return optionsResponse(request.headers.get('Origin') || undefined);
};
