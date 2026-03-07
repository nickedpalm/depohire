#!/usr/bin/env python3
import csv, re

rows = list(csv.DictReader(open('/Users/nick/Desktop/depohire-src/scripts/enriched_emails.csv')))
total = len(rows)
with_email = [r for r in rows if r['email'].strip()]
without = [r for r in rows if not r['email'].strip()]
high = [r for r in with_email if r['confidence'] == 'high']
medium = [r for r in with_email if r['confidence'] == 'medium']
low_conf = [r for r in with_email if r['confidence'] == 'low']

email_re = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
junk = [r for r in with_email if not email_re.match(r['email'].strip())]

print(f"Total rows: {total}")
print(f"With email: {len(with_email)} ({len(with_email)/total*100:.0f}%)")
print(f"  High confidence: {len(high)}")
print(f"  Medium confidence: {len(medium)}")
print(f"  Low confidence: {len(low_conf)}")
print(f"Without email: {len(without)}")
print(f"Malformed/junk: {len(junk)}")

if junk:
    print("\nJunk emails to review:")
    for r in junk:
        print(f"  {r['name'][:35]:35} -> {r['email']}")

print("\nSample found (first 12):")
for r in with_email[:12]:
    print(f"  {r['name'][:35]:35} {r['email']}")

print("\nSample not found (first 5):")
for r in without[:5]:
    print(f"  {r['name'][:35]:35} {r['notes'][:70]}")
