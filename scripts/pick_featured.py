#!/usr/bin/env python3
import json, glob, os

listings = []
for f in sorted(glob.glob('/Users/nick/Desktop/depohire-src/src/data/listings/*.json')):
    city = os.path.basename(f).replace('.json','')
    for l in json.load(open(f)):
        l['__city_file'] = city
        l['__file'] = f
        listings.append(l)

CHAINS = ['veritext','planet depos','esquire','naegeli','pohlman','u.s. legal','magna',
          'huseby','lexitas','benchmark','steno','stenograph']

def score(l):
    s = 0
    if l.get('email'): s += 3
    if l.get('phone') and l['phone'] != 'Not provided': s += 1
    if l.get('website') and l['website'] != 'Not provided': s += 1
    desc = l.get('description') or ''
    if len(desc) > 80: s += 2
    rating = l.get('rating') or 0
    if rating >= 4.5: s += 3
    elif rating >= 4.0: s += 2
    rc = l.get('review_count') or 0
    if rc >= 10: s += 2
    elif rc >= 5: s += 1
    certs = l.get('certifications') or []
    if len(certs) > 0: s += 2
    if l.get('years_experience'): s += 1
    sent = l.get('sentiment') or {}
    if sent.get('label') == 'positive': s += 2
    highlights = sent.get('highlights') or []
    if len(highlights) >= 2: s += 1
    name = l.get('name','').lower()
    for chain in CHAINS:
        if chain in name:
            s -= 3
            break
    return s

ranked = sorted(listings, key=score, reverse=True)

print('Top 15 candidates:')
for l in ranked[:15]:
    sc = score(l)
    name = l['name'][:38]
    city = l['__city_file'][:18]
    has_email = 'Y' if l.get('email') else 'N'
    rating = l.get('rating') or 0
    certs = len(l.get('certifications') or [])
    yrs = l.get('years_experience') or ''
    email = l.get('email','')[:30]
    print(f"[{sc:2d}] {name:38} {city:18} email={has_email} r={rating} cert={certs} yrs={yrs}")
    if email:
        print(f"       -> {email}")
