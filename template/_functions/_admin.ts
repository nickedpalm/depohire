/**
 * Admin notification helpers for the claim verification system.
 *
 * Sends transactional email via Listmonk (same pattern as api/leads.ts).
 */

import type { Env } from './_types';
import { getSiteConfig } from './_auth';

function esc(str: string): string {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/**
 * Notify the admin that a claim requires manual review.
 */
export async function notifyAdminPendingClaim(
  env: Env,
  providerEmail: string,
  listingSlug: string,
  reason: string,
): Promise<void> {
  const adminEmail = env.ADMIN_EMAIL;
  if (!adminEmail) {
    console.error('ADMIN_EMAIL not configured — skipping claim notification');
    return;
  }

  const site = getSiteConfig(env);
  const auth = 'Basic ' + btoa(`${site.listmonkUser}:${site.listmonkPass}`);
  const siteName = site.name;
  const siteDomain = site.domain;
  const fromEmail = site.fromEmail;
  const timestamp = new Date().toISOString();

  const htmlBody = `<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f9fafb;font-family:system-ui,-apple-system,sans-serif">
<div style="max-width:560px;margin:40px auto;background:#fff;border-radius:12px;border:1px solid #e5e7eb;overflow:hidden">
  <div style="background:#92400e;padding:24px 32px">
    <h1 style="color:#fff;font-size:20px;margin:0;font-weight:700">${siteName} — Claim Review Needed</h1>
  </div>
  <div style="padding:32px">
    <div style="background:#fef3c7;border:1px solid #fbbf24;border-radius:8px;padding:16px 20px;margin-bottom:24px">
      <p style="color:#92400e;font-size:14px;font-weight:600;margin:0 0 4px">Manual Review Required</p>
      <p style="color:#b45309;font-size:13px;margin:0">A listing claim could not be auto-verified.</p>
    </div>

    <table style="width:100%;border-collapse:collapse">
      <tr>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#6b7280;font-size:14px;width:130px;vertical-align:top">Provider Email</td>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#1a1a1a;font-size:14px;font-weight:500">${esc(providerEmail)}</td>
      </tr>
      <tr>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#6b7280;font-size:14px;vertical-align:top">Listing Slug</td>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#1a1a1a;font-size:14px">
          <a href="https://${siteDomain}/listing/${encodeURIComponent(listingSlug)}/" style="color:#2563eb;text-decoration:none">${esc(listingSlug)}</a>
        </td>
      </tr>
      <tr>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#6b7280;font-size:14px;vertical-align:top">Reason</td>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#1a1a1a;font-size:14px">${esc(reason)}</td>
      </tr>
      <tr>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#6b7280;font-size:14px;vertical-align:top">Timestamp</td>
        <td style="padding:10px 0;border-bottom:1px solid #f3f4f6;color:#9ca3af;font-size:13px">${timestamp}</td>
      </tr>
    </table>
  </div>
  <div style="border-top:1px solid #f3f4f6;padding:20px 32px;background:#fafafa">
    <p style="color:#d1d5db;font-size:11px;margin:0;line-height:1.5">
      ${siteName} Admin Notification &middot; ${siteDomain}
    </p>
  </div>
</div>
</body>
</html>`;

  try {
    // Ensure admin subscriber exists
    await fetch(`${site.listmonkUrl}/api/subscribers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': auth },
      body: JSON.stringify({ email: adminEmail, name: 'Admin', status: 'enabled' }),
    }); // 409 if already exists — fine

    const resp = await fetch(`${site.listmonkUrl}/api/tx`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': auth },
      body: JSON.stringify({
        subscriber_email: adminEmail,
        template_id: site.passthroughTemplateId,
        subject: `[${siteName}] Claim review: ${listingSlug}`,
        data: { body: htmlBody },
        content_type: 'html',
        messenger: 'email',
        from_email: fromEmail,
      }),
    });

    if (!resp.ok) {
      const text = await resp.text();
      console.error(`Admin notification email failed: ${resp.status} ${text}`);
    }
  } catch (err) {
    console.error('Admin notification error:', err);
  }
}
