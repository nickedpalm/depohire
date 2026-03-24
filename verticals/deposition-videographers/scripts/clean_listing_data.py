#!/usr/bin/env python3
"""Clean listing data quality issues across all city listing files.

Reads per-city JSON files from src/data/listings/, applies fixes, writes back.
Idempotent — safe to run multiple times.
"""

import json
import os
import re
from pathlib import Path
from urllib.parse import unquote

LISTINGS_DIR = Path(__file__).resolve().parent.parent / "src" / "data" / "listings"

# Keywords in listing name that suggest non-legal videography services
FLAG_KEYWORDS = [
    "wedding",
    "photography",
    "marketing",
    "digital marketing",
    "cinematic wedding",
    "youtube",
]

# Compile a single regex for flagging (case-insensitive)
FLAG_PATTERN = re.compile(
    "|".join(re.escape(kw) for kw in FLAG_KEYWORDS), re.IGNORECASE
)


def is_bad_email(email: str) -> bool:
    """Check if an email is a known bad pattern."""
    if not email:
        return False
    if email == "user@domain.com":
        return True
    if email.endswith("@sentry.wixpress.com") or email.endswith("@sentry-next.wixpress.com"):
        return True
    return False


def fix_email(email: str) -> tuple[str, str | None]:
    """Fix or clear a bad email. Returns (fixed_email, reason_or_None)."""
    if not email:
        return email, None
    if is_bad_email(email):
        return "", f"removed bad email: {email}"
    if email.startswith("%20"):
        fixed = email.lstrip("%20")
        # Be careful: lstrip removes chars, not substring. Use removeprefix-style.
        fixed = email
        while fixed.startswith("%20"):
            fixed = fixed[3:]
        return fixed, f"stripped %20 prefix: {email} -> {fixed}"
    return email, None


def normalize_phone(phone: str) -> str:
    """Normalize a 10-digit US phone to (XXX) XXX-XXXX format."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone  # Can't normalize, return as-is


def fix_phone(phone: str) -> tuple[str, str | None]:
    """Fix or clear a bad phone. Returns (fixed_phone, reason_or_None)."""
    if not phone:
        return phone, None

    original = phone
    reason = None

    # URL-decode %20
    if "%20" in phone:
        phone = unquote(phone)
        reason = f"url-decoded phone: {original} -> {phone}"

    # Strip leading //
    if phone.startswith("//"):
        phone = phone[2:].strip()
        reason = f"stripped // prefix: {original} -> {phone}"

    # Check if too short (just area code)
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 7:
        return "", f"removed short phone ({len(digits)} digits): {original}"

    # Normalize to (XXX) XXX-XXXX
    normalized = normalize_phone(phone)
    if normalized != phone:
        if reason:
            reason += f", then normalized to {normalized}"
        else:
            reason = f"normalized phone: {phone} -> {normalized}"
        phone = normalized

    if reason is None and phone != original:
        reason = f"fixed phone: {original} -> {phone}"

    return phone, reason


def should_flag(name: str) -> bool:
    """Check if a listing name suggests non-legal videography services."""
    return bool(FLAG_PATTERN.search(name))


def has_no_contact(listing: dict) -> bool:
    """Check if a listing has no contact method at all."""
    phone = (listing.get("phone") or "").strip()
    email = (listing.get("email") or "").strip()
    website = (listing.get("website") or "").strip()
    return not phone and not email and not website


def process_file(filepath: Path) -> dict:
    """Process a single city listing file. Returns stats dict."""
    with open(filepath, "r") as f:
        listings = json.load(f)

    stats = {
        "emails_fixed": [],
        "phones_fixed": [],
        "flagged": [],
        "zero_coords": [],
        "empty_descriptions": [],
        "empty_certifications": [],
        "removed_no_contact": [],
    }

    modified = False
    kept_listings = []

    for listing in listings:
        name = listing.get("name", "")
        city_file = filepath.stem

        # Fix emails
        email = listing.get("email", "") or ""
        fixed_email, email_reason = fix_email(email)
        if email_reason:
            listing["email"] = fixed_email
            stats["emails_fixed"].append(f"  [{city_file}] {name}: {email_reason}")
            modified = True

        # Fix phones
        phone = listing.get("phone", "") or ""
        fixed_phone, phone_reason = fix_phone(phone)
        if phone_reason:
            listing["phone"] = fixed_phone
            stats["phones_fixed"].append(f"  [{city_file}] {name}: {phone_reason}")
            modified = True

        # Flag non-legal videographers
        if should_flag(name):
            if not listing.get("flagged"):
                listing["flagged"] = True
                stats["flagged"].append(f"  [{city_file}] {name}")
                modified = True
        else:
            # Ensure flagged is False if not matching (idempotent)
            if listing.get("flagged"):
                listing["flagged"] = False
                modified = True

        # Report zero coordinates
        if listing.get("lat") == 0 and listing.get("lng") == 0:
            stats["zero_coords"].append(f"  [{city_file}] {name}")

        # Report empty descriptions
        if not (listing.get("description") or "").strip():
            stats["empty_descriptions"].append(f"  [{city_file}] {name}")

        # Report empty certifications
        certs = listing.get("certifications", [])
        if not certs:
            stats["empty_certifications"].append(f"  [{city_file}] {name}")

        # Check for no contact method (after fixes applied)
        if has_no_contact(listing):
            stats["removed_no_contact"].append(f"  [{city_file}] {name}")
            modified = True
            continue  # Don't add to kept_listings

        kept_listings.append(listing)

    if modified:
        with open(filepath, "w") as f:
            json.dump(kept_listings, f, indent=2, ensure_ascii=False)
            f.write("\n")

    return stats


def main():
    if not LISTINGS_DIR.is_dir():
        print(f"ERROR: Listings directory not found: {LISTINGS_DIR}")
        return

    json_files = sorted(LISTINGS_DIR.glob("*.json"))
    print(f"Processing {len(json_files)} city listing files in {LISTINGS_DIR}\n")

    totals = {
        "emails_fixed": [],
        "phones_fixed": [],
        "flagged": [],
        "zero_coords": [],
        "empty_descriptions": [],
        "empty_certifications": [],
        "removed_no_contact": [],
    }

    for filepath in json_files:
        stats = process_file(filepath)
        for key in totals:
            totals[key].extend(stats[key])

    # Print summary
    print("=" * 60)
    print("CLEANING SUMMARY")
    print("=" * 60)

    print(f"\n--- Emails fixed/removed: {len(totals['emails_fixed'])} ---")
    for line in totals["emails_fixed"]:
        print(line)

    print(f"\n--- Phones fixed/removed: {len(totals['phones_fixed'])} ---")
    for line in totals["phones_fixed"]:
        print(line)

    print(f"\n--- Flagged as non-legal videographer: {len(totals['flagged'])} ---")
    for line in totals["flagged"]:
        print(line)

    print(f"\n--- Removed (no contact method): {len(totals['removed_no_contact'])} ---")
    for line in totals["removed_no_contact"]:
        print(line)

    print(f"\n--- Zero coordinates (needs geocoding): {len(totals['zero_coords'])} ---")
    for line in totals["zero_coords"]:
        print(line)

    print(f"\n--- Empty descriptions: {len(totals['empty_descriptions'])} ---")
    for line in totals["empty_descriptions"][:10]:
        print(line)
    if len(totals["empty_descriptions"]) > 10:
        print(f"  ... and {len(totals['empty_descriptions']) - 10} more")

    print(f"\n--- Empty certifications: {len(totals['empty_certifications'])} ---")
    if totals["empty_certifications"]:
        print(f"  ({len(totals['empty_certifications'])} listings — not shown individually)")

    print(f"\n{'=' * 60}")
    print("TOTALS:")
    print(f"  Emails fixed/removed:    {len(totals['emails_fixed'])}")
    print(f"  Phones fixed/removed:    {len(totals['phones_fixed'])}")
    print(f"  Flagged (non-legal):     {len(totals['flagged'])}")
    print(f"  Removed (no contact):    {len(totals['removed_no_contact'])}")
    print(f"  Zero coordinates:        {len(totals['zero_coords'])}")
    print(f"  Empty descriptions:      {len(totals['empty_descriptions'])}")
    print(f"  Empty certifications:    {len(totals['empty_certifications'])}")
    print("=" * 60)


if __name__ == "__main__":
    main()
