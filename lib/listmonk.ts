/**
 * Listmonk API utility for DepoHire
 * Handles email subscriber creation and tagging
 *
 * Set LISTMONK_URL and LISTMONK_API_KEY in your environment / Cloudflare Pages secrets.
 * For static Astro, form submissions hit a Cloudflare Worker (see /functions/subscribe.ts)
 */

export interface SubscribeOptions {
  email: string;
  name?: string;
  listIds: number[];        // Listmonk list IDs
  tags?: string[];
  attribs?: Record<string, string | number | boolean>;
}

export interface SubscribeResult {
  ok: boolean;
  error?: string;
}

/**
 * Subscribe a user to Listmonk.
 * Called server-side only (Cloudflare Worker / Astro SSR endpoint).
 */
export async function subscribeToListmonk(
  opts: SubscribeOptions,
  listmonkUrl: string,
  apiKey: string,          // base64("user:password") or token
): Promise<SubscribeResult> {
  const url = `${listmonkUrl.replace(/\/$/, '')}/api/subscribers`;

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Basic ${apiKey}`,
      },
      body: JSON.stringify({
        email: opts.email,
        name: opts.name || opts.email.split('@')[0],
        status: 'enabled',
        lists: opts.listIds,
        attribs: opts.attribs || {},
        preconfirm_subscriptions: true,
      }),
    });

    // 409 = already subscribed — treat as success
    if (res.status === 409) return { ok: true };
    if (!res.ok) {
      const body = await res.text();
      return { ok: false, error: body };
    }
    return { ok: true };
  } catch (err: unknown) {
    return { ok: false, error: String(err) };
  }
}
