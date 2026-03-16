#!/usr/bin/env python3
"""
Generate candidate emails from listing website domains and verify via SMTP.
Checks if mailbox exists without sending anything.

Usage:
    python3 scripts/enrich_emails_smtp.py --vertical deposition-videographers [--dry-run] [--limit N]
"""

import argparse
import asyncio
import re
import smtplib
import socket
import sqlite3
import dns.resolver
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).parent.parent

CANDIDATE_PREFIXES = ["info", "contact", "office", "hello", "inquiries", "admin"]

# Domains that use catch-all (accept everything) — skip verification
CATCH_ALL_CACHE = {}


def extract_domain(website: str) -> str | None:
    """Extract clean domain from a website URL."""
    if not website:
        return None
    if not website.startswith(("http://", "https://")):
        website = "http://" + website
    try:
        parsed = urlparse(website)
        domain = parsed.netloc.lower()
        # Strip www.
        if domain.startswith("www."):
            domain = domain[4:]
        # Skip IP addresses, localhost, etc.
        if not domain or "." not in domain:
            return None
        # Skip common platforms (no business email there)
        skip = {
            "facebook.com", "instagram.com", "linkedin.com", "twitter.com",
            "youtube.com", "yelp.com", "google.com", "wix.com",
            "squarespace.com", "wordpress.com", "weebly.com",
            "godaddy.com", "sites.google.com",
        }
        if domain in skip or any(domain.endswith("." + s) for s in skip):
            return None
        return domain
    except Exception:
        return None


def get_mx_host(domain: str) -> str | None:
    """Get the primary MX record for a domain."""
    try:
        answers = dns.resolver.resolve(domain, "MX")
        # Sort by preference (lowest = highest priority)
        records = sorted(answers, key=lambda r: r.preference)
        if records:
            return str(records[0].exchange).rstrip(".")
        return None
    except Exception:
        return None


def verify_email_smtp(email: str, mx_host: str, timeout: int = 10) -> str:
    """
    Verify email via SMTP RCPT TO.
    Returns: 'valid', 'invalid', 'catch_all', 'error'
    """
    domain = email.split("@")[1]

    # Check catch-all cache
    if domain in CATCH_ALL_CACHE:
        return "catch_all" if CATCH_ALL_CACHE[domain] else "unknown"

    try:
        smtp = smtplib.SMTP(timeout=timeout)
        smtp.connect(mx_host, 25)
        smtp.helo("depohire.com")
        smtp.mail("verify@depohire.com")
        code, msg = smtp.rcpt(email)
        smtp.quit()

        if code == 250:
            return "valid"
        elif code == 550 or code == 551 or code == 553:
            return "invalid"
        else:
            return "unknown"
    except smtplib.SMTPServerDisconnected:
        return "error"
    except smtplib.SMTPConnectError:
        return "error"
    except socket.timeout:
        return "error"
    except Exception:
        return "error"


def check_catch_all(domain: str, mx_host: str) -> bool:
    """Check if domain has catch-all by testing a random address."""
    if domain in CATCH_ALL_CACHE:
        return CATCH_ALL_CACHE[domain]

    fake = f"xyznonexistent8742@{domain}"
    result = verify_email_smtp(fake, mx_host, timeout=8)
    is_catch_all = result == "valid"
    CATCH_ALL_CACHE[domain] = is_catch_all
    return is_catch_all


def main():
    parser = argparse.ArgumentParser(description="Find emails via SMTP verification")
    parser.add_argument("--vertical", required=True, help="Vertical slug")
    parser.add_argument("--dry-run", action="store_true", help="Show candidates without verifying")
    parser.add_argument("--limit", type=int, default=0, help="Limit listings to check")
    args = parser.parse_args()

    db_path = PROJECT_ROOT / "verticals" / args.vertical / "pipeline.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    rows = conn.execute("""
        SELECT id, name, city, state, website, email
        FROM raw_listings
        WHERE (email IS NULL OR email = '')
        AND website IS NOT NULL AND website != ''
        ORDER BY city, name
    """).fetchall()

    print(f"Listings missing email with website: {len(rows)}")

    # Extract domains and build candidates
    candidates = []
    for row in rows:
        domain = extract_domain(row["website"])
        if not domain:
            continue
        emails = [f"{prefix}@{domain}" for prefix in CANDIDATE_PREFIXES]
        candidates.append({
            "id": row["id"],
            "name": row["name"],
            "city": row["city"],
            "domain": domain,
            "emails": emails,
        })

    print(f"Candidates with valid domains: {len(candidates)}")

    if args.limit:
        candidates = candidates[:args.limit]
        print(f"Limited to {args.limit}")

    if args.dry_run:
        for c in candidates[:20]:
            print(f"  {c['name']}: {', '.join(c['emails'][:3])}")
        print(f"\n  ... and {len(candidates) - 20} more")
        print("\nDry run — no SMTP checks.")
        conn.close()
        return

    stats = {
        "verified": 0, "catch_all": 0, "no_mx": 0,
        "invalid": 0, "errors": 0, "checked": 0,
    }
    mx_cache = {}

    print(f"\nVerifying emails for {len(candidates)} listings...")
    for i, c in enumerate(candidates):
        if (i + 1) % 25 == 0 or (i + 1) == len(candidates):
            print(f"  Progress: {i + 1}/{len(candidates)} (verified: {stats['verified']}, catch-all: {stats['catch_all']}, no-mx: {stats['no_mx']})")

        domain = c["domain"]
        stats["checked"] += 1

        # Get MX record (cached)
        if domain not in mx_cache:
            mx_cache[domain] = get_mx_host(domain)
        mx_host = mx_cache[domain]

        if not mx_host:
            stats["no_mx"] += 1
            continue

        # Check catch-all first
        if domain not in CATCH_ALL_CACHE:
            is_catch_all = check_catch_all(domain, mx_host)
        else:
            is_catch_all = CATCH_ALL_CACHE[domain]

        if is_catch_all:
            # Catch-all accepts everything — use info@ as best guess
            best = f"info@{domain}"
            conn.execute(
                "UPDATE raw_listings SET email = ?, contact_method = 'email' WHERE id = ?",
                (best, c["id"]),
            )
            stats["catch_all"] += 1
            continue

        # Try each candidate
        found = False
        for email in c["emails"]:
            result = verify_email_smtp(email, mx_host)
            if result == "valid":
                conn.execute(
                    "UPDATE raw_listings SET email = ?, contact_method = 'email' WHERE id = ?",
                    (email, c["id"]),
                )
                stats["verified"] += 1
                found = True
                break
            elif result == "invalid":
                stats["invalid"] += 1
            else:
                stats["errors"] += 1
                break  # Server issue, skip remaining candidates

        # Commit every 50
        if (i + 1) % 50 == 0:
            conn.commit()

    conn.commit()
    conn.close()

    print(f"\nDone!")
    print(f"  Checked: {stats['checked']} domains")
    print(f"  SMTP verified: {stats['verified']}")
    print(f"  Catch-all (used info@): {stats['catch_all']}")
    print(f"  No MX record: {stats['no_mx']}")
    print(f"  Invalid addresses: {stats['invalid']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Total emails added: {stats['verified'] + stats['catch_all']}")
    print(f"\nRun: python3 scripts/export.py --vertical {args.vertical}")


if __name__ == "__main__":
    main()
