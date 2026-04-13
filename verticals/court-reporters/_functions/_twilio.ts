/**
 * Twilio SMS helpers for claim verification.
 *
 * - normalizePhone: coerce US numbers to E.164 (+1XXXXXXXXXX)
 * - maskPhone: redact all but last 2 digits for UI display
 * - generateCode: 6-digit random numeric code
 * - sendVerificationSMS: deliver code via Twilio REST API
 */

import type { Env } from './_types';

/**
 * Strip non-digits and normalise to E.164 US format (+1XXXXXXXXXX).
 * Returns null if the input cannot be normalised.
 */
export function normalizePhone(phone: string): string | null {
  const digits = phone.replace(/\D/g, '');
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length === 11 && digits.startsWith('1')) return `+${digits}`;
  return null;
}

/**
 * Mask a phone number for display, showing only the last 2 digits.
 * Input should be normalised E.164 (+1XXXXXXXXXX) but handles raw digits too.
 */
export function maskPhone(phone: string): string {
  const digits = phone.replace(/\D/g, '');
  // Take the 10-digit national number (strip leading country code)
  const national = digits.length === 11 && digits.startsWith('1')
    ? digits.slice(1)
    : digits.slice(-10);

  if (national.length < 10) return '(***) ***-**' + national.slice(-2);

  const last2 = national.slice(-2);
  return `(${national.slice(0, 3)}) ${national.slice(3, 6)}-**${last2}`;
}

/**
 * Generate a 6-digit random numeric verification code.
 */
export function generateCode(): string {
  const array = new Uint32Array(1);
  crypto.getRandomValues(array);
  // Mod 1_000_000 gives 0–999999; pad to 6 digits
  return String(array[0] % 1_000_000).padStart(6, '0');
}

/**
 * Send a verification SMS via Twilio REST API.
 * Returns true on success (HTTP 2xx), false otherwise.
 */
export async function sendVerificationSMS(
  phone: string,
  code: string,
  env: Env,
): Promise<boolean> {
  const sid = env.TWILIO_ACCOUNT_SID;
  const token = env.TWILIO_AUTH_TOKEN;
  const from = env.TWILIO_PHONE_NUMBER;

  if (!sid || !token || !from) {
    console.error('Twilio credentials not configured');
    return false;
  }

  const url = `https://api.twilio.com/2010-04-01/Accounts/${sid}/Messages.json`;

  const body = new URLSearchParams({
    To: phone,
    From: from,
    Body: `Your ${env.SITE_NAME || 'Directory'} verification code is: ${code}. It expires in 10 minutes.`,
  });

  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': 'Basic ' + btoa(`${sid}:${token}`),
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
    });

    if (!resp.ok) {
      const text = await resp.text();
      console.error(`Twilio SMS failed: ${resp.status} ${text}`);
      return false;
    }

    return true;
  } catch (err) {
    console.error('Twilio SMS error:', err);
    return false;
  }
}
